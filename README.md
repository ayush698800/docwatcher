# DocWatcher

Detects stale documentation by watching your git commits.

When you change a function, DocWatcher finds every doc section 
that talks about it and asks a local AI — is this still accurate?

## Demo

[PUT YOUR GIF HERE]

## Install

pip install docwatcher

## Usage

docwatcher check

First run asks for your local AI endpoint once and remembers it.
Works with LM Studio and Ollama.

## How it works

1. Watches git diff for changed functions and classes
2. Finds related documentation using semantic search
3. Asks a local LLM — is this doc still accurate?
4. Reports stale docs with severity and exact reason

## Requirements

- Python 3.11+
- LM Studio or Ollama running locally