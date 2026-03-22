import os
from dataclasses import dataclass
from typing import List

@dataclass
class DocChunk:
    content: str
    source_file: str
    start_line: int
    heading: str

def find_doc_files(repo_path: str) -> List[str]:
    doc_files = []
    
    extensions = ['.md', '.rst', '.txt']
    skip_folders = ['venv', '.git', '__pycache__', 'node_modules']
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_folders]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                full_path = os.path.join(root, file)
                doc_files.append(full_path)
    
    return doc_files

def chunk_markdown(content: str, source_file: str) -> List[DocChunk]:
    chunks = []
    lines = content.split('\n')
    
    current_heading = 'Introduction'
    current_lines = []
    start_line = 0
    
    for i, line in enumerate(lines):
        if line.startswith('#'):
            if current_lines:
                chunk_text = '\n'.join(current_lines).strip()
                if chunk_text:
                    chunks.append(DocChunk(
                        content=chunk_text,
                        source_file=source_file,
                        start_line=start_line,
                        heading=current_heading
                    ))
            current_heading = line.lstrip('#').strip()
            current_lines = []
            start_line = i
        else:
            current_lines.append(line)
    
    if current_lines:
        chunk_text = '\n'.join(current_lines).strip()
        if chunk_text:
            chunks.append(DocChunk(
                content=chunk_text,
                source_file=source_file,
                start_line=start_line,
                heading=current_heading
            ))
    
    return chunks

def scan_docs(repo_path: str) -> List[DocChunk]:
    doc_files = find_doc_files(repo_path)
    all_chunks = []
    
    for file_path in doc_files:
        try:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
            chunks = chunk_markdown(content, file_path)
            all_chunks.extend(chunks)
        except Exception:
            continue
    
    return all_chunks