# DocDrift

> Finds stale documentation and fixes it automatically

You change a function. DocDrift finds every doc section that is now
lying because of that change — and fixes it with one keypress.

No more merging PRs with outdated documentation. No more new developers
wasting hours following instructions that stopped being true months ago.

---

## The problem

You change a function. You forget to update the docs.
Now your README is lying. A new developer follows it and wastes 3 hours.
This happens everywhere, all the time. Nobody has a good solution.

Until now.

---

## Demo
```
$ git add .
$ ./docdrift commit

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

  Apply? (y/n/e to edit): y
  Fixed

2 undocumented symbols found
Auto-document all in README? (y/n): y
  Generated docs for refresh_token
  Generated docs for AuthService
  Added 2 new sections to README

Commit now? (y/n): y
Commit message: refactor auth flow
Committed
```

---

## Install
```bash
git clone https://github.com/ayush698800/docwatcher.git
cd docwatcher
pip install -r requirements.txt
bash install-hook.sh
```

Set your free Groq API key for cloud AI:
```bash
export GROQ_API_KEY="your_key_here"
```

Get a free key at groq.com — takes 2 minutes.

Or use LM Studio or Ollama for fully local, private AI — no API key needed.

---

## Usage

### Smart commit — the main command
```bash
git add .
./docdrift commit
```

DocDrift will:
- Scan all changed functions and classes
- Find documentation that is now stale or wrong
- Show each finding with exact file and line number
- Ask if you want to fix it — AI generates the updated doc
- Auto-document any new undocumented functions
- Commit everything when you approve

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

Add `GROQ_API_KEY` to your repo secrets once.
Now every PR gets automatically checked for stale docs and posts findings as a comment.

---

## Pre-commit hook

DocDrift installs as a git hook that runs automatically before every commit:
```bash
bash install-hook.sh
```

Now every time you commit a Python or JS file, DocDrift checks automatically.
Blocks commits with ERROR-level stale docs.
Allows commits with warnings so you are never fully blocked.

Skip when needed:
```bash
git commit --no-verify -m "your message"
```

---

## How it works
```
git diff → changed functions and classes detected via Tree-sitter
       ↓
semantic search → finds related documentation sections
       ↓  
LLM check → is this doc still accurate after the code change?
       ↓
if stale → generates fix → asks permission → applies to file
       ↓
if undocumented → generates new docs → appends to README
```

---

## What it finds

- Functions that changed signature but docs describe the old one
- Functions that now raise exceptions but docs say they return values
- New parameters that are not mentioned anywhere in docs
- Completely undocumented new functions and classes
- Removed functionality still described as available

---

## Works with

- Python and JavaScript codebases
- Markdown and RST documentation
- README files, /docs folders, inline comments
- GitHub Actions for automatic team-wide PR checks
- LM Studio and Ollama — fully local and private
- Groq — free cloud AI, instant responses

---

## Built with

- Tree-sitter — code parsing across languages
- sentence-transformers — semantic documentation search
- ChromaDB — local vector index
- Groq / LM Studio / Ollama — LLM verdicts and fixes

---

## License

MIT