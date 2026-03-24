import subprocess
import os
import json
import tempfile
import time
import shutil
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests as req

# Rich for Pro-Level Terminal UI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

# Your local modules
from docwatcher.symbol_extractor import get_changed_symbols
from docwatcher.embeddings import build_index, search_docs
from docwatcher.llm_checker import check_consistency

# ==========================================
# CONFIGURATION & SETUP
# ==========================================
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
MAX_WORKERS = 4  # Number of repos to scan in parallel
TARGET_REPOS = 10
MIN_STARS = 5000
DAYS_TO_LOOK_BACK = 14

console = Console()
logging.basicConfig(
    filename='docdrift_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==========================================
# GITHUB API MANAGER (Rate Limit Safe)
# ==========================================
class GitHubAPI:
    def __init__(self, token: str):
        self.headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"} if token else {}
        self.session = req.Session()
        self.session.headers.update(self.headers)

    def _handle_rate_limit(self, response):
        remaining = int(response.headers.get('X-RateLimit-Remaining', 1))
        if remaining <= 1:
            reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
            sleep_time = max(reset_time - time.time(), 0) + 5
            console.print(f"[yellow]⚠️ API Rate limit hit. Sleeping for {sleep_time:.0f}s...[/yellow]")
            logging.warning(f"Rate limit hit. Sleeping {sleep_time}s.")
            time.sleep(sleep_time)

    def get_top_repos(self, count: int) -> list:
        repos = []
        page = 1
        with console.status("[bold cyan]Querying GitHub API for top Python repos...", spinner="dots"):
            while len(repos) < count:
                try:
                    res = self.session.get(
                        "https://api.github.com/search/repositories",
                        params={"q": f"language:python stars:>{MIN_STARS}", "sort": "stars", "order": "desc", "per_page": 30, "page": page},
                        timeout=15
                    )
                    self._handle_rate_limit(res)
                    res.raise_for_status()
                    
                    items = res.json().get("items", [])
                    if not items: break
                    
                    for item in items:
                        repos.append({
                            "full_name": item["full_name"],
                            "stars": item["stargazers_count"],
                            "url": item["html_url"],
                            "default_branch": item.get("default_branch", "main")
                        })
                    page += 1
                    time.sleep(2)  # Secondary rate limit buffer
                except Exception as e:
                    logging.error(f"GitHub API Error on page {page}: {e}")
                    console.print(f"[red]❌ API Error: {e}[/red]")
                    break
        return repos[:count]

# ==========================================
# GIT CORE OPERATIONS
# ==========================================
class GitOps:
    @staticmethod
    def clone_repo(repo_name: str, branch: str, target_dir: str) -> bool:
        try:
            # Shallow clone specifically targeting the default branch
            cmd = ["git", "clone", "--depth", "50", "--branch", branch, "--single-branch", f"https://github.com/{repo_name}.git", target_dir]
            subprocess.run(cmd, capture_output=True, timeout=300, check=True)
            return True
        except subprocess.TimeoutExpired:
            logging.error(f"Timeout cloning {repo_name}")
            return False
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to clone {repo_name}: {e.stderr.decode('utf-8', errors='ignore')}")
            return False

    @staticmethod
    def get_recent_files(repo_path: str, days: int) -> list:
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            res = subprocess.run(
                ["git", "log", f"--since={since_date}", "--name-only", "--pretty=format:"],
                capture_output=True, text=True, cwd=repo_path, check=True
            )
            files = set(f.strip() for f in res.stdout.split("\n") if f.endswith(('.py', '.js', '.ts')) and f.strip())
            return list(files)
        except Exception as e:
            logging.error(f"Git log failed in {repo_path}: {e}")
            return []

    @staticmethod
    def get_file_content(repo_path: str, filepath: str, commit_ref: str = "HEAD~10"):
        try:
            old = subprocess.run(["git", "show", f"{commit_ref}:{filepath}"], capture_output=True, text=True, cwd=repo_path).stdout
            new_path = os.path.join(repo_path, filepath)
            new = open(new_path, 'r', errors='ignore').read() if os.path.exists(new_path) else ''
            return old, new
        except Exception:
            return '', ''

# ==========================================
# AUDIT ENGINE
# ==========================================
def audit_single_repo(repo: dict) -> dict:
    repo_name = repo["full_name"]
    branch = repo["default_branch"]
    stats = {
        "repo": repo_name,
        "stars": repo["stars"],
        "url": repo["url"],
        "critical_errors": 0,
        "warnings": 0,
        "undocumented": 0,
        "findings": [],
        "status": "success"
    }

    tmp_dir = tempfile.mkdtemp()
    try:
        if not GitOps.clone_repo(repo_name, branch, tmp_dir):
            stats["status"] = "clone_failed"
            return stats

        changed_files = GitOps.get_recent_files(tmp_dir, DAYS_TO_LOOK_BACK)
        if not changed_files:
            stats["status"] = "no_activity"
            return stats

        try:
            build_index(tmp_dir)
        except Exception as e:
            logging.error(f"Indexing failed for {repo_name}: {e}")
            stats["status"] = "index_failed"
            return stats

        for filepath in changed_files[:15]:  # Process top 5 files to save time
            old_code, new_code = GitOps.get_file_content(tmp_dir, filepath)
            if not old_code or not new_code or old_code == new_code:
                continue

            try:
                symbols = get_changed_symbols(filepath, old_code, new_code)
            except Exception as e:
                logging.error(f"Symbol extraction failed in {filepath}: {e}")
                continue

            for sym in symbols[:3]:
                matches = search_docs(tmp_dir, sym.name)
                if not matches:
                    stats["undocumented"] += 1
                    continue

                for match in matches[:1]:
                    try:
                        verdict = check_consistency(
                            symbol_name=sym.name,
                            old_code=sym.old_code,
                            new_code=sym.new_code,
                            doc_content=match['content']
                        )
                        if verdict and verdict.stale:
                            stats["findings"].append({
                                "file": filepath,
                                "symbol": sym.name,
                                "doc_file": match.get('source_file', 'unknown'),
                                "severity": verdict.severity,
                                "reason": verdict.reason
                            })
                            if verdict.severity == "error":
                                stats["critical_errors"] += 1
                            else:
                                stats["warnings"] += 1
                    except Exception as e:
                        logging.error(f"LLM Check failed for {sym.name}: {e}")
                        continue
                        
    except Exception as e:
        logging.critical(f"Fatal error auditing {repo_name}: {e}")
        stats["status"] = "fatal_error"
    finally:
        # Hard cleanup to prevent disk bloat
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return stats

# ==========================================
# MAIN ORCHESTRATOR
# ==========================================
def main():
    console.rule("[bold cyan]DOCDRIFT ENTERPRISE AUDITOR[/bold cyan]")
    
    api = GitHubAPI(GITHUB_TOKEN)
    repos = api.get_top_repos(TARGET_REPOS)
    
    if not repos:
        console.print("[red]Failed to fetch repositories. Check your network or token.[/red]")
        return

    results = []
    
    # Multithreading with Beautiful Progress Bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Auditing repositories...", total=len(repos))
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_repo = {executor.submit(audit_single_repo, repo): repo for repo in repos}
            
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Save state dynamically in case of crash
                    with open("audit_state_backup.json", "w") as f:
                        json.dump(results, f, indent=2)
                        
                except Exception as e:
                    logging.error(f"Thread failed for {repo['full_name']}: {e}")
                finally:
                    progress.advance(task)

    # Sort results by most critical errors (Wall of Shame logic)
    results.sort(key=lambda x: x.get("critical_errors", 0), reverse=True)

    # Generate the Final JSON
    with open("docdrift_final_report.json", "w") as f:
        json.dump(results, f, indent=2)

    # ==========================================
    # RICH TERMINAL REPORTING
    # ==========================================
    console.rule("[bold red]🏆 THE WALL OF SHAME (Top 15)[/bold red]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Repository", style="cyan", width=35)
    table.add_column("Stars", justify="right", style="green")
    table.add_column("Critical Mismatches", justify="right", style="red")
    table.add_column("Stale Warnings", justify="right", style="yellow")
    table.add_column("Undocumented", justify="right", style="blue")
    table.add_column("Status", justify="center")

    total_errors = sum(r.get('critical_errors', 0) for r in results)
    
    for r in results[:15]:
        status_color = "green" if r["status"] == "success" else "red"
        table.add_row(
            r["repo"],
            f"{r['stars']:,}",
            str(r["critical_errors"]),
            str(r["warnings"]),
            str(r["undocumented"]),
            f"[{status_color}]{r['status']}[/{status_color}]"
        )

    console.print(table)
    console.print(f"\n[bold green]✅ Audit Complete![/bold green] Found a total of [bold red]{total_errors}[/bold red] critical doc mismatches.")
    console.print("📄 Detailed logs saved to [italic]docdrift_audit.log[/italic]")
    console.print("💾 Full data saved to [italic]docdrift_final_report.json[/italic]")

if __name__ == "__main__":
    main()