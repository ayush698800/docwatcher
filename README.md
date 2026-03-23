# 🚀 DocDrift

> ⚡ Your docs should never lie again.

DocDrift finds stale documentation in your codebase **before you commit** — and fixes it automatically using AI.

No more outdated READMEs.
No more confused developers.
No more wasting hours debugging *wrong documentation*.

---

## 😤 The Problem

You change a function.
You forget to update the docs.

Now your README is lying.

A new developer follows it → wastes 3 hours → blames the project.

This happens **everywhere**.

> And nobody really fixes it.

---

## 💡 The Solution

**DocDrift hooks into your workflow and fixes documentation drift instantly.**

* Detects changed functions/classes
* Finds related documentation
* Checks if it's still correct
* Fixes it using AI
* Updates everything before commit

All in **one command**.

---

## ⚡ Demo

```bash
$ git add .
$ ./docdrift commit
```

```bash
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
✔ Generated docs

Commit now? (y/n): y
✔ Committed
```

---

## ✨ Features

* 🔍 Detects stale or incorrect documentation
* 🤖 AI-generated fixes (interactive or automatic)
* ⚡ Runs before every commit (git hook)
* 📄 Auto-generates missing documentation
* 🔗 Works with README, docs folders & comments
* 🧠 Semantic search for accurate doc matching
* 🔐 Supports local AI (privacy-friendly)

---

## 🛠️ Installation

```bash
git clone https://github.com/ayush698800/docwatcher.git
cd docwatcher
pip install -r requirements.txt
bash install-hook.sh
```

### 🔑 Set API Key (Optional - Cloud AI)

```bash
export GROQ_API_KEY="your_key_here"
```

👉 Get a free key at https://groq.com (takes ~2 minutes)

**OR**

Run fully locally using:

* LM Studio
* Ollama

No API key needed 🔒

---

## 🚀 Usage

### Smart Commit (Main Command)

```bash
git add .
./docdrift commit
```

### Check Only

```bash
./docdrift check
```

### Rebuild Index

```bash
./docdrift index
```

---

## 🤖 GitHub Actions (Auto PR Checks)

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
      - uses: actions/checkout@v3
        with:
          fetch-depth: 2

      - name: Run DocDrift
        uses: ayush698800/docwatcher@v2.0.0
        with:
          groq_api_key: ${{ secrets.GROQ_API_KEY }}
```

Now every PR gets checked automatically 🔥

---

## 🔗 Pre-Commit Hook

```bash
bash install-hook.sh
```

* ❌ Blocks commits with critical doc errors
* ⚠️ Allows warnings (no workflow disruption)

Skip if needed:

```bash
git commit --no-verify -m "message"
```

---

## ⚙️ How It Works

```
git diff
   ↓
Detect changed functions (Tree-sitter)
   ↓
Find related docs (semantic search)
   ↓
AI checks accuracy
   ↓
Fix or generate docs
   ↓
Apply + commit
```

---

## 🧠 What It Detects

* Changed function signatures with outdated docs
* Incorrect return values / exceptions
* Missing parameters in documentation
* Undocumented functions/classes
* Removed features still described

---

## 🌍 Supported Stack

* Python & JavaScript
* Markdown & RST
* README + /docs + inline comments

---

## 🏗️ Built With

* Tree-sitter
* sentence-transformers
* ChromaDB
* Groq / Ollama / LM Studio

---

## 📜 License

MIT

---

## ⭐ Why This Matters

> Bad documentation kills good projects.

DocDrift makes sure your documentation stays as reliable as your code.

---

## 🙌 Contribute

PRs, ideas, and feedback are welcome!
Let's make documentation actually trustworthy.

---

## ⭐ Star This Repo

If this saved you even one hour — give it a star ⭐
