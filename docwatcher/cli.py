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
        console.print("[yellow]No trackable symbols found in changed files[/yellow]")
        return

    console.print(f"[dim]Found {len(all_symbols)} changed symbol(s)[/dim]\n")

    found_any_match = False

    for symbol in all_symbols:
        matches = search_docs(repo_path, symbol.name)

        if not matches:
            continue

        found_any_match = True
        console.print(f"[bold cyan]{symbol.name}[/bold cyan] ([magenta]{symbol.symbol_type}[/magenta]) — [dim]{symbol.file_path}[/dim]")

        for match in matches:
            console.print(f"  [yellow]>[/yellow] [white]{match['source_file']}[/white] line [white]{match['start_line']}[/white] — section: [green]{match['heading']}[/green]")
            console.print(f"    [dim]{match['content'][:100]}...[/dim]")
            console.print(f"    [dim]relevance score: {match['distance']}[/dim]\n")

    if not found_any_match:
        console.print("[green]No documentation matches found for changed symbols[/green]")
        console.print("[dim]Either no docs reference these symbols or index needs rebuilding[/dim]")
if __name__ == '__main__':
    cli()