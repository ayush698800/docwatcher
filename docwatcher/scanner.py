"""
scanner.py
==========
DocDrift Enterprise Scanner — CLI entry point.

Usage:
  python scanner.py                          # Mass scan top 100 Python repos
  python scanner.py --url https://github.com/org/repo    # Sniper: single remote repo
  python scanner.py --local /path/to/repo   # Local mode: scan a repo on disk
  python scanner.py --local .               # Local mode: current directory

The script is designed to run from any directory thanks to explicit sys.path
management. All heavy lifting is delegated to the modular sub-packages.
"""

# ==========================================
# PATH SETUP — must be first
# Allows `python scanner.py` from any directory by ensuring the parent
# of docwatcher/ is always on sys.path.
# ==========================================
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
import logging
import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests as req

# Rich terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich import box

# Local modules
from docwatcher.git_manager import GitOps
from docwatcher.analyzer import get_changed_symbols
from docwatcher.embeddings import build_index, search_docs, needs_reindex
from docwatcher.auditor import (
    check_consistency,
    RateLimitExceeded,
    save_progress,
    load_progress,
    PROGRESS_FILE
)

# ==========================================
# GLOBAL CONFIG
# ==========================================
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
MAX_WORKERS   = 4
TARGET_REPOS  = 100
MIN_STARS     = 10_000
FINAL_REPORT  = "docdrift_final_report.json"
BACKUP_FILE   = "audit_state_backup.json"

console = Console()

logging.basicConfig(
    filename='docdrift_audit.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s'
)
logger = logging.getLogger(__name__)


# ==========================================
# GITHUB API MANAGER
# ==========================================
class GitHubAPI:
    """Thin wrapper around the GitHub REST Search API."""

    def __init__(self, token: str = ""):
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"
        self.session = req.Session()
        self.session.headers.update(headers)

    def get_top_repos(self, count: int = TARGET_REPOS) -> list:
        """
        Fetch the top `count` Python repos by star count.
        Filters out curated list repos ("awesome", "list").
        Paginates with a polite 2-second delay between pages.
        """
        repos = []
        page = 1
        with console.status("[bold cyan]Querying GitHub for top Python repos...", spinner="dots"):
            while len(repos) < count:
                try:
                    res = self.session.get(
                        "https://api.github.com/search/repositories",
                        params={
                            "q": f"language:python stars:>{MIN_STARS} NOT awesome NOT list",
                            "sort": "stars",
                            "order": "desc",
                            "per_page": 30,
                            "page": page
                        },
                        timeout=15
                    )
                    res.raise_for_status()
                    items = res.json().get("items", [])
                    if not items:
                        break
                    for item in items:
                        repos.append({
                            "full_name": item["full_name"],
                            "stars": item["stargazers_count"],
                            "url": item["html_url"]
                        })
                    page += 1
                    time.sleep(2)
                except req.HTTPError as e:
                    console.print(f"[red]GitHub API error: {e}[/red]")
                    break
                except Exception as e:
                    console.print(f"[red]Unexpected error: {e}[/red]")
                    break
        return repos[:count]


