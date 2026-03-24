import os
import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from docwatcher.config import is_configured, setup_config
from docwatcher.diff_parser import get_changed_files
from docwatcher.engine import analyze_repo
from docwatcher.embeddings import build_index, needs_reindex, search_docs
from docwatcher.fixer import apply_fix, generate_fix
from docwatcher.llm_checker import is_lm_studio_running

console = Console()


def _status_badge(enabled: bool) -> str:
    return "[green]ready[/green]" if enabled else "[yellow]offline[/yellow]"


def _print_commit_banner(files, symbols, llm_available):
    table = Table.grid(expand=True)
    table.add_column(justify="left")
    table.add_column(justify="left")
    table.add_column(justify="left")
    table.add_row(
        f"[bold]{len(files)}[/bold] staged file(s)",
        f"[bold]{len(symbols)}[/bold] changed symbol(s)",
        f"AI {_status_badge(llm_available)}",
    )
    console.print(Panel(table, title="DocDrift Commit", border_style="green"))


def _print_finding(verdict, symbol, level: str):
    accent = {
        "error": "red",
        "warning": "yellow",
        "info": "blue",
    }.get(level, "white")
    heading = verdict.doc_heading or "Untitled section"
    body = (
        f"[bold]{symbol.name}[/bold] in [dim]{symbol.file_path}[/dim]\n"
        f"Docs: [cyan]{verdict.doc_file}:{verdict.doc_line}[/cyan] ([dim]{heading}[/dim])\n"
        f"[{accent}]{verdict.reason}[/{accent}]"
    )
    console.print(Panel(body, border_style=accent, title=level.upper()))


def _print_fix_preview(suggested: str):
    console.print(Panel(suggested, title="Suggested Fix", border_style="green"))


@click.group()
def cli():
    pass


@cli.command()
@click.argument("repo_path", default=".")
def precommit(repo_path):
    console.print("\n[bold green]DocDrift[/bold green] pre-commit check...\n")

    if needs_reindex(repo_path):
        build_index(repo_path)

    files = get_changed_files(repo_path)
    if not files:
        sys.exit(0)

    analysis = analyze_repo(repo_path)
    all_symbols = analysis.changed_symbols

    if not all_symbols:
        sys.exit(0)

    llm_available = analysis.llm_available
    errors = analysis.errors
    warnings = analysis.warnings
    undocumented = analysis.undocumented

    if errors:
        console.print(
            f"[bold red]DocDrift blocked this commit - {len(errors)} stale doc(s) found[/bold red]\n"
        )
        for verdict, _symbol in errors:
            console.print(f"[red]ERROR[/red] {verdict.symbol_name} - {verdict.doc_file} line {verdict.doc_line}")
            console.print(f"  {verdict.reason}\n")

        for symbol in undocumented:
            console.print(f"[red]UNDOCUMENTED[/red] {symbol.name} - {symbol.file_path}\n")

        console.print("[dim]Options:[/dim]")
        console.print("[dim]  Run './docdrift commit' to fix interactively[/dim]")
        console.print("[dim]  Run 'git commit --no-verify' to skip this check[/dim]")
        sys.exit(1)

    if warnings or undocumented:
        console.print(
            f"[yellow]DocDrift warnings - {len(warnings)} warnings, {len(undocumented)} undocumented[/yellow]"
        )
        for verdict, _symbol in warnings:
            console.print(f"[yellow]WARNING[/yellow] {verdict.symbol_name} - {verdict.reason}")
        for symbol in undocumented:
            console.print(f"[yellow]UNDOCUMENTED[/yellow] {symbol.name} - {symbol.file_path}")
        console.print("\n[dim]Commit allowed - run './docdrift commit' to fix[/dim]")
        sys.exit(0)

    console.print("[green]All docs look accurate - commit allowed[/green]")
    sys.exit(0)


