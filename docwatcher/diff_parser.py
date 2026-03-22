import git
import os
from dataclasses import dataclass
from typing import List

@dataclass
class ChangedFile:
    path: str
    old_content: str
    new_content: str

def get_changed_files(repo_path: str = '.') -> List[ChangedFile]:
    repo = git.Repo(repo_path)
    changed = []

    for item in repo.index.diff('HEAD'):
        try:
            old = ''
            new = ''

            # Read old content from HEAD commit directly
            try:
                old = (repo.head.commit.tree / item.a_path).data_stream.read().decode('utf-8', errors='ignore')
            except Exception:
                old = ''

            # Read new content from actual file on disk
            full_path = os.path.join(repo_path, item.b_path or item.a_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', errors='ignore') as f:
                    new = f.read()

            changed.append(ChangedFile(
                path=item.b_path or item.a_path,
                old_content=old,
                new_content=new
            ))
        except Exception:
            continue

    return changed