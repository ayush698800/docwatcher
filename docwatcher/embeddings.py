import chromadb
import os
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
from typing import List
from sentence_transformers import SentenceTransformer
from docwatcher.doc_scanner import DocChunk, scan_docs
import logging
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('huggingface_hub').setLevel(logging.ERROR)

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_client(repo_path: str):
    db_path = os.path.join(repo_path, '.docwatcher', 'db')
    os.makedirs(db_path, exist_ok=True)
    return chromadb.PersistentClient(path=db_path)

def get_index_age(repo_path: str) -> float:
    db_path = os.path.join(repo_path, '.docwatcher', 'db')
    marker = os.path.join(db_path, 'last_indexed')
    if not os.path.exists(marker):
        return float('inf')
    return os.path.getmtime(marker)

def get_docs_age(repo_path: str) -> float:
    newest = 0
    skip = ['venv', '.git', '__pycache__', '.docwatcher']
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if f.endswith('.md') or f.endswith('.rst'):
                path = os.path.join(root, f)
                newest = max(newest, os.path.getmtime(path))
    return newest

def needs_reindex(repo_path: str) -> bool:
    return get_docs_age(repo_path) > get_index_age(repo_path)

def touch_marker(repo_path: str):
    db_path = os.path.join(repo_path, '.docwatcher', 'db')
    os.makedirs(db_path, exist_ok=True)
    marker = os.path.join(db_path, 'last_indexed')
    with open(marker, 'w') as f:
        f.write('indexed')

def get_collection(client):
    return client.get_or_create_collection('docs')

def build_index(repo_path: str):
    client = get_client(repo_path)
    try:
        client.delete_collection('docs')
    except Exception:
        pass
    collection = client.create_collection('docs')
    chunks = scan_docs(repo_path)
    if not chunks:
        return 0
    documents = [c.content for c in chunks]
    embeddings = model.encode(documents).tolist()
    metadatas = [
        {
            'source_file': c.source_file,
            'start_line': c.start_line,
            'heading': c.heading
        }
        for c in chunks
    ]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    touch_marker(repo_path)
    return len(chunks)

def search_docs(repo_path: str, query: str, top_k: int = 3) -> List[dict]:
    client = get_client(repo_path)

    try:
        collection = client.get_collection('docs')
    except Exception:
        return []

    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    matches = []
    for i in range(len(results['documents'][0])):
        distance = results['distances'][0][i]
        if distance > 1.2:
            continue
        matches.append({
            'content': results['documents'][0][i],
            'source_file': results['metadatas'][0][i]['source_file'],
            'start_line': results['metadatas'][0][i]['start_line'],
            'heading': results['metadatas'][0][i]['heading'],
            'distance': round(distance, 3)
        })

    return matches