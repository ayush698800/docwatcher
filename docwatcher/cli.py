from docwatcher.llm_checker import check_consistency, LLMVerdict
import click
from rich.console import Console
from rich.table import Table
from docwatcher.diff_parser import get_changed_files
from docwatcher.symbol_extractor import get_changed_symbols
from docwatcher.embeddings import build_index, search_docs

console = Console()

@click.group()
def cli():
    pass

@cli.command()
@click.argument('repo_path', default='.')
def index(repo_path):
    console.print("[bold green]DocWatcher[/bold green] building index...")
    count = build_index(repo_path)
    console.print(f"[green]Indexed {count} documentation chunks[/green]")

@cli.command()
@click.argument('repo_path', default='.')
def check(repo_path):
    console.print("\n[bold green]DocWatcher[/bold green] scanning...\n")

    files = get_changed_files(repo_path)

    if not files:
        console.print("[yellow]No changed files found[/yellow]")
        return

    all_symbols = []
    for f in files:
        symbols = get_changed_symbols(f.path, f.old_content, f.new_content)
        all_symbols.extend(symbols)

    if not all_symbols:
        console.print("[yellow]No trackable symbols found[/yellow]")
        return

    console.print(f"[dim]Found {len(all_symbols)} changed symbol(s) — running LLM checks...[/dim]\n")

    errors = []
    warnings = []
    infos = []
    undocumented = []

    for symbol in all_symbols:
        matches = search_docs(repo_path, symbol.name)

        if not matches:
            undocumented.append(symbol)
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
                doc_heading=match['heading']
            )

            if verdict is None:
                continue

            if verdict.stale:
                if verdict.severity == 'error':
                    errors.append(verdict)
                elif verdict.severity == 'warning':
                    warnings.append(verdict)
                else:
                    infos.append(verdict)

    console.print()

    for v in errors:
        console.print(f"[bold red]ERROR[/bold red] [cyan]{v.symbol_name}[/cyan]")
        console.print(f"  [white]{v.doc_file}[/white] line [white]{v.doc_line}[/white] — section: [green]{v.doc_section}[/green]")
        console.print(f"  [red]{v.reason}[/red]\n")

    for v in warnings:
        console.print(f"[bold yellow]WARNING[/bold yellow] [cyan]{v.symbol_name}[/cyan]")
        console.print(f"  [white]{v.doc_file}[/white] line [white]{v.doc_line}[/white] — section: [green]{v.doc_section}[/green]")
        console.print(f"  [yellow]{v.reason}[/yellow]\n")

    for v in infos:
        console.print(f"[bold blue]INFO[/bold blue] [cyan]{v.symbol_name}[/cyan]")
        console.print(f"  [white]{v.doc_file}[/white] line [white]{v.doc_line}[/white] — section: [green]{v.doc_section}[/green]")
        console.print(f"  [blue]{v.reason}[/blue]\n")

    for s in undocumented:
        console.print(f"[bold red]UNDOCUMENTED[/bold red] [cyan]{s.name}[/cyan] — [dim]{s.file_path}[/dim]\n")

    total_issues = len(errors) + len(warnings) + len(infos) + len(undocumented)

    if total_issues == 0:
        console.print("[bold green]All documentation looks accurate[/bold green]")
    else:
        console.print(f"[bold]Found {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info, {len(undocumented)} undocumented[/bold]")
if __name__ == '__main__':
    cli()