@cli.command()
@click.argument("repo_path", default=".")
def index(repo_path):
    console.print("[bold green]DocDrift[/bold green] building index...")
    count = build_index(repo_path)
    console.print(f"[green]Indexed {count} documentation chunks[/green]")


@cli.command()
@click.argument("message", required=False)
@click.argument("repo_path", default=".")
def commit(message, repo_path):
    if not is_configured(repo_path):
        setup_config(repo_path)

    console.print("\n[bold green]DocDrift[/bold green] scanning before commit...\n")

    if needs_reindex(repo_path):
        build_index(repo_path)

    if not get_changed_files(repo_path):
        console.print("[yellow]No changed files found - stage files first with git add[/yellow]")
        return

    analysis = analyze_repo(repo_path)
    files = analysis.changed_files
    all_symbols = analysis.changed_symbols

    if not all_symbols:
        console.print("[yellow]No changed functions or classes found in staged files[/yellow]")
        return

    llm_available = analysis.llm_available
    _print_commit_banner(files, all_symbols, llm_available)

    if not llm_available:
        console.print(
            "[yellow]AI is not available, so DocDrift can only surface undocumented symbols right now[/yellow]\n"
        )

    errors = analysis.errors
    warnings = analysis.warnings
    undocumented = analysis.undocumented
    total = len(errors) + len(warnings) + len(undocumented)
    fixed_count = 0
    generated_count = 0

    if total == 0:
        console.print("[bold green]All docs look accurate[/bold green]\n")
    else:
        console.print(
            f"[bold]Found {len(errors)} errors · {len(warnings)} warnings · {len(undocumented)} undocumented[/bold]\n"
        )

        for verdict, symbol in errors:
            _print_finding(verdict, symbol, "error")
            if console.input("  Fix this? (y/n): ").strip().lower() != "y":
                continue

            console.print("  [dim]Generating fix...[/dim]")
            suggested = generate_fix(
                old_doc=verdict.doc_content,
                reason=verdict.reason,
                old_code=symbol.old_code,
                new_code=symbol.new_code,
                repo_path=repo_path,
            )
            if not suggested:
                console.print("  [red]Could not generate a fix[/red]\n")
                continue

            _print_fix_preview(suggested)
            apply = console.input("  Apply? (y/n/e to edit): ").strip().lower()
            if apply == "y":
                success = apply_fix(verdict.doc_file, verdict.doc_content, suggested)
                if success:
                    fixed_count += 1
                    console.print("  [bold green]Fixed[/bold green]\n")
                else:
                    console.print("  [red]Could not apply - fix manually[/red]\n")
            elif apply == "e":
                console.print(f"  [dim]Open {verdict.doc_file} line {verdict.doc_line} and edit manually[/dim]\n")

        for verdict, symbol in warnings:
            _print_finding(verdict, symbol, "warning")
            if console.input("  Fix this? (y/n): ").strip().lower() != "y":
                continue

            console.print("  [dim]Generating fix...[/dim]")
            suggested = generate_fix(
                old_doc=verdict.doc_content,
                reason=verdict.reason,
                old_code=symbol.old_code,
                new_code=symbol.new_code,
                repo_path=repo_path,
            )
            if not suggested:
                console.print("  [red]Could not generate a fix[/red]\n")
                continue

            _print_fix_preview(suggested)
            apply = console.input("  Apply? (y/n/e to edit): ").strip().lower()
            if apply == "y":
                success = apply_fix(verdict.doc_file, verdict.doc_content, suggested)
                if success:
                    fixed_count += 1
                    console.print("  [bold green]Fixed[/bold green]\n")
            elif apply == "e":
                console.print(f"  [dim]Open {verdict.doc_file} line {verdict.doc_line} and edit manually[/dim]\n")

        if undocumented:
            console.print(f"\n[bold yellow]{len(undocumented)} undocumented symbols found[/bold yellow]\n")
            for symbol in undocumented:
                console.print(f"[yellow]UNDOCUMENTED[/yellow] [cyan]{symbol.name}[/cyan] - [dim]{symbol.file_path}[/dim]")

            console.print()
            if console.input("[yellow]Auto-document all in README? (y/n): [/yellow]").strip().lower() == "y":
                readme_path = os.path.join(repo_path, "README.md")
                additions = []

                for symbol in undocumented:
                    console.print(f"  [dim]Documenting {symbol.name}...[/dim]")
                    suggested = generate_fix(
                        old_doc="",
                        reason=f"New symbol {symbol.name} needs documentation",
                        old_code="",
                        new_code=symbol.new_code,
                        repo_path=repo_path,
                    )
                    if suggested:
                        additions.append(f"\n## {symbol.name}\n\n{suggested}\n")
                        generated_count += 1
                        console.print(f"  [green]Generated docs for {symbol.name}[/green]")

                if additions:
                    with open(readme_path, "a", encoding="utf-8") as handle:
                        handle.write("\n" + "\n".join(additions))
                    console.print(f"\n[bold green]Added {len(additions)} new sections to README[/bold green]\n")

        if fixed_count or generated_count:
            summary = []
            if fixed_count:
                summary.append(f"[green]{fixed_count}[/green] fix(es) applied")
            if generated_count:
                summary.append(f"[green]{generated_count}[/green] doc section(s) generated")
            console.print(Panel(" · ".join(summary), title="Ready To Commit", border_style="green"))

    console.print()
    if console.input("[bold]Commit now? (y/n): [/bold]").strip().lower() != "y":
        console.print("[dim]Cancelled[/dim]")
        return

    if not message:
        message = console.input("[yellow]Commit message: [/yellow]").strip()
    if not message:
        console.print("[red]No message - aborting[/red]")
        return

    build_index(repo_path)
    subprocess.run(["git", "add", "-A"])
    result = subprocess.run(["git", "commit", "--no-verify", "-m", message])
    if result.returncode == 0:
        console.print("\n[bold green]Committed[/bold green]")
    else:
        console.print("\n[red]Commit failed[/red]")


