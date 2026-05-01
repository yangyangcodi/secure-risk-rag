"""
Vector Store — persists and searches document embeddings using FAISS.

Two components work together:
  - FAISS index  : stores vectors, does fast nearest-neighbour search
  - Docstore     : stores original text + metadata keyed by vector ID

Flow:
  add_documents()  → chunk IDs assigned by FAISS → metadata saved to docstore
  search()         → FAISS returns closest IDs → look up text in docstore
"""

import json
import os
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

from app.core.config import settings
from app.services.embedder import EMBEDDING_DIM

# In-memory cache (loaded once from disk, reused across requests)
_index: Optional[faiss.Index] = None
_docstore: Dict[int, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_dirs() -> None:
    os.makedirs(os.path.dirname(os.path.abspath(settings.vector_index_path)), exist_ok=True)


def _load_index() -> faiss.Index:
    """Load index from disk or create a new one."""
    if os.path.exists(settings.vector_index_path):
        return faiss.read_index(settings.vector_index_path)
    _ensure_dirs()
    return faiss.IndexFlatL2(EMBEDDING_DIM)


def _load_docstore() -> Dict[int, Dict[str, Any]]:
    """Load docstore from disk or return empty dict."""
    if os.path.exists(settings.doc_store_path):
        with open(settings.doc_store_path) as f:
            raw = json.load(f)
        return {int(k): v for k, v in raw.items()}
    return {}


def _save() -> None:
    """Persist index and docstore to disk."""
    _ensure_dirs()
    faiss.write_index(_index, settings.vector_index_path)
    with open(settings.doc_store_path, "w") as f:
        json.dump(_docstore, f, indent=2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_index() -> faiss.Index:
    """Return the in-memory FAISS index, loading from disk if needed."""
    global _index
    if _index is None:
        _index = _load_index()
    return _index


def get_docstore() -> Dict[int, Dict[str, Any]]:
    """Return the in-memory docstore, loading from disk if needed."""
    global _docstore
    if not _docstore:
        _docstore = _load_docstore()
    return _docstore


def add_documents(
    embeddings: List[List[float]],
    metadata: List[Dict[str, Any]],
) -> List[int]:
    """Add embeddings + metadata to the store.

    Args:
        embeddings: One vector per chunk.
        metadata:   One metadata dict per chunk (text, source, doc_type, etc.)

    Returns:
        List of assigned vector IDs.
    """
    global _index, _docstore

    index = get_index()
    docstore = get_docstore()

    start_id = index.ntotal                          # next available ID
    vectors = np.array(embeddings, dtype="float32")
    index.add(vectors)                               # adds to FAISS

    ids = list(range(start_id, start_id + len(embeddings)))
    for vec_id, meta in zip(ids, metadata):
        docstore[vec_id] = meta                      # save text + metadata

    _save()
    return ids


def search(
    query_embedding: List[float],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Find the top_k most relevant chunks for a query vector.

    Args:
        query_embedding: The embedded query vector.
        top_k:           Number of results to return.

    Returns:
        List of metadata dicts with an added "score" field (L2 distance).
        Lower score = more similar.
    """
    index = get_index()
    docstore = get_docstore()

    if index.ntotal == 0:
        return []

    query_vec = np.array([query_embedding], dtype="float32")
    k = min(top_k, index.ntotal)
    distances, indices = index.search(query_vec, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        meta = docstore.get(idx, {})
        results.append({**meta, "score": round(float(dist), 4)})

    return results


def reset() -> None:
    """Clear the index and docstore (used in tests)."""
    global _index, _docstore
    _index = faiss.IndexFlatL2(EMBEDDING_DIM)
    _docstore = {}