# ==========================================
# CORE AUDIT ENGINE
# ==========================================
def audit_repo(repo: dict, is_sniper: bool = False, repo_path: str = None) -> dict:
    """
    Audit a single repository for documentation drift.

    Parameters
    ----------
    repo       : dict with keys: full_name, url, stars
    is_sniper  : True → scan up to 10 files and expand lookback automatically
    repo_path  : If provided, skip cloning and use this local directory directly

    Returns a stats dict with findings ready for JSON serialisation.

    Raises RateLimitExceeded when the LLM quota is exhausted so the caller
    can save state before exiting.
    """
    repo_name = repo.get("full_name", repo_path or "local-repo")
    stats = {
        "repo":            repo_name,
        "stars":           repo.get("stars", "N/A"),
        "url":             repo.get("url", "local"),
        "critical_errors": 0,
        "warnings":        0,
        "undocumented":    0,
        "findings":        [],
        "status":          "success"
    }

    # If no local path provided, clone into a temp dir
    tmp_dir = None
    if repo_path is None:
        tmp_dir = tempfile.mkdtemp()
        work_dir = tmp_dir
        if not GitOps.clone_repo(repo["url"], work_dir):
            stats["status"] = "clone_failed"
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return stats
    else:
        work_dir = repo_path

    try:
        # --- 1. Discover recently changed files ---
        changed_files, days_used = GitOps.get_changed_files_with_fallback(
            work_dir, is_verbose=is_sniper
        )
        if not changed_files:
            stats["status"] = "no_activity"
            return stats

        if is_sniper:
            console.print(f"  [dim]Found {len(changed_files)} changed files (lookback: {days_used}d)[/dim]")

        # --- 2. Build / refresh doc index ---
        try:
            if needs_reindex(work_dir):
                build_index(work_dir)
        except Exception as e:
            logger.error(f"Index build failed for {repo_name}: {e}")
            stats["status"] = "index_failed"
            return stats

        # --- 3. Choose how many files to inspect ---
        limit = 10 if is_sniper else 3
        files_to_check = changed_files[:limit]

        # --- 4. Per-file symbol loop ---
        for filepath in files_to_check:
            old_code, new_code = GitOps.get_file_content(work_dir, filepath)
            if not old_code or not new_code or old_code.strip() == new_code.strip():
                continue

            try:
                symbols = get_changed_symbols(filepath, old_code, new_code)
            except Exception as e:
                logger.warning(f"Symbol extraction failed for {filepath}: {e}")
                continue

            # Check up to 2 symbols per file to respect rate limits
            for sym in symbols[:2]:
                matches = search_docs(work_dir, sym.name)
                if not matches:
                    stats["undocumented"] += 1
                    continue

                # Only check the single best semantic match
                best = matches[0]

                # --- LLM verdict (may raise RateLimitExceeded) ---
                verdict = check_consistency(
                    symbol_name=sym.name,
                    old_code=sym.old_code,
                    new_code=sym.new_code,
                    doc_content=best['content'],
                    doc_file=best['source_file'],
                    doc_line=best['start_line'],
                    doc_heading=best['heading'],
                    repo_path=work_dir
                )

                if verdict is None:
                    continue

                if verdict.stale:
                    stats["findings"].append({
                        "file":     filepath,
                        "symbol":   sym.name,
                        "severity": verdict.severity,
                        "reason":   verdict.reason,
                        "doc_file": best['source_file'],
                        "doc_line": best['start_line'],
                        "doc_section": best['heading']
                    })
                    if verdict.severity == "error":
                        stats["critical_errors"] += 1
                    else:
                        stats["warnings"] += 1

    except RateLimitExceeded:
        # Propagate upward so the orchestrator can save state cleanly
        raise

    except Exception as e:
        logger.exception(f"Fatal error auditing {repo_name}: {e}")
        stats["status"] = "fatal_error"

    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return stats