@cli.command()
@click.argument("repo_path", default=".")
@click.option("--no-llm", is_flag=True, help="Skip LLM check, show matches only")
def check(repo_path, no_llm):
    if not is_configured(repo_path):
        setup_config(repo_path)

    console.print("\n[bold green]DocDrift[/bold green] scanning...\n")

    if needs_reindex(repo_path):
        console.print("[dim]Docs changed - rebuilding index...[/dim]")
        count = build_index(repo_path)
        console.print(f"[dim]Indexed {count} chunks[/dim]\n")

    llm_available = is_lm_studio_running(repo_path)
    if not llm_available and not no_llm:
        console.print("[yellow]No AI model running - showing doc matches only[/yellow]")
        console.print("[dim]Set GROQ_API_KEY or start LM Studio for full analysis[/dim]\n")

    files = get_changed_files(repo_path)
    if not files:
        console.print("[yellow]No changed files found[/yellow]")
        console.print("[dim]Edit some code files and run check again[/dim]")
        return

    all_symbols = []
    for changed_file in files:
        all_symbols.extend(
            get_changed_symbols(
                changed_file.path,
                changed_file.old_content,
                changed_file.new_content,
            )
        )

    if not all_symbols:
        console.print("[yellow]No trackable symbols found in changed files[/yellow]")
        return

    console.print(f"[dim]Found {len(all_symbols)} changed symbol(s)[/dim]\n")

    analysis = analyze_repo(repo_path, use_llm=not no_llm)
    errors = analysis.errors
    warnings = analysis.warnings
    infos = analysis.infos
    undocumented = analysis.undocumented

    if not analysis.llm_available or no_llm:
        for _verdict, symbol, matches in infos:
            console.print(f"[bold yellow]DOC MATCH[/bold yellow] [cyan]{symbol.name}[/cyan] - [dim]{symbol.file_path}[/dim]")
            for match in matches:
                console.print(f"  [yellow]>[/yellow] {match['source_file']} line {match['start_line']} - {match['heading']}")
                console.print(f"    [dim]score: {match['distance']}[/dim]\n")
        for symbol in undocumented:
            console.print(f"[bold red]UNDOCUMENTED[/bold red] [cyan]{symbol.name}[/cyan] - [dim]{symbol.file_path}[/dim]\n")
        return

    console.print()

    for verdict, symbol in errors:
        _print_finding(verdict, symbol, "error")
        fix = console.input("  Want DocDrift to fix this? (y/n): ").strip().lower()
        if fix != "y":
            console.print("  [dim]Skipped[/dim]\n")
            continue

        console.print("  [dim]Generating fix...[/dim]")
        suggested = generate_fix(
            old_doc=verdict.doc_content,
            reason=verdict.reason,
            old_code=symbol.old_code,
            new_code=symbol.new_code,
            repo_path=repo_path,
        )
        if not suggested:
            console.print("  [red]Could not generate fix[/red]")
            continue

        _print_fix_preview(suggested)
        apply = console.input("  Apply this fix? (y/n/e to edit): ").strip().lower()
        if apply == "y":
            success = apply_fix(verdict.doc_file, verdict.doc_content, suggested)
            if success:
                console.print(f"  [bold green]Fixed - {verdict.doc_file} updated[/bold green]\n")
            else:
                console.print("  [red]Could not apply automatically - update manually[/red]\n")
        elif apply == "e":
            console.print(f"  [dim]Open {verdict.doc_file} line {verdict.doc_line} and edit manually[/dim]\n")
        else:
            console.print("  [dim]Skipped[/dim]\n")

    for verdict, symbol in warnings:
        _print_finding(verdict, symbol, "warning")
        fix = console.input("  Want DocDrift to fix this? (y/n): ").strip().lower()
        if fix != "y":
            console.print("  [dim]Skipped[/dim]\n")
            continue

        console.print("  [dim]Generating fix...[/dim]")
        suggested = generate_fix(
            old_doc=verdict.doc_content,
            reason=verdict.reason,
            old_code=symbol.old_code,
            new_code=symbol.new_code,
            repo_path=repo_path,
        )
        if not suggested:
            console.print("  [red]Could not generate fix[/red]")
            continue

        _print_fix_preview(suggested)
        apply = console.input("  Apply this fix? (y/n/e to edit): ").strip().lower()
        if apply == "y":
            success = apply_fix(verdict.doc_file, verdict.doc_content, suggested)
            if success:
                console.print(f"  [bold green]Fixed - {verdict.doc_file} updated[/bold green]\n")
        elif apply == "e":
            console.print(f"  [dim]Open {verdict.doc_file} line {verdict.doc_line} and edit manually[/dim]\n")
        else:
            console.print("  [dim]Skipped[/dim]\n")

    for verdict, symbol, _matches in infos:
        if verdict is None:
            continue
        _print_finding(verdict, symbol, "info")

    for symbol in undocumented:
        console.print(f"[bold red]UNDOCUMENTED[/bold red] [cyan]{symbol.name}[/cyan] - [dim]{symbol.file_path}[/dim]\n")

    total = len(errors) + len(warnings) + len([item for item in infos if item[0] is not None]) + len(undocumented)
    if total == 0:
        console.print("[bold green]All documentation looks accurate[/bold green]")
    else:
        info_count = len([item for item in infos if item[0] is not None])
        console.print(
            f"[bold]Found {len(errors)} errors · {len(warnings)} warnings · {info_count} info · {len(undocumented)} undocumented[/bold]"
        )
        if errors or warnings:
            console.print("\n[dim]Run './docdrift commit' to fix and commit interactively[/dim]")


if __name__ == "__main__":
    cli()
