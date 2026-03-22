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
    
    diffs = repo.index.diff('HEAD')
    
    for diff in diffs:
        try:
            old = diff.a_blob.data_stream.read().decode('utf-8', errors='ignore') if diff.a_blob else ''
            new = diff.b_blob.data_stream.read().decode('utf-8', errors='ignore') if diff.b_blob else ''
            changed.append(ChangedFile(
                path=diff.a_path,
                old_content=old,
                new_content=new
            ))
        except Exception:
            continue
    
    return changed