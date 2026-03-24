"""
git_manager.py
==============
Handles all Git operations: cloning remote repos, querying commit history,
and retrieving file contents at specific revisions.

Supports shallow clones (--depth 50) with automatic fallback to deeper
history when no recent activity is detected.
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

DEFAULT_LOOK_BACK_DAYS = 14
FALLBACK_LOOK_BACK_DAYS = 60
SHALLOW_DEPTH = 50


class GitOps:
    """Static helper class for all Git shell operations."""

    @staticmethod
    def clone_repo(repo_url: str, target_dir: str, depth: int = SHALLOW_DEPTH) -> bool:
        """
        Shallow-clone a remote GitHub repo into target_dir.

        Uses --depth {depth} for speed. Returns True on success.
        Falls back gracefully on timeout or subprocess errors.
        """
        try:
            cmd = ["git", "clone", "--depth", str(depth), repo_url, target_dir]
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=180,
                check=True
            )
            logger.info(f"Cloned {repo_url} into {target_dir}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Clone failed for {repo_url}: {e.stderr.decode(errors='ignore')}")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"Clone timed out for {repo_url}")
            return False
        except Exception as e:
            logger.error(f"Unexpected clone error for {repo_url}: {e}")
            return False

    @staticmethod
    def get_recent_files(repo_path: str, days: int = DEFAULT_LOOK_BACK_DAYS) -> list:
        """
        Return a deduplicated list of Python/JS/TS files that were changed
        within the last `days` days, using git log.

        Applies auto-fallback logic: if shallow history doesn't go back far
        enough, the caller should retry with a larger `days` value.
        """
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            result = subprocess.run(
                ["git", "log", f"--since={since_date}", "--name-only", "--pretty=format:"],
                capture_output=True,
                text=True,
                cwd=repo_path,
                timeout=30,
                check=True
            )
            files = set(
                f.strip()
                for f in result.stdout.split("\n")
                if f.strip() and f.strip().endswith(('.py', '.js', '.ts'))
            )
            logger.info(f"Found {len(files)} changed files in last {days} days at {repo_path}")
            return list(files)
        except Exception as e:
            logger.warning(f"get_recent_files failed for {repo_path}: {e}")
            return []

    @staticmethod
    def get_file_at_revision(repo_path: str, filepath: str, revision: str = "HEAD~10") -> str:
        """
        Return the raw text of a file at a specific git revision.
        Returns empty string if the file didn't exist at that revision.
        """
        try:
            result = subprocess.run(
                ["git", "show", f"{revision}:{filepath}"],
                capture_output=True,
                text=True,
                cwd=repo_path,
                timeout=10
            )
            # git show exits non-zero if path doesn't exist at that revision
            if result.returncode != 0:
                return ''
            return result.stdout
        except Exception:
            return ''

    @staticmethod
    def get_file_content(repo_path: str, filepath: str):
        """
        Return (old_content, new_content) for a given file.

        old_content = file at HEAD~10 (or '' if it's a new file)
        new_content = current working tree content
        """
        old_code = GitOps.get_file_at_revision(repo_path, filepath, "HEAD~10")
        full_path = os.path.join(repo_path, filepath)
        try:
            new_code = open(full_path, 'r', errors='ignore').read() if os.path.exists(full_path) else ''
        except Exception:
            new_code = ''
        return old_code, new_code

    @staticmethod
    def get_changed_files_with_fallback(repo_path: str, is_verbose: bool = False) -> tuple:
        """
        Try DEFAULT_LOOK_BACK_DAYS first. If no results, expand to FALLBACK_LOOK_BACK_DAYS.

        Returns (changed_files: list, days_used: int).
        """
        files = GitOps.get_recent_files(repo_path, DEFAULT_LOOK_BACK_DAYS)
        if files:
            return files, DEFAULT_LOOK_BACK_DAYS

        if is_verbose:
            print(f"  [yellow]No changes in {DEFAULT_LOOK_BACK_DAYS}d. Expanding to {FALLBACK_LOOK_BACK_DAYS}d...[/yellow]")

        files = GitOps.get_recent_files(repo_path, FALLBACK_LOOK_BACK_DAYS)
        return files, FALLBACK_LOOK_BACK_DAYS