# ==========================================
# REPORTING HELPERS
# ==========================================
def _print_sniper_result(result: dict):
    """Pretty-print the result of a single-repo sniper audit."""
    console.print()

    if result["status"] == "clone_failed":
        console.print(Panel("[red]❌ Failed to clone repository.[/red]", title="Result"))
        return

    if result["status"] == "no_activity":
        console.print(Panel(
            "[yellow]😴 No code changes detected in the lookback window.\n"
            "This repo appears dormant.[/yellow]",
            title="Result"
        ))
        return

    if result["status"] == "index_failed":
        console.print(Panel("[red]❌ Documentation index build failed.[/red]", title="Result"))
        return

    # Build findings table
    if result["findings"]:
        table = Table(title="Findings", box=box.ROUNDED, show_lines=True)
        table.add_column("Symbol", style="cyan", no_wrap=True)
        table.add_column("Severity", justify="center")
        table.add_column("Doc File", style="dim")
        table.add_column("Reason")

        for f in result["findings"]:
            sev = f["severity"]
            colour = "red" if sev == "error" else "yellow" if sev == "warning" else "blue"
            table.add_row(
                f["symbol"],
                f"[{colour}]{sev.upper()}[/{colour}]",
                os.path.basename(f.get("doc_file", "?")),
                f["reason"]
            )
        console.print(table)
    else:
        console.print("[green]No stale documentation found.[/green]")

    # Summary banner
    errors   = result["critical_errors"]
    warnings = result["warnings"]
    undoc    = result["undocumented"]

    summary = (
        f"[bold]Critical errors:[/bold] [red]{errors}[/red]   "
        f"[bold]Warnings:[/bold] [yellow]{warnings}[/yellow]   "
        f"[bold]Undocumented symbols:[/bold] [blue]{undoc}[/blue]"
    )
    console.print(Panel(summary, title="Summary"))

    if errors > 0:
        console.print("\n[bold red]🚨 CRITICAL DRIFT DETECTED — documentation is actively misleading![/bold red]")
    elif warnings > 0:
        console.print("\n[bold yellow]⚠️  Some documentation is outdated. Worth a review.[/bold yellow]")
    else:
        console.print("\n[bold green]✅ Documentation appears to be in sync.[/bold green]")


def _print_wall_of_shame(results: list):
    """Print the mass-scan leaderboard table."""
    console.rule("[bold red]🏆 WALL OF SHAME — Top 15 Most Drifted Repos[/bold red]")
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE_HEAVY)
    table.add_column("Repository",  style="cyan")
    table.add_column("⭐ Stars",    justify="right", style="dim")
    table.add_column("🔴 Errors",  justify="right", style="red")
    table.add_column("⚠️  Warnings", justify="right", style="yellow")
    table.add_column("📭 Undoc",   justify="right", style="blue")
    table.add_column("Status",     justify="center")

    for r in results[:15]:
        colour = "green" if r["status"] == "success" else "red"
        table.add_row(
            r["repo"],
            str(r["stars"]),
            str(r["critical_errors"]),
            str(r["warnings"]),
            str(r["undocumented"]),
            f"[{colour}]{r['status']}[/{colour}]"
        )
    console.print(table)


