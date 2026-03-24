## 🚀 DocDrift

⚡ **Your docs should never lie again.**

DocDrift finds stale documentation in your codebase before you commit — and fixes it automatically using AI.

No more outdated READMEs. No more confused developers. No more wasting hours debugging wrong documentation.

---

## 😤 The Problem

You change a function. You forget to update the docs.
Now your README is lying.

A new developer follows it → wastes 3 hours → blames the project.

This happens everywhere. And nobody really fixes it.

---

## 💡 The Solution

DocDrift hooks into your workflow and fixes documentation drift instantly.

- Detects changed functions/classes
- Finds related documentation
- Checks if it's still correct
- Fixes it using AI
- Updates everything before commit

All in one command.

![ScreenRecording2026-03-23213053-ezgif com-video-to-gif-converter](https://github.com/user-attachments/assets/33c37392-68d9-4f68-9cbe-ac914f14f78f)
---

## ⚡ Demo
```bash
$ git add .
$ docdrift commit
```
```
DocDrift scanning before commit...

Found 1 errors · 0 warnings · 2 undocumented

ERROR validate_token
  README.md line 7
  Function now raises NotImplementedError but docs say it returns True/False

  Fix this? (y/n): y
  Generating fix...

  Suggested:
  The validate_token function validates a token and scope.
  Raises NotImplementedError if validation has been removed.
  Use AuthService.login() instead.

  Apply? (y/n/e): y
  ✔ Fixed

2 undocumented symbols found
Auto-document all in README? (y/n): y
  ✔ Generated docs for refresh_token
  ✔ Generated docs for AuthService
  Added 2 new sections to README

Commit now? (y/n): y
Commit message: refactor auth flow
✔ Committed
```
![ScreenRecording2026-03-23213400-ezgif com-video-to-gif-converter](https://github.com/user-attachments/assets/fbc671bb-debe-4fdc-8f67-eea5515af4e7)

---

## 🛠� Installation
```bash
pip install docdrift
```

That is it. No cloning. No setup.

---

## 🔑 Set API Key — Optional, Cloud AI
```bash
export GROQ_API_KEY="your_key_here"
```

👉 Get a free key at https://groq.com — takes 2 minutes.

**OR** run fully locally — no API key needed:

- LM Studio
- Ollama

🔒 Your code never leaves your machine.

---

## 🚀 Usage

### Smart Commit — main command
DocDrift will:
- Scan all changed files
- Find documentation that is now stale or wrong
- Show each finding with exact file and line number
- Ask if you want to fix it — AI generates the fix
- Auto-document any new undocumented functions
- Commit everything when you approve

Why it is stale:
The documentation mentions 'changed functions and classes', but the code now also checks for 'changed files' which may contain non-code changes.

### Check Only
```bash
docdrift check
```

### Rebuild Index
```bash
docdrift index
```

---

## 🤖 GitHub Actions — Auto PR Checks

Add `.github/workflows/docdrift.yml` to any repo:
```yaml
name: DocDrift
on:
  pull_request:
    branches: [main, master]
  workflow_dispatch:

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 2

      - name: DocDrift
        uses: ayush698800/docwatcher@v2.0.0
        with:
          groq_api_key: ${{ secrets.GROQ_API_KEY }}
```

Add `GROQ_API_KEY` to your repo secrets once.
Now every PR gets automatically checked and findings posted as comments. 🔥

---

## 🔗 Pre-Commit Hook
```bash
pip install docdrift
docdrift-install-hook
```

Or manually:
```bash
bash install-hook.sh
```

- � Blocks commits with critical doc errors
- ⚠� Allows warnings — no workflow disruption

Skip when needed:
```bash
git commit --no-verify -m "message"
```

---

## ⚙� How It Works
```
git diff
   ↓
Detect changed functions via Tree-sitter
   ↓
Find related docs via semantic search
   ↓
AI checks if docs are still accurate
   ↓
Generate fix → ask permission → apply
   ↓
Auto-document undocumented symbols
   ↓
Commit everything
```

---

## 🧠 What It Detects

- Changed function signatures with outdated docs
- Incorrect return values or exceptions described wrong
- Missing parameters not mentioned in documentation
- Completely undocumented new functions and classes
- Removed features still described as available

---

## � Supported Stack

- Python and JavaScript codebases
- Markdown and RST documentation
- README files, /docs folders, inline comments
- GitHub Actions for automatic team-wide PR checks
- LM Studio and Ollama — fully local and private
- Groq — free cloud AI, instant responses

---

## �� Built With

- Tree-sitter — code parsing across languages
- sentence-transformers — semantic documentation search
- ChromaDB — local vector index
- Groq / LM Studio / Ollama — LLM verdicts and fixes

---

## 📜 License

MIT

---

## � Why This Matters

Bad documentation kills good projects.

DocDrift makes sure your documentation stays as reliable as your code.

---

## 🙌 Contribute

PRs, ideas, and feedback are welcome.
Let's make documentation actually trustworthy.

---

## � Star This Repo

If this saved you even one hour — give it a star �

[![PyPI version](https://badge.fury.io/py/docdrift.svg)](https://badge.fury.io/py/docdrift)


## _print_commit_banner

### `_print_commit_banner`

Prints a commit banner to the console, displaying the number of staged files, changed symbols, and AI availability.

#### Parameters

* `files`: A list of staged files
* `symbols`: A list of changed symbols
* `llm_available`: A boolean indicating whether the Large Language Model is available

#### Returns

None

#### Example

```python
_print_commit_banner(files=["file1", "file2"], symbols=["symbol1", "symbol2"], llm_available=True)
```


## _print_finding

### _print_finding Function

Prints a finding to the console.

#### Parameters

* `verdict`: The verdict object containing information about the finding.
* `symbol`: The symbol object associated with the finding.
* `level`: The level of the finding, which can be "error", "warning", or "info".

#### Description

This function formats and prints a finding to the console, including the symbol name, file path, documentation details, and reason for the finding. The output is displayed in a panel with a colored border and title based on the finding level.

#### Example

```python
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
```


## _print_fix_preview

The `_print_fix_preview` function prints a suggested fix preview to the console. It takes a string `suggested` as input, which represents the suggested fix to be displayed. The function uses the `console.print` method to render the suggested fix in a green bordered panel.

```python
def _print_fix_preview(suggested: str):
    console.print(Panel(suggested, title="Suggested Fix", border_style="green"))
```


## _collect_findings

**_collect_findings Function**

This function collects findings from the documentation of a repository. It takes three parameters:

* `repo_path`: the path to the repository
* `symbols`: a list of symbols to check
* `llm_available`: a boolean indicating whether a Large Language Model (LLM) is available for use

The function returns four lists:

* `errors`: a list of tuples containing the verdict and the symbol that caused the error
* `warnings`: a list of tuples containing the verdict and the symbol that caused the warning
* `infos`: a list of tuples containing the verdict, symbol, and matches for informational messages
* `undocumented`: a list of symbols that were not found in the documentation

The function iterates over the symbols, checks if they have any matches in the documentation, and then uses the LLM to check the consistency of the documentation. If the LLM is not available, it falls back to a simpler check. The function returns the findings in the four lists.


## precommit

**precommit Function**
=====================

The `precommit` function is a new addition to the DocDrift toolset. It is designed to run as a pre-commit hook to check for stale documentation in the repository.

**Function Signature**
--------------------

```python
def precommit(repo_path: str) -> None
```

**Function Description**
------------------------

The `precommit` function takes a `repo_path` parameter, which is the path to the repository to be checked. It performs the following steps:

1. Checks if the repository needs to be reindexed. If so, it builds the index.
2. Retrieves the list of changed files in the repository.
3. If no changed files are found, it exits with a status code of 0.
4. Iterates over the changed files, collecting all changed symbols.
5. If no changed symbols are found, it exits with a status code of 0.
6. Checks if the Large Model (LLM) is available. If so, it collects findings about the changed symbols.
7. If errors are found, it prints an error message and exits with a status code of 1.
8. If warnings or undocumented symbols are found, it prints a warning message and exits with a status code of 0.
9. If no issues are found, it prints a success message and exits with a status code of 0.

**Example Usage**
-----------------

To use the `precommit` function, simply call


## check

New symbol check
===============

The new symbol check is performed after the index has been rebuilt and the AI model is available. It scans the changed files for new symbols and checks if they are documented.

If new symbols are found, the check will print a list of the new symbols, along with their file paths, and the matches found by the AI model. If the AI model is not available, the check will only print the new symbols and their file paths.

If the new symbol check finds any undocumented symbols, it will print a list of the undocumented symbols, along with their file paths.

The new symbol check will only be performed if the `no_llm` flag is not set.

```python
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
    console.print("[yellow]No trackable symbols found in changed files


## _db_path

### db_path Function

Returns the absolute path to the database directory within the given repository path.

#### Parameters

* `repo_path`: The absolute path to the repository.

#### Returns

The absolute path to the database directory.

#### Example

```python
db_path = db_path(repo_path="/path/to/repo")
print(db_path)  # Output: /path/to/repo/_db
```


## get_client

### get_client

Retrieves a persistent client instance for the specified repository path.

#### Parameters

* `repo_path`: The path to the repository.

#### Returns

A `chromadb.PersistentClient` instance, initialized with the specified repository path.


## _marker_path

### marker_path Function

```python
def marker_path(repo_path: str) -> str:
    """
    Returns the path to the marker file for the given repository path.

    Args:
        repo_path: The path to the repository.

    Returns:
        The path to the marker file.
    """
    return os.path.join(_db_path(repo_path), MARKER_FILE)
```


## get_index_age

```python
def get_index_age(repo_path: str) -> float:
    """
    Returns the age of the index in the repository at the given path.

    The age is calculated as the time since the last modification of the index marker file.
    If the index marker file does not exist, returns infinity.

    Args:
        repo_path (str): The path to the repository.

    Returns:
        float: The age of the index in seconds since the epoch.
    """
    marker = _marker_path(repo_path)
    return os.path.getmtime(marker) if os.path.exists(marker) else float('inf')
```


## get_docs_age

### get_docs_age Function

Returns the age of the most recently modified documentation file in the specified repository.

```python
def get_docs_age(repo_path: str) -> float:
    """
    Returns the age of the most recently modified documentation file in the specified repository.

    Args:
        repo_path (str): The path to the repository.

    Returns:
        float: The age of the most recently modified documentation file in seconds since the epoch.
    """
    newest = 0.0
    skip = {'venv', '.git', '__pycache__', '.docwatcher'}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if f.endswith(('.md', '.rst', '.mdx')):
                path = os.path.join(root, f)
                newest = max(newest, os.path.getmtime(path))
    return newest
```


## needs_reindex

needs_reindex(repo_path: str) -> bool:
    """Return True if any documentation file is newer than the last index build."""
    return get_docs_age(repo_path) > get_index_age(repo_path)


## _touch_marker

### touch_marker Function

Creates a touch marker file at the specified repository path.

```python
touch_marker(repo_path: str):
    os.makedirs(_db_path(repo_path), exist_ok=True)
    with open(_marker_path(repo_path), 'w') as f:
        f.write('indexed')
```

#### Parameters

* `repo_path` (str): The path to the repository.

#### Description

This function initializes the database directory and creates a touch marker file at the specified repository path. The touch marker file is used to indicate that the repository has been indexed.


## build_index

```python
build_index(repo_path: str) -> int:
    """
    (Re)build the ChromaDB index from all .md / .rst / .mdx files.
    
    Args:
        repo_path (str): The path to the repository to index.
    
    Returns:
        int: The number of chunks indexed.
    """
```


## LLMVerdict

## LLMVerdict Class

The `LLMVerdict` class represents a verdict returned by the Large Language Model (LLM). It contains information about the verdict, including its staleness, severity, reason, and associated documentation.

### Attributes

- `stale`: A boolean indicating whether the verdict is stale.
- `severity`: A string representing the severity of the verdict.
- `reason`: A string describing the reason for the verdict.
- `symbol_name`: A string representing the name of the symbol associated with the verdict.
- `doc_heading`: A string representing the heading of the associated documentation.
- `doc_content`: A string containing the content of the associated documentation.
- `doc_file`: A string representing the file path of the associated documentation.
- `doc_line`: An integer representing the line number of the associated documentation.


## check_consistency

```python
def check_consistency(
    symbol_name: str,
    old_code: str,
    new_code: str,
    doc_content: str,
    doc_file: str,
    doc_line: int,
    doc_heading: str,
    repo_path: str = '.'
) -> Optional[LLMVerdict]:
    """
    Checks the consistency of the documentation for a given symbol after a code change.

    Args:
        symbol_name (str): The name of the symbol.
        old_code (str): The original code.
        new_code (str): The updated code.
        doc_content (str): The content of the documentation section.
        doc_file (str): The file path of the documentation.
        doc_line (int): The line number of the documentation.
        doc_heading (str): The heading of the documentation section.
        repo_path (str, optional): The path to the repository. Defaults to '.'.

    Returns:
        Optional[LLMVerdict]: The verdict on the consistency of the documentation.
    """
```


## GitHubAPI

```python
class GitHubAPI:
    """
    Thin wrapper around the GitHub REST Search API.
    """

    def __init__(self, token: str = ""):
        """
        Initializes the GitHub API wrapper.

        :param token: GitHub API token (optional)
        """
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

        :param count: Number of top repos to fetch (default: TARGET_REPOS)
        :return: List of top Python repos
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
                            "page


## __init__

```python
def __init__(self, token: str = ""):
    """
    Initializes the session with the provided GitHub token.

    Args:
        token (str, optional): The GitHub token to authenticate the session. Defaults to an empty string.
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    self.session = req.Session()
    self.session.headers.update(headers)
```


## get_top_repos

```python
os(self, count: int = TARGET_REPOS) -> list:
    """
    Fetch the top `count` Python repos by star count.
    Filters out curated list repos ("awesome", "list").
    Paginates with a polite 2-second delay between pages.

    Args:
        count (int, optional): The number of top Python repos to fetch. Defaults to TARGET_REPOS.

    Returns:
        list: A list of dictionaries containing information about the top Python repos.
              Each dictionary contains the keys "full_name", "stars", and "url".
    """
```


## _print_sniper_result

```python
def _print_sniper_result(result: dict):
    """
    Pretty-print the result of a single-repo sniper audit.

    :param result: A dictionary containing the audit result.
    """
    console.print()

    if result["status"] == "clone_failed":
        console.print(Panel("[red]âŒ Failed to clone repository.[/red]", title="Result"))
        return

    if result["status"] == "no_activity":
        console.print(Panel(
            "[yellow]ðŸ˜´ No code changes detected in the lookback window.\n"
            "This repo appears dormant.[/yellow]",
            title="Result"
        ))
        return

    if result["status"] == "index_failed":
        console.print(Panel("[red]âŒ Documentation index build failed.[/red]", title="Result"))
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


## _print_wall_of_shame

## _print_wall_of_shame Function

Prints the mass-scan leaderboard table, showcasing the top 15 most drifted repositories.

```python
console.rule("[bold red]ðŸ† WALL OF SHAME â€” Top 15 Most Drifted Repos[/bold red]")
table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE_HEAVY)
table.add_column("Repository",  style="cyan")
table.add_column("â­ Stars",    justify="right", style="dim")
table.add_column("ðŸ”´ Errors",  justify="right", style="red")
table.add_column("âš ï¸  Warnings", justify="right", style="yellow")
table.add_column("ðŸ“­ Undoc",   justify="right", style="blue")
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
```


## main

```python
ocDrift â€” Find documentation drift in Python/JS repositories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scanner.py                          # Mass scan top 100 GitHub repos
  python scanner.py --url https://github.com/psf/requests   # Sniper mode
  python scanner.py --local /path/to/project  # Local repo scan
  python scanner.py --local .                 # Current directory
  python scanner.py --resume                  # Resume from previous run
        """
```
