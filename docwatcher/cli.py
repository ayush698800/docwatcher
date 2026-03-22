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
    console.print("[bold green]DocWatcher[/bold green] starting...")
    console.print(f"Scanning repo at: [cyan]{repo_path}[/cyan]")

    files = get_changed_files(repo_path)

    if not files:
        console.print("[yellow]No changed files found[/yellow]")
        return

    all_symbols = []
    for f in files:
        symbols = get_changed_symbols(f.path, f.old_content, f.new_content)
        all_symbols.extend(symbols)

    if not all_symbols:
        console.print(f"[yellow]Found {len(files)} changed file(s) but no trackable symbols[/yellow]")
        return

    console.print(f"[green]Found {len(all_symbols)} changed symbol(s) — searching docs...[/green]\n")

    for symbol in all_symbols:
        matches = search_docs(repo_path, symbol.name)
        
        if matches:
            console.print(f"[bold cyan]{symbol.name}[/bold cyan] ([magenta]{symbol.symbol_type}[/magenta]) in [green]{symbol.file_path}[/green]")
            for match in matches:
                console.print(f"  [yellow]Doc match:[/yellow] {match['source_file']} line {match['start_line']}")
                console.print(f"  [dim]Section: {match['heading']}[/dim]")
                console.print(f"  [dim]{match['content'][:120]}...[/dim]\n")

if __name__ == '__main__':
    cli()