# ==========================================
# MAIN ORCHESTRATOR
# ==========================================
def main():
    parser = argparse.ArgumentParser(
        description="DocDrift — Find documentation drift in Python/JS repositories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scanner.py                          # Mass scan top 100 GitHub repos
  python scanner.py --url https://github.com/psf/requests   # Sniper mode
  python scanner.py --local /path/to/project  # Local repo scan
  python scanner.py --local .                 # Current directory
        """
    )
    parser.add_argument("--url",   "-u", type=str, help="Remote GitHub URL to audit (sniper mode)")
    parser.add_argument("--local", "-l", type=str, help="Local repo path to audit (use '.' for current dir)")
    parser.add_argument("--resume",      action="store_true", help=f"Resume from {PROGRESS_FILE} if it exists")
    args = parser.parse_args()

    console.rule("[bold cyan] DocDrift Enterprise Auditor [/bold cyan]")

    # ──────────────────────────────────────────────
    # MODE 1: LOCAL DIRECTORY SCAN
    # ──────────────────────────────────────────────
    if args.local:
        local_path = os.path.abspath(args.local)
        if not os.path.isdir(local_path):
            console.print(f"[red]❌ Directory not found: {local_path}[/red]")
            sys.exit(1)

        repo_name = os.path.basename(local_path)
        console.print(f"\n[bold green]📂 LOCAL MODE: {local_path}[/bold green]")

        target = {"full_name": repo_name, "url": "local", "stars": "N/A"}
        with console.status(f"[cyan]Auditing {repo_name}...", spinner="bouncingBar"):
            try:
                result = audit_repo(target, is_sniper=True, repo_path=local_path)
            except RateLimitExceeded as e:
                console.print(f"\n[bold red]⛔ Rate limit hit: {e}[/bold red]")
                console.print(f"[yellow]Partial results not saved (single-repo mode).[/yellow]")
                sys.exit(1)

        _print_sniper_result(result)

        report_path = f"docdrift_{repo_name}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        console.print(f"\n[dim]Full report → {report_path}[/dim]")
        return

    # ──────────────────────────────────────────────
    # MODE 2: SNIPER — Single remote URL
    # ──────────────────────────────────────────────
    if args.url:
        parts     = args.url.rstrip("/").split("/")
        repo_name = "/".join(parts[-2:])
        console.print(f"\n[bold green]🎯 SNIPER MODE: {repo_name}[/bold green]")

        target = {"full_name": repo_name, "url": args.url, "stars": "N/A"}
        with console.status(f"[cyan]Cloning and auditing {repo_name}...", spinner="bouncingBar"):
            try:
                result = audit_repo(target, is_sniper=True)
            except RateLimitExceeded as e:
                console.print(f"\n[bold red]⛔ Rate limit hit: {e}[/bold red]")
                sys.exit(1)

        _print_sniper_result(result)

        report_path = f"docdrift_{repo_name.replace('/', '_')}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        console.print(f"\n[dim]Full report → {report_path}[/dim]")
        return

    # ──────────────────────────────────────────────
    # MODE 3: MASS SCAN (Top 100 repos)
    # ──────────────────────────────────────────────
    api   = GitHubAPI(GITHUB_TOKEN)
    repos = api.get_top_repos(TARGET_REPOS)

    # Optionally resume from a previous interrupted run
    completed_names = set()
    results = []
    if args.resume:
        results = load_progress()
        completed_names = {r["repo"] for r in results}
        console.print(f"[yellow]Resuming — {len(results)} repos already done.[/yellow]")

    repos_to_do = [r for r in repos if r["full_name"] not in completed_names]
    console.print(f"\n[cyan]Scanning {len(repos_to_do)} repos with {MAX_WORKERS} workers...[/cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Auditing...", total=len(repos_to_do))

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_map = {executor.submit(audit_repo, repo, False): repo for repo in repos_to_do}

            for future in as_completed(future_map):
                try:
                    result = future.result()
                    results.append(result)
                    # Rolling backup after every completed repo
                    with open(BACKUP_FILE, 'w') as f:
                        json.dump(results, f, indent=2)

                except RateLimitExceeded as e:
                    console.print(f"\n[bold red]⛔ Daily quota exhausted: {e}[/bold red]")
                    console.print(f"[yellow]Saving progress to {PROGRESS_FILE}...[/yellow]")
                    save_progress(results, PROGRESS_FILE)
                    executor.shutdown(wait=False, cancel_futures=True)
                    console.print(f"[green]Run with --resume tomorrow to continue.[/green]")
                    sys.exit(0)

                except Exception as e:
                    repo_info = future_map[future]
                    logger.error(f"Future failed for {repo_info['full_name']}: {e}")

                finally:
                    progress.advance(task)

    # Sort by most critical issues first
    results.sort(key=lambda x: (x.get("critical_errors", 0), x.get("warnings", 0)), reverse=True)

    with open(FINAL_REPORT, 'w') as f:
        json.dump(results, f, indent=2)
    console.print(f"\n[green]✅ Final report saved → {FINAL_REPORT}[/green]")

    _print_wall_of_shame(results)

    # Print aggregate stats
    total_errors   = sum(r.get("critical_errors", 0) for r in results)
    total_warnings = sum(r.get("warnings", 0) for r in results)
    total_undoc    = sum(r.get("undocumented", 0) for r in results)
    console.print(
        f"\n[bold]Totals across {len(results)} repos:[/bold] "
        f"[red]{total_errors} critical errors[/red] · "
        f"[yellow]{total_warnings} warnings[/yellow] · "
        f"[blue]{total_undoc} undocumented symbols[/blue]"
    )


if __name__ == "__main__":
    main()
