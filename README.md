# DocWatcher

> Detects stale documentation by watching your git diffs

When you change a function, DocWatcher finds every doc section 
that talks about it and asks an AI — is this still accurate?

## How it works

1. Watches git diff for changed functions and classes
2. Finds related documentation using semantic search  
3. Asks an AI — is this doc still accurate?
4. Posts results directly on your Pull Request

## Usage

Add this to `.github/workflows/docwatcher.yml` in your repo:
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
Get a free key at groq.com.

## What you get on every PR
```
## DocWatcher — Documentation Check

### ERROR — validate_token
File: README.md line 10
Section: validate_token
Issue: Function now requires scope parameter but docs don't mention it

Found 1 errors, 0 warnings, 0 undocumented
```

## Local usage
```bash
pip install docwatcher
docwatcher check
```

Works with LM Studio and Ollama. First run asks for your endpoint once.

## Requirements

- For GitHub Actions: free Groq API key
- For local use: LM Studio or Ollama