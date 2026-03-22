import git
import os
from dataclasses import dataclass
from typing import List

@dataclass
class ChangedFile:
    path: str
    old_content: str
    new_content: str

def get_file_from_head(repo, path: str) -> str:
    try:
        return (repo.head.commit.tree / path).data_stream.read().decode('utf-8', errors='ignore')
    except Exception:
        return ''

def get_changed_files(repo_path: str = '.') -> List[ChangedFile]:
    repo = git.Repo(repo_path)
    changed = []
    seen_paths = set()

    # Staged changes
    for item in repo.index.diff('HEAD'):
        try:
            path = item.b_path or item.a_path
            if path in seen_paths:
                continue
            seen_paths.add(path)
            old = get_file_from_head(repo, item.a_path)
            full_path = os.path.join(repo_path, path)
            new = open(full_path, 'r', errors='ignore').read() if os.path.exists(full_path) else ''
            changed.append(ChangedFile(path=path, old_content=old, new_content=new))
        except Exception:
            continue

    # Unstaged changes — works without git add
    for item in repo.index.diff(None):
        try:
            path = item.b_path or item.a_path
            if path in seen_paths:
                continue
            seen_paths.add(path)
            old = get_file_from_head(repo, item.a_path)
            full_path = os.path.join(repo_path, path)
            new = open(full_path, 'r', errors='ignore').read() if os.path.exists(full_path) else ''
            changed.append(ChangedFile(path=path, old_content=old, new_content=new))
        except Exception:
            continue

    return changed