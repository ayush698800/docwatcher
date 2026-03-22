# DocWatcher

> Detects stale documentation by watching your git diffs

When you change a function, DocWatcher finds every doc section
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