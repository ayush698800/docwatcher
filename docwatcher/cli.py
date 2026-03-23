import click
import os
import sys
from rich.console import Console
from docwatcher.diff_parser import get_changed_files
from docwatcher.symbol_extractor import get_changed_symbols
from docwatcher.embeddings import build_index, search_docs, needs_reindex
from docwatcher.llm_checker import check_consistency, is_lm_studio_running
from docwatcher.config import is_configured, setup_config
from docwatcher.fixer import generate_fix, apply_fix

console = Console()

@click.group()
def cli():
    pass

@cli.command()
@click.argument('repo_path', default='.')
def precommit(repo_path):
    console.print("\n[bold green]DocDrift[/bold green] pre-commit check...\n")

    if needs_reindex(repo_path):
        build_index(repo_path)

    files = get_changed_files(repo_path)

    if not files:
        sys.exit(0)

    all_symbols = []
    for f in files:
        symbols = get_changed_symbols(f.path, f.old_content, f.new_content)
        all_symbols.extend(symbols)

    if not all_symbols:
        sys.exit(0)

    llm_available = is_lm_studio_running(repo_path)

    errors = []
    warnings = []
    undocumented = []

    for symbol in all_symbols:
        matches = search_docs(repo_path, symbol.name)

        if not matches:
            undocumented.append(symbol)
            continue

        if not llm_available:
            continue

        for match in matches:
            verdict = check_consistency(
                symbol_name=symbol.name,
                old_code=symbol.old_code,
                new_code=symbol.new_code,
                doc_content=match['content'],
                doc_file=match['source_file'],
                doc_line=match['start_line'],
                doc_heading=match['heading'],
                repo_path=repo_path
            )
            if verdict and verdict.stale:
                if verdict.severity == 'error':
                    errors.append(verdict)
                else:
                    warnings.append(verdict)

    if errors:
        console.print(f"[bold red]DocDrift blocked this commit — {len(errors)} stale doc(s) found[/bold red]\n")
        for v in errors:
            console.print(f"[red]ERROR[/red] {v.symbol_name} — {v.doc_file} line {v.doc_line}")
            console.print(f"  {v.reason}\n")

        for s in undocumented:
            console.print(f"[red]UNDOCUMENTED[/red] {s.name} — {s.file_path}\n")

        console.print("[dim]Options:[/dim]")
        console.print("[dim]  Run './docdrift commit' to fix interactively[/dim]")
        console.print("[dim]  Run 'git commit --no-verify' to skip this check[/dim]")
        sys.exit(1)

    if warnings or undocumented:
        console.print(f"[yellow]DocDrift warnings — {len(warnings)} warnings, {len(undocumented)} undocumented[/yellow]")
        for v in warnings:
            console.print(f"[yellow]WARNING[/yellow] {v.symbol_name} — {v.reason}")
        for s in undocumented:
            console.print(f"[yellow]UNDOCUMENTED[/yellow] {s.name} — {s.file_path}")
        console.print("\n[dim]Commit allowed — run './docdrift commit' to fix[/dim]")
        sys.exit(0)

    console.print("[green]All docs look accurate — commit allowed[/green]")
    sys.exit(0)


@cli.command()
@click.argument('repo_path', default='.')
def index(repo_path):
    console.print("[bold green]DocDrift[/bold green] building index...")
    count = build_index(repo_path)
    console.print(f"[green]Indexed {count} documentation chunks[/green]")


