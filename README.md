
# DocDrift

Catch stale docs before they reach `main`.

DocDrift checks the code you changed against your README, docs, and examples, then flags documentation that is now wrong, incomplete, or missing.

## Why DocDrift

Documentation usually does not break loudly. It just drifts.

You rename a parameter, change a return value, remove a feature, or start raising a new exception. The code is correct, but the docs still teach the old behavior.

DocDrift catches that gap before you commit or merge.

![Animation](https://github.com/user-attachments/assets/d45152c2-d7ec-4f13-99fd-0917a949454d)

## What It Does

- Detects changed functions and classes from staged git diffs
- Finds related Markdown and RST docs with semantic search
- Uses AI to check whether the docs still match the code
- Suggests updated documentation and applies fixes interactively
- Flags undocumented new symbols
- Runs locally in the CLI and in GitHub Actions

## Install

```bash
pip install docdrift
```

## Quick Start

From inside your git repository:

```bash
git add .
docdrift commit
```

That will:
- scan your staged code changes
- find related docs
- flag stale or missing documentation
- offer fixes interactively
- let you commit after review


## AI Setup

For full documentation checks and autofixes, DocDrift needs an AI backend.

You have 2 options:

### Option 1: Groq

This is the easiest setup.

Set your API key:

```bash
export GROQ_API_KEY="your_key_here"
```

Then run:

```bash
git add .
docdrift commit
```

### Option 2: Local / Private AI

If you do not want to use a cloud API, you can use a local OpenAI-compatible endpoint such as:

- LM Studio
- Ollama-compatible OpenAI endpoint

On first run, DocDrift will ask for your endpoint and save it to:

```text
.docdrift/config.json
```

Common endpoints:

- LM Studio: `http://localhost:1234/v1/chat/completions`
- Ollama-compatible endpoint: `http://localhost:11434/v1/chat/completions`

## What Happens Without AI?

If you do not set `GROQ_API_KEY` and do not configure a local endpoint, DocDrift cannot run full AI consistency checks or generate fixes.

To get the real stale-doc detection and autofix workflow, you need one of:
- `GROQ_API_KEY`
- a local AI endpoint

## Example

```bash
git add .
docdrift commit
```

```text
DocDrift scanning before commit...

Found 1 errors · 0 warnings · 1 undocumented

ERROR validate_token
Docs: README.md:42
Docs still say the function returns bool,
but the code now raises InvalidTokenError.

Fix this? (y/n): y
Generating fix...
README.md updated

Commit now? (y/n): y
Committed
```

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

Run the pre-commit safety check manually:

```bash
docdrift precommit
```

## GitHub Actions

Add this workflow to your repo:

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

      - uses: ayush698800/docwatcher@v2.1.0
        with:
          groq_api_key: ${{ secrets.GROQ_API_KEY }}
```

This runs the same core detection logic in PRs that you use locally in the CLI.

## Pre-commit Hook

Install the built-in git hook:

```bash
bash install-hook.sh
```

After that, DocDrift will run automatically before each commit.

You can also use the included `.pre-commit-config.yaml` if you prefer `pre-commit`.

## When To Use It

DocDrift is most useful if your repo has:

- a README with code examples
- `/docs` content tied to implementation
- public APIs or SDK usage docs
- fast-moving code where docs often drift
- pull requests where reviewers care about docs accuracy

## Project Layout

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

## Troubleshooting

### `docdrift: command not found`

Try:

```bash
python -m docwatcher.cli commit
```

If that works, the package is installed but the CLI executable is not on your shell `PATH`.

### No AI checks are happening

Make sure you have either:
- `GROQ_API_KEY` set, or
- a local endpoint configured in `.docdrift/config.json`

### No changed files found

DocDrift checks staged changes, so stage your files first:

```bash
git add .
```

Then run:

```bash
docdrift commit
```

## Development

If you are working from a cloned source checkout, install in editable mode:

```bash
python -m pip install -e .
```

Run from source:

```bash
python -m docwatcher.cli check
```

Run tests:

```bash
python -m unittest discover -s tests
```

## License

[MIT](LICENSE)

