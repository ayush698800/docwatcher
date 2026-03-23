# DocDrift

> Finds stale documentation and fixes it automatically

You change a function. DocDrift finds every doc section that is now
lying because of that change — and fixes it with one keypress.

No more merging PRs with outdated documentation.

---

## What it does
```
You change validate_token() to require MFA
       ↓
DocDrift detects the change
       ↓
Finds README section describing the old behavior
       ↓
ERROR: docs say "returns True/False" but function now raises exception
       ↓
Want DocDrift to fix this? (y/n): y
       ↓
README updated automatically
```

---

## Install
```bash
git clone https://github.com/ayush698800/docwatcher.git
cd docwatcher
pip install -r requirements.txt
bash install-hook.sh
```

Get a free Groq API key at groq.com and set it:
```bash
export GROQ_API_KEY="your_key_here"
```

---

## Usage

### Smart commit — the main command
```bash
git add .
./docdrift commit
```

This will:
- Scan all changed functions and classes
- Find documentation that is now stale
- Ask if you want to fix each one — AI generates the fix
- Auto-document any undocumented new functions
- Commit everything when you are ready

### Check only — no commit
```bash
./docdrift check
```

### Rebuild doc index
```bash
./docdrift index
```

---

## GitHub Actions — automatic PR checks

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

Add `GROQ_API_KEY` to your repo secrets. Done.
Every PR now gets automatically checked for stale docs.

---

## How it works

1. Watches git diff for changed functions and classes using Tree-sitter
2. Finds related documentation using semantic AI search
3. Sends code change and doc section to LLM — is this still accurate?
4. If stale — generates a fix and asks permission to apply it
5. Auto-documents new functions that have no documentation yet

---

## Works with

- Python and JavaScript codebases
- Markdown and RST documentation
- LM Studio and Ollama for local AI — fully private
- Groq for cloud AI — free tier is enough
- GitHub Actions for automatic team-wide PR checks

---

## Built with

- Tree-sitter — code parsing across languages
- sentence-transformers — semantic doc search
- ChromaDB — local doc index
- Groq / LM Studio / Ollama — LLM verdicts and fixes

---

## License

MIT