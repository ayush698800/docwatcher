import os
import sys

import requests as req

from docwatcher.embeddings import build_index, needs_reindex
from docwatcher.engine import analyze_repo

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
PR_NUMBER = os.environ.get("PR_NUMBER", "")


def post_pr_comment(body: str):
    if not all([GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER]):
        print("--- PR COMMENT ---")
        print(body)
        print("------------------")
        return

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{PR_NUMBER}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = req.post(url, json={"body": body}, headers=headers, timeout=30)
    if response.status_code == 201:
        print("PR comment posted successfully")
    else:
        print(f"Failed to post comment: {response.status_code}")
        print(response.text)


def build_comment(analysis) -> str:
    if not analysis.changed_files:
        return "## DocDrift\n\nNo staged or changed files were detected for analysis."

    if not analysis.changed_symbols:
        return "## DocDrift\n\nNo function or class changes were detected in this PR."

    if not analysis.errors and not analysis.warnings and not analysis.undocumented:
        return "## DocDrift\n\nAll related documentation looks accurate."

    lines = ["## DocDrift", ""]

    if not analysis.llm_available:
        lines.append(
            "> AI checks were unavailable for this run, so DocDrift only reported undocumented symbols."
        )
        lines.append("")

    for verdict, _symbol in analysis.errors:
        lines.append(f"### Error: `{verdict.symbol_name}`")
        lines.append(f"- Docs: `{verdict.doc_file}` line {verdict.doc_line}")
        lines.append(f"- Section: {verdict.doc_heading}")
        lines.append(f"- Issue: {verdict.reason}")
        lines.append("")

    for verdict, _symbol in analysis.warnings:
        lines.append(f"### Warning: `{verdict.symbol_name}`")
        lines.append(f"- Docs: `{verdict.doc_file}` line {verdict.doc_line}")
        lines.append(f"- Section: {verdict.doc_heading}")
        lines.append(f"- Issue: {verdict.reason}")
        lines.append("")

    for symbol in analysis.undocumented:
        lines.append(f"### Undocumented: `{symbol.name}`")
        lines.append(f"- File: `{symbol.file_path}`")
        lines.append("- No related documentation chunk was found.")
        lines.append("")

    lines.append("---")
    lines.append(
        f"Found **{len(analysis.errors)} errors**, **{len(analysis.warnings)} warnings**, and **{len(analysis.undocumented)} undocumented symbols**."
    )
    return "\n".join(lines)


def main():
    repo_path = "."
    print("DocDrift PR check starting...")

    if needs_reindex(repo_path):
        build_index(repo_path)

    analysis = analyze_repo(repo_path)
    body = build_comment(analysis)
    post_pr_comment(body)
    print(body)

    if analysis.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
