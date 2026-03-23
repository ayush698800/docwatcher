# DocDrift

> Detects stale documentation by watching your git diffs

When you change a function, DocDrift finds every doc section
that talks about it and asks an AI — is this still accurate?

No more merging PRs with lying documentation.

## The problem

You change a function. You forget to update the docs.
Now your README is lying. A new developer follows it and
wastes 3 hours. This happens everywhere, all the time.

DocWatcher catches it automatically before you merge.

## What you get on every PR
```
## DocWatcher — Documentation Check

### ERROR — validate_token

Raises a `NotImplementedError` if token validation has been removed. Use `AuthService.login()` instead.

The `old_display` variable is used to display the old code in a user-friendly format. If the old code is empty, it defaults to "New function � did not exist before".

Raises a `NotImplementedError` if token validation has been removed. Use `AuthService.login()` instead.

This function does not exist in the provided code. The actual function is named `check_consistency`.

This function is not used in the code.

This function raises a NotImplementedError when called. It has been removed in favor of using AuthService.login().
File: README.md line 10
Section: validate_token
Issue: Function now requires scope parameter but docs don't mention it

Found 1 errors · 0 warnings · 0 undocumented
```

## GitHub Actions setup

Add this file to your repo at `.github/workflows/docwatcher.yml`:
```yaml
name: DocWatcher
on:
  pull_request:
    branches: [main, master]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 2

      - uses: ayush698800/docwatcher@main
        with:
          groq_api_key: ${{ secrets.GROQ_API_KEY }}
```

Then add your Groq API key to your repo secrets as `GROQ_API_KEY`.
Get a free key at groq.com — takes 2 minutes.

## Local usage
```bash
git clone https://github.com/ayush698800/docwatcher.git
cd docwatcher
pip install -r requirements.txt
python -m docwatcher.cli check
```

First run asks for your local AI endpoint once and remembers it.
Works with LM Studio and Ollama.

## How it works

1. Watches git diff for changed functions and classes
2. Finds related documentation using semantic search
3. Asks an AI — is this doc still accurate?
4. Reports stale docs with severity and exact reason

## Supports

- Python and JavaScript files
- Markdown and RST documentation
- README files, /docs folders, inline docstrings
- GitHub Actions for automatic PR checks
- Local AI via LM Studio or Ollama
- Cloud AI via Groq — free tier is enough

## Requirements

For GitHub Actions — free Groq API key from groq.com

For local use — LM Studio or Ollama running on your machine

## Built with

- Tree-sitter for code parsing
- sentence-transformers for semantic search
- ChromaDB for the doc index
- Groq / LM Studio / Ollama for LLM verdicts

## License

MIT

## precommit

@cli.command()
@click.argument('repo_path')
def precommit(repo_path):
    """
    Runs a pre-commit check for the DocDrift tool.

    This function checks for stale documentation in the repository at the given path.
    It searches for changed symbols, checks their documentation, and reports any errors or warnings.

    If any stale documentation is found, the function will block the commit and provide options to fix the issues.
    """
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
                doc_content=match['content


## index

### Building the Symbol Index

The `build_index` function is used to create a symbol index for the documentation. This process is triggered when the `[bold green]DocDrift[/bold green]` command is executed. The function takes the repository path as an argument and returns the count of indexed documentation chunks.

```python
"[bold green]DocDrift[/bold green] building index...")
    count = build_index(repo_path)
    console.print(f"[green]Indexed {count} documentation chunks[/green]")
```

This process is initiated through the `cli` command, which is decorated with the `@click.command()` decorator. The `messa` argument is not used in this context and is likely a typo.


## commit

```python
rt subprocess

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
        symbols = get_changed_symbols(f.path, f.old_content, f.new_code)  # Changed from f.new_content to f.new_code
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
                new_code=symbol.new_code,  # Changed from symbol.new_content to symbol.new_code
                doc_content=match['content'],
                doc_file=match['source_file'],
                doc_line=match['start_line'],
                doc_heading=match['heading'],
                repo_path=repo_path
            )


## check

```python
# Check for new symbols
if not all_symbols:
    console.print("[yellow]No trackable symbols found in changed files[/yellow]")
    return

console.print(f"[dim]Found {len(all_symbols)} changed symbol(s)[/dim]\n")

# New symbol check
new_symbols = []
for symbol in all_symbols:
    if not symbol.name in [s.name for s in all_symbols if s.name != symbol.name]:
        new_symbols.append(symbol)

if new_symbols:
    console.print("[bold yellow]NEW SYMBOL[/bold yellow]")
    for symbol in new_symbols:
        console.print(f"  [cyan]{symbol.name}[/cyan] — [dim]{symbol.file_path}[/dim]")
    console.print()
```


## should_skip

### should_skip Function

Determines whether a given path should be skipped based on the configured `SKIP_PATTERNS`.

#### Parameters

* `path`: The path to check (str)

#### Returns

* A boolean indicating whether the path should be skipped (bool)


## generate_fix

### generate_fix Function

The `generate_fix` function generates an updated documentation string based on the provided old documentation, reason for staleness, old code, and new code.

#### Parameters

* `old_doc`: The original documentation string.
* `reason`: The reason why the documentation is stale.
* `old_code`: The original code snippet.
* `new_code`: The updated code snippet.
* `repo_path`: The path to the repository (default: current directory).

#### Returns

An updated documentation string if successful, otherwise `None`.

#### Example Usage

```python
new_doc = generate_fix(
    old_doc="Original documentation",
    reason="Reason for staleness",
    old_code="Original code",
    new_code="Updated code"
)
print(new_doc)
```


## apply_fix

### apply_fix Function

Applies a text replacement to a specified file.

```python
def apply_fix(file_path: str, old_text: str, new_text: str) -> bool:
```

#### Parameters

* `file_path`: The path to the file to be updated.
* `old_text`: The text to be replaced.
* `new_text`: The replacement text.

#### Returns

* `True` if the replacement was successful, `False` otherwise.


## check_with_groq

## check_with_groq Function

The `check_with_groq` function sends a list of messages to the Groq API for completion using a specified model.

### Parameters

* `messages`: A list of messages to be completed.
* `model`: The Groq model to use for completion (default: "llama-3.1-8b-instant").

### Returns

* The completed message content as a string, or `None` if the API key is invalid or an error occurs.