@cli.command()
@click.argument('message', required=False)
@click.argument('repo_path', default='.')
def commit(message, repo_path):
    import subprocess

    if not is_configured(repo_path):
        setup_config(repo_path)

    console.print("\n[bold green]DocDrift[/bold green] scanning before commit...\n")

    if needs_reindex(repo_path):
        build_index(repo_path)

    files = get_changed_files(repo_path)

    if not files:
        console.print("[yellow]No changed files found — stage files first with git add[/yellow]")
        return

    all_symbols = []
    for f in files:
        symbols = get_changed_symbols(f.path, f.old_content, f.new_content)
        all_symbols.extend(symbols)

    llm_available = is_lm_studio_running(repo_path)
    errors = []
    warnings = []
    undocumented = []

    for symbol in all_symbols:
        matches = search_docs(repo_path, symbol.name)
        if not matches:
            undocumented.append(symbol)
            continue
        if not llm_available:
            continue
        for match in matches:
            verdict = check_consistency(
                symbol_name=symbol.name,
                old_code=symbol.old_code,
                new_code=symbol.new_code,
                doc_content=match['content'],
                doc_file=match['source_file'],
                doc_line=match['start_line'],
                doc_heading=match['heading'],
                repo_path=repo_path
            )
            if verdict and verdict.stale:
                if verdict.severity == 'error':
                    errors.append((verdict, symbol))
                else:
                    warnings.append((verdict, symbol))

    total = len(errors) + len(warnings) + len(undocumented)

    if total == 0:
        console.print("[bold green]All docs look accurate[/bold green]\n")
    else:
        console.print(f"[bold]Found {len(errors)} errors · {len(warnings)} warnings · {len(undocumented)} undocumented[/bold]\n")

        for v, symbol in errors:
            console.print(f"[bold red]ERROR[/bold red] [cyan]{v.symbol_name}[/cyan]")
            console.print(f"  {v.doc_file} line {v.doc_line}")
            console.print(f"  [red]{v.reason}[/red]\n")
            fix = console.input("  Fix this? (y/n): ").strip().lower()
            if fix == 'y':
                console.print("  [dim]Generating fix...[/dim]")
                suggested = generate_fix(
                    old_doc=v.doc_section,
                    reason=v.reason,
                    old_code=symbol.old_code,
                    new_code=symbol.new_code,
                    repo_path=repo_path
                )
                if suggested:
                    console.print(f"\n  [bold]Suggested:[/bold]")
                    console.print(f"  [green]{suggested}[/green]\n")
                    apply = console.input("  Apply? (y/n/e to edit): ").strip().lower()
                    if apply == 'y':
                        success = apply_fix(v.doc_file, v.doc_section, suggested)
                        if success:
                            console.print(f"  [bold green]Fixed[/bold green]\n")
                        else:
                            console.print(f"  [red]Could not apply — fix manually[/red]\n")
                    elif apply == 'e':
                        console.print(f"  [dim]Open {v.doc_file} line {v.doc_line} and edit manually[/dim]\n")

        for v, symbol in warnings:
            console.print(f"[bold yellow]WARNING[/bold yellow] [cyan]{v.symbol_name}[/cyan]")
            console.print(f"  {v.doc_file} line {v.doc_line}")
            console.print(f"  [yellow]{v.reason}[/yellow]\n")
            fix = console.input("  Fix this? (y/n): ").strip().lower()
            if fix == 'y':
                console.print("  [dim]Generating fix...[/dim]")
                suggested = generate_fix(
                    old_doc=v.doc_section,
                    reason=v.reason,
                    old_code=symbol.old_code,
                    new_code=symbol.new_code,
                    repo_path=repo_path
                )
                if suggested:
                    console.print(f"\n  [bold]Suggested:[/bold]")
                    console.print(f"  [green]{suggested}[/green]\n")
                    apply = console.input("  Apply? (y/n/e to edit): ").strip().lower()
                    if apply == 'y':
                        success = apply_fix(v.doc_file, v.doc_section, suggested)
                        if success:
                            console.print(f"  [bold green]Fixed[/bold green]\n")
                    elif apply == 'e':
                        console.print(f"  [dim]Open {v.doc_file} line {v.doc_line} and edit manually[/dim]\n")

        if undocumented:
            console.print(f"\n[bold yellow]{len(undocumented)} undocumented symbols found[/bold yellow]\n")
            for s in undocumented:
                console.print(f"[yellow]UNDOCUMENTED[/yellow] [cyan]{s.name}[/cyan] — [dim]{s.file_path}[/dim]")

            console.print()
            doc_all = console.input("[yellow]Auto-document all in README? (y/n): [/yellow]").strip().lower()

            if doc_all == 'y':
                readme_path = os.path.join(repo_path, 'README.md')
                additions = []

                for s in undocumented:
                    console.print(f"  [dim]Documenting {s.name}...[/dim]")
                    suggested = generate_fix(
                        old_doc='',
                        reason=f'New symbol {s.name} needs documentation',
                        old_code='',
                        new_code=s.new_code,
                        repo_path=repo_path
                    )
                    if suggested:
                        additions.append(f"\n## {s.name}\n\n{suggested}\n")
                        console.print(f"  [green]Generated docs for {s.name}[/green]")

                if additions:
                    with open(readme_path, 'a') as f:
                        f.write('\n' + '\n'.join(additions))
                    console.print(f"\n[bold green]Added {len(additions)} new sections to README[/bold green]\n")

    console.print()
    proceed = console.input("[bold]Commit now? (y/n): [/bold]").strip().lower()

    if proceed == 'y':
        if not message:
            message = console.input("[yellow]Commit message: [/yellow]").strip()
        if not message:
            console.print("[red]No message — aborting[/red]")
            return

        build_index(repo_path)
        subprocess.run(['git', 'add', '-A'])
        result = subprocess.run(['git', 'commit', '--no-verify', '-m', message])
        if result.returncode == 0:
            console.print("\n[bold green]Committed[/bold green]")
        else:
            console.print("\n[red]Commit failed[/red]")
    else:
        console.print("[dim]Cancelled[/dim]")


