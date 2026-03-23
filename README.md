# 🚀 DocDrift

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

---

## 🛠️ Installation
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
```bash
git add .
docdrift commit
```

DocDrift will:
- Scan all changed functions and classes
- Find documentation that is now stale or wrong
- Show each finding with exact file and line number
- Ask if you want to fix it — AI generates the fix
- Auto-document any new undocumented functions
- Commit everything when you approve

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

- ❌ Blocks commits with critical doc errors
- ⚠️ Allows warnings — no workflow disruption

Skip when needed:
```bash
git commit --no-verify -m "message"
```

---

## ⚙️ How It Works
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

## 🌍 Supported Stack

- Python and JavaScript codebases
- Markdown and RST documentation
- README files, /docs folders, inline comments
- GitHub Actions for automatic team-wide PR checks
- LM Studio and Ollama — fully local and private
- Groq — free cloud AI, instant responses

---

## 🏗️ Built With

- Tree-sitter — code parsing across languages
- sentence-transformers — semantic documentation search
- ChromaDB — local vector index
- Groq / LM Studio / Ollama — LLM verdicts and fixes

---

## 📜 License

MIT

---

## ⭐ Why This Matters

Bad documentation kills good projects.

DocDrift makes sure your documentation stays as reliable as your code.

---

## 🙌 Contribute

PRs, ideas, and feedback are welcome.
Let's make documentation actually trustworthy.

---

## ⭐ Star This Repo

If this saved you even one hour — give it a star ⭐

[![PyPI version](https://badge.fury.io/py/docdrift.svg)](https://badge.fury.io/py/docdrift)