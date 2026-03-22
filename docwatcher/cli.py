import click
from rich.console import Console
from docwatcher.diff_parser import get_changed_files

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
    else:
        console.print(f"[green]Found {len(files)} changed file(s):[/green]")
        for f in files:
            console.print(f"  [cyan]{f.path}[/cyan]")

if __name__ == '__main__':
    cli()