@cli.command()
@click.argument('repo_path', default='.')
@click.option('--no-llm', is_flag=True, help='Skip LLM check, show matches only')
def check(repo_path, no_llm):
    if not is_configured(repo_path):
        setup_config(repo_path)

    console.print("\n[bold green]DocDrift[/bold green] scanning...\n")

    if needs_reindex(repo_path):
        console.print("[dim]Docs changed — rebuilding index...[/dim]")
        count = build_index(repo_path)
        console.print(f"[dim]Indexed {count} chunks[/dim]\n")

    llm_available = is_lm_studio_running(repo_path)
    if not llm_available and not no_llm:
        console.print("[yellow]No AI model running — showing doc matches only[/yellow]")
        console.print("[dim]Set GROQ_API_KEY or start LM Studio for full analysis[/dim]\n")

    files = get_changed_files(repo_path)

    if not files:
        console.print("[yellow]No changed files found[/yellow]")
        console.print("[dim]Edit some code files and run check again[/dim]")
        return

    all_symbols = []
    for f in files:
        symbols = get_changed_symbols(f.path, f.old_content, f.new_content)
        all_symbols.extend(symbols)

    if not all_symbols:
        console.print("[yellow]No trackable symbols found in changed files[/yellow]")
        return

    console.print(f"[dim]Found {len(all_symbols)} changed symbol(s)[/dim]\n")

    errors = []
    warnings = []
    infos = []
    undocumented = []

    for symbol in all_symbols:
        matches = search_docs(repo_path, symbol.name)

        if not matches:
            undocumented.append(symbol)
            continue

        if not llm_available or no_llm:
            console.print(f"[bold yellow]DOC MATCH[/bold yellow] [cyan]{symbol.name}[/cyan] — [dim]{symbol.file_path}[/dim]")
            for match in matches:
                console.print(f"  [yellow]>[/yellow] {match['source_file']} line {match['start_line']} — {match['heading']}")
                console.print(f"    [dim]score: {match['distance']}[/dim]\n")
            continue

        console.print(f"[dim]Checking {symbol.name}...[/dim]")
        for match in matches:
            verdict = check_consistency(
                symbol_name=symbol.name,
                old_code=symbol.old_code,
                new_code=symbol.new_code,
                doc_content=match['content'],
                doc_file=match['source_file'],
                doc_line=match['start_line'],
                doc_heading=match['heading'],
                repo_path=repo_path
            )
            if verdict is None:
                continue
            if verdict.stale:
                if verdict.severity == 'error':
                    errors.append((verdict, symbol))
                elif verdict.severity == 'warning':
                    warnings.append((verdict, symbol))
                else:
                    infos.append((verdict, symbol))

    console.print()

    for v, symbol in errors:
        console.print(f"[bold red]ERROR[/bold red] [cyan]{v.symbol_name}[/cyan]")
        console.print(f"  {v.doc_file} line {v.doc_line} — section: [green]{v.doc_section}[/green]")
        console.print(f"  [red]{v.reason}[/red]\n")

        fix = console.input("  Want DocDrift to fix this? (y/n): ").strip().lower()
        if fix == 'y':
            console.print("  [dim]Generating fix...[/dim]")
            suggested = generate_fix(
                old_doc=v.doc_section,
                reason=v.reason,
                old_code=symbol.old_code,
                new_code=symbol.new_code,
                repo_path=repo_path
            )
            if not suggested:
                console.print("  [red]Could not generate fix[/red]")
                continue
            console.print(f"\n  [bold]Suggested fix:[/bold]")
            console.print(f"  [green]{suggested}[/green]\n")
            apply = console.input("  Apply this fix? (y/n/e to edit): ").strip().lower()
            if apply == 'y':
                success = apply_fix(v.doc_file, v.doc_section, suggested)
                if success:
                    console.print(f"  [bold green]Fixed — {v.doc_file} updated[/bold green]\n")
                else:
                    console.print(f"  [red]Could not apply automatically — update manually[/red]\n")
            elif apply == 'e':
                console.print(f"  [dim]Open {v.doc_file} line {v.doc_line} and edit manually[/dim]\n")
            else:
                console.print("  [dim]Skipped[/dim]\n")

    for v, symbol in warnings:
        console.print(f"[bold yellow]WARNING[/bold yellow] [cyan]{v.symbol_name}[/cyan]")
        console.print(f"  {v.doc_file} line {v.doc_line} — section: [green]{v.doc_section}[/green]")
        console.print(f"  [yellow]{v.reason}[/yellow]\n")

        fix = console.input("  Want DocDrift to fix this? (y/n): ").strip().lower()
        if fix == 'y':
            console.print("  [dim]Generating fix...[/dim]")
            suggested = generate_fix(
                old_doc=v.doc_section,
                reason=v.reason,
                old_code=symbol.old_code,
                new_code=symbol.new_code,
                repo_path=repo_path
            )
            if not suggested:
                console.print("  [red]Could not generate fix[/red]")
                continue
            console.print(f"\n  [bold]Suggested fix:[/bold]")
            console.print(f"  [green]{suggested}[/green]\n")
            apply = console.input("  Apply this fix? (y/n/e to edit): ").strip().lower()
            if apply == 'y':
                success = apply_fix(v.doc_file, v.doc_section, suggested)
                if success:
                    console.print(f"  [bold green]Fixed — {v.doc_file} updated[/bold green]\n")
            elif apply == 'e':
                console.print(f"  [dim]Open {v.doc_file} line {v.doc_line} and edit manually[/dim]\n")
            else:
                console.print("  [dim]Skipped[/dim]\n")

    for v, symbol in infos:
        console.print(f"[bold blue]INFO[/bold blue] [cyan]{v.symbol_name}[/cyan]")
        console.print(f"  {v.doc_file} line {v.doc_line} — section: [green]{v.doc_section}[/green]")
        console.print(f"  [blue]{v.reason}[/blue]\n")

    for s in undocumented:
        console.print(f"[bold red]UNDOCUMENTED[/bold red] [cyan]{s.name}[/cyan] — [dim]{s.file_path}[/dim]\n")

    total = len(errors) + len(warnings) + len(infos) + len(undocumented)
    if total == 0:
        console.print("[bold green]All documentation looks accurate[/bold green]")
    else:
        console.print(f"[bold]Found {len(errors)} errors · {len(warnings)} warnings · {len(infos)} info · {len(undocumented)} undocumented[/bold]")
        if errors or warnings:
            console.print("\n[dim]Run './docdrift commit' to fix and commit interactively[/dim]")


if __name__ == '__main__':
    cli()