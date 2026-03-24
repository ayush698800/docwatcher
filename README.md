# DocDrift

DocDrift keeps code and docs in sync before you commit.

It scans your staged git diff, finds the functions and classes you changed, looks up the related documentation, and flags docs that are now wrong, incomplete, or missing.

## Why it exists

Most documentation does not fail loudly. It just drifts.

You rename a parameter, change a return value, or start raising a new exception. The code is correct, but the README still teaches the old behavior. DocDrift catches that gap before it ships.

## What it does

- Detects changed functions and classes from staged git diffs
- Finds related Markdown and RST docs with semantic search
- Uses AI to check whether the docs still match the code
- Suggests updated documentation and applies fixes interactively
- Flags undocumented new symbols
- Runs locally in the CLI and in GitHub Actions with the same analysis path

## Demo

```bash
git add .
python -m pip install -e .
docdrift commit
```

Example flow:

```text
DocDrift scanning before commit...

+-----------------------------------------------+
| DocDrift Commit                               |
| 2 staged file(s)  3 changed symbol(s)  ready  |
+-----------------------------------------------+

Found 1 errors · 1 warnings · 1 undocumented

+-----------------------------------------------+
| ERROR                                         |
| validate_token in auth/service.py             |
| Docs: README.md:42 (Authentication)           |
| Docs still promise True/False, but the code   |
| now raises InvalidTokenError on failure.      |
+-----------------------------------------------+

  Fix this? (y/n): y
  Generating fix...

+-----------------------------------------------+
| Suggested Fix                                 |
| validate_token validates a token and raises   |
| InvalidTokenError when the token is rejected. |
+-----------------------------------------------+

  Apply? (y/n/e to edit): y
  Fixed
```

## Installation

Install from source:

```bash
python -m pip install -e .
```

Or run directly from this checkout:

```bash
./docdrift commit
```

## Configuration

DocDrift works with:

- Groq via `GROQ_API_KEY`
- LM Studio compatible OpenAI-style endpoints
- Ollama compatible OpenAI-style endpoints

On first run, `docdrift commit` will prompt for a local endpoint if no config exists. The config is saved to `.docdrift/config.json`.

## CLI

Check staged changes without committing:

```bash
docdrift check
```

Run the interactive commit flow:

```bash
docdrift commit
```

Rebuild the documentation index:

```bash
docdrift index
```

## GitHub Actions

Add this workflow:

```yaml
name: DocDrift

on:
  pull_request:
    branches: [main, master]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: ./
        with:
          groq_api_key: ${{ secrets.GROQ_API_KEY }}
```

The GitHub Action uses the same analysis engine as the CLI, so local checks and PR comments stay aligned.

## Pre-commit hook

Install the built-in git hook:

```bash
bash install-hook.sh
```

Or use the included `.pre-commit-config.yaml`.

## Project layout

```text
docwatcher/
├── docwatcher/
│   ├── cli.py
│   ├── engine.py
│   ├── diff_parser.py
│   ├── symbol_extractor.py
│   ├── doc_scanner.py
│   ├── embeddings.py
│   ├── llm_checker.py
│   ├── fixer.py
│   └── config.py
├── .github/workflows/docdrift.yml
├── action.yml
├── README.md
├── setup.py
└── tests/
```

## Development

Run the package from source:

```bash
python -m docwatcher.cli check
```

Run tests:

```bash
python -m unittest discover -s tests
```

## License

[MIT](LICENSE)
