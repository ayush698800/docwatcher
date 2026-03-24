"""
embeddings.py
=============
Manages the ChromaDB vector index for all documentation files in a repo.

Uses the `all-MiniLM-L6-v2` sentence-transformer model for embedding.
Supports incremental re-indexing: only rebuilds when docs are newer than
the last-indexed marker file.
"""

import logging
import os

os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from typing import List

import chromadb
from sentence_transformers import SentenceTransformer

from docwatcher.doc_scanner import DocChunk, scan_docs

logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('huggingface_hub').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# Shared model — loaded once at import time
_model = SentenceTransformer('all-MiniLM-L6-v2')

DB_SUBDIR   = '.docwatcher/db'
MARKER_FILE = 'last_indexed'
COLLECTION  = 'docs'
MAX_DISTANCE = 1.2   # Cosine distance above this = irrelevant result, skip it


def _db_path(repo_path: str) -> str:
    return os.path.join(repo_path, DB_SUBDIR)


def get_client(repo_path: str) -> chromadb.PersistentClient:
    path = _db_path(repo_path)
    os.makedirs(path, exist_ok=True)
    return chromadb.PersistentClient(path=path)


def _marker_path(repo_path: str) -> str:
    return os.path.join(_db_path(repo_path), MARKER_FILE)


def get_index_age(repo_path: str) -> float:
    marker = _marker_path(repo_path)
    return os.path.getmtime(marker) if os.path.exists(marker) else float('inf')


def get_docs_age(repo_path: str) -> float:
    newest = 0.0
    skip = {'venv', '.git', '__pycache__', '.docwatcher'}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if f.endswith(('.md', '.rst', '.mdx')):
                path = os.path.join(root, f)
                newest = max(newest, os.path.getmtime(path))
    return newest


def needs_reindex(repo_path: str) -> bool:
    """Return True if any doc file is newer than the last index build."""
    return get_docs_age(repo_path) > get_index_age(repo_path)


def _touch_marker(repo_path: str):
    os.makedirs(_db_path(repo_path), exist_ok=True)
    with open(_marker_path(repo_path), 'w') as f:
        f.write('indexed')


def build_index(repo_path: str) -> int:
    """
    (Re)build the ChromaDB index from all .md / .rst / .mdx files.
    Returns the number of chunks indexed.
    """
    client = get_client(repo_path)

    # Drop old collection
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass

    collection = client.create_collection(COLLECTION)
    chunks = scan_docs(repo_path)

    if not chunks:
        logger.info(f"No doc files found in {repo_path}")
        return 0

    documents  = [c.content for c in chunks]
    embeddings = _model.encode(documents).tolist()
    metadatas  = [
        {
            'source_file': c.source_file,
            'start_line':  c.start_line,
            'heading':     c.heading
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
    _touch_marker(repo_path)
    logger.info(f"Indexed {len(chunks)} doc chunks for {repo_path}")
    return len(chunks)


def search_docs(repo_path: str, query: str, top_k: int = 3) -> List[dict]:
    """
    Semantic search over indexed documentation.

    Returns a list of matches (dicts with content, source_file, start_line,
    heading, distance), filtered to MAX_DISTANCE threshold.
    """
    client = get_client(repo_path)

    try:
        collection = client.get_collection(COLLECTION)
    except Exception:
        logger.warning(f"No index found for {repo_path}. Run build_index first.")
        return []

    query_embedding = _model.encode([query]).tolist()

    try:
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, collection.count())
        )
    except Exception as e:
        logger.warning(f"search_docs query failed: {e}")
        return []

    matches = []
    for i in range(len(results['documents'][0])):
        distance = results['distances'][0][i]
        if distance > MAX_DISTANCE:
            continue
        matches.append({
            'content':     results['documents'][0][i],
            'source_file': results['metadatas'][0][i]['source_file'],
            'start_line':  results['metadatas'][0][i]['start_line'],
            'heading':     results['metadatas'][0][i]['heading'],
            'distance':    round(distance, 3)
        })

    return matches
