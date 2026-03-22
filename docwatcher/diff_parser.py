import git
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
            old = item.a_blob.data_stream.read().decode('utf-8', errors='ignore') if item.a_blob else ''
            new = item.b_blob.data_stream.read().decode('utf-8', errors='ignore') if item.b_blob else ''
            changed.append(ChangedFile(path=item.a_path, old_content=old, new_content=new))
        except Exception:
            continue

    for item in repo.index.diff(None):
        try:
            old = item.a_blob.data_stream.read().decode('utf-8', errors='ignore') if item.a_blob else ''
            new_path = f"{repo_path}/{item.b_path}"
            try:
                with open(new_path, 'r', errors='ignore') as f:
                    new = f.read()
            except Exception:
                new = ''
            changed.append(ChangedFile(path=item.b_path, old_content=old, new_content=new))
        except Exception:
            continue

    staged_new = [item for item in repo.index.diff('HEAD') if item.a_blob is None]
    for item in staged_new:
        try:
            new = item.b_blob.data_stream.read().decode('utf-8', errors='ignore') if item.b_blob else ''
            changed.append(ChangedFile(path=item.b_path, old_content='', new_content=new))
        except Exception:
            continue

    return changed