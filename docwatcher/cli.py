import click
from rich.console import Console
from rich.table import Table
from docwatcher.diff_parser import get_changed_files
from docwatcher.symbol_extractor import get_changed_symbols

console = Console()

@click.group()
def cli():
    pass

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
        for f in files:
            console.print(f"  [cyan]{f.path}[/cyan]")
        return

    table = Table(title="Changed Symbols")
    table.add_column("Symbol", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("File", style="green")
    table.add_column("Status", style="yellow")

    for s in all_symbols:
        status = "modified" if s.old_code else "new"
        table.add_row(s.name, s.symbol_type, s.file_path, status)

    console.print(table)
    console.print(f"\n[bold]Total changed symbols: {len(all_symbols)}[/bold]")

if __name__ == '__main__':
    cli()