import chromadb
import os
from typing import List
from sentence_transformers import SentenceTransformer
from docwatcher.doc_scanner import DocChunk, scan_docs

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_client(repo_path: str):
    db_path = os.path.join(repo_path, '.docwatcher', 'db')
    os.makedirs(db_path, exist_ok=True)
    return chromadb.PersistentClient(path=db_path)

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
        matches.append({
            'content': results['documents'][0][i],
            'source_file': results['metadatas'][0][i]['source_file'],
            'start_line': results['metadatas'][0][i]['start_line'],
            'heading': results['metadatas'][0][i]['heading'],
        })

    return matches