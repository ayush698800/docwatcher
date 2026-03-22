import os
import sys
import subprocess
import requests as req

sys.path.insert(0, os.path.dirname(__file__))

from docwatcher.symbol_extractor import get_changed_symbols
from docwatcher.embeddings import build_index, search_docs
from docwatcher.llm_checker import check_consistency

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPOSITORY = os.environ.get('GITHUB_REPOSITORY', '')
PR_NUMBER = os.environ.get('PR_NUMBER', '')

def get_changed_files_ci():
    try:
        result = subprocess.run(
            ['git', 'diff', 'HEAD~1', 'HEAD', '--name-only'],
            capture_output=True,
            text=True
        )
        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        return files
    except Exception as e:
        print(f"Error getting changed files: {e}")
        return []

def get_file_content_at_commit(filepath, commit):
    try:
        result = subprocess.run(
            ['git', 'show', f'{commit}:{filepath}'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout
        return ''
    except Exception:
        return ''

def post_pr_comment(body: str):
    if not all([GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER]):
        print("--- PR COMMENT ---")
        print(body)
        print("------------------")
        return

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{PR_NUMBER}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = req.post(url, json={"body": body}, headers=headers)
    if response.status_code == 201:
        print("PR comment posted successfully")
    else:
        print(f"Failed to post comment: {response.status_code}")
        print(response.text)

def main():
    repo_path = '.'
    print("DocDrift scanning...")

    changed_file_paths = get_changed_files_ci()
    print(f"Changed files: {changed_file_paths}")

    if not changed_file_paths:
        print("No changed files found")
        post_pr_comment("## DocDrift\n\nNo changed code files detected in this PR.")
        return

    build_index(repo_path)

    from dataclasses import dataclass
    @dataclass
    class FileChange:
        path: str
        old_content: str
        new_content: str

    all_symbols = []
    for filepath in changed_file_paths:
        if not filepath.endswith(('.py', '.js', '.ts')):
            continue
        old = get_file_content_at_commit(filepath, 'HEAD~1')
        new = get_file_content_at_commit(filepath, 'HEAD')
        symbols = get_changed_symbols(filepath, old, new)
        print(f"  {filepath}: {len(symbols)} changed symbols")
        all_symbols.extend(symbols)

    if not all_symbols:
        print("No trackable symbols found")
        post_pr_comment("## DocDrift\n\nNo function or class changes detected in this PR.")
        return

    print(f"Found {len(all_symbols)} changed symbols — running LLM checks...")

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
        post_pr_comment("## DocDrift\n\nAll documentation looks accurate.")
        return

    lines = ["## DocDrift — Documentation Check\n"]

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

    lines.append("---")
    lines.append(f"Found **{len(errors)} errors** · **{len(warnings)} warnings** · **{len(undocumented)} undocumented**")

    body = '\n'.join(lines)
    post_pr_comment(body)
    print(body)

    if errors:
        sys.exit(1)

if __name__ == '__main__':
    main()