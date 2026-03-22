import os
import sys
import json
import requests

sys.path.insert(0, os.path.dirname(__file__))

from docwatcher.diff_parser import get_changed_files
from docwatcher.symbol_extractor import get_changed_symbols
from docwatcher.embeddings import build_index, search_docs
from docwatcher.llm_checker import check_consistency

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPOSITORY = os.environ.get('GITHUB_REPOSITORY', '')
PR_NUMBER = os.environ.get('PR_NUMBER', '')

def post_pr_comment(body: str):
    if not all([GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER]):
        print(body)
        return

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{PR_NUMBER}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    requests.post(url, json={"body": body}, headers=headers)

def main():
    repo_path = '.'

    print("DocWatcher scanning...")
    build_index(repo_path)

    files = get_changed_files(repo_path)
    if not files:
        print("No changed files found")
        return

    all_symbols = []
    for f in files:
        symbols = get_changed_symbols(f.path, f.old_content, f.new_content)
        all_symbols.extend(symbols)

    if not all_symbols:
        print("No trackable symbols found")
        return

    errors = []
    warnings = []
    undocumented = []

    for symbol in all_symbols:
        matches = search_docs(repo_path, symbol.name)

        if not matches:
            undocumented.append(symbol)
            continue

        for match in matches:
            verdict = check_consistency(
                symbol_name=symbol.name,
                old_code=symbol.old_code,
                new_code=symbol.new_code,
                doc_content=match['content'],
                doc_file=match['source_file'],
                doc_line=match['start_line'],
                doc_heading=match['heading'],
                repo_path=repo_path
            )

            if verdict and verdict.stale:
                if verdict.severity == 'error':
                    errors.append(verdict)
                else:
                    warnings.append(verdict)

    if not errors and not warnings and not undocumented:
        post_pr_comment("## DocWatcher\n\nAll documentation looks accurate.")
        return

    lines = ["## DocWatcher — Documentation Check\n"]

    for v in errors:
        lines.append(f"### ERROR — `{v.symbol_name}`")
        lines.append(f"**File:** `{v.doc_file}` line {v.doc_line}")
        lines.append(f"**Section:** {v.doc_section}")
        lines.append(f"**Issue:** {v.reason}\n")

    for v in warnings:
        lines.append(f"### WARNING — `{v.symbol_name}`")
        lines.append(f"**File:** `{v.doc_file}` line {v.doc_line}")
        lines.append(f"**Section:** {v.doc_section}")
        lines.append(f"**Issue:** {v.reason}\n")

    for s in undocumented:
        lines.append(f"### UNDOCUMENTED — `{s.name}`")
        lines.append(f"**File:** `{s.file_path}`")
        lines.append(f"No documentation found for this symbol.\n")

    lines.append(f"---")
    lines.append(f"Found **{len(errors)} errors**, **{len(warnings)} warnings**, **{len(undocumented)} undocumented**")

    post_pr_comment('\n'.join(lines))
    print('\n'.join(lines))

    if errors:
        sys.exit(1)

if __name__ == '__main__':
    main()
