"""
Embedder — converts text chunks into vectors.

Supports three providers controlled by MODEL_PROVIDER in .env:
  - "mock"      : hash-based vectors, no network calls (for local dev/testing)
  - "anthropic" : sentence-transformers (real semantic embeddings, runs locally)
  - "vertex"    : Vertex AI text-embedding-004 (GCP production)

Why mock works for testing:
  Words shared between query and document push their vectors closer together,
  so FAISS nearest-neighbour retrieval behaves meaningfully without any LLM.
"""


import hashlib
from typing import List

import numpy as np

from app.core.config import settings

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 outputs 384-dim; mock matches this


# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------

def _mock_embed(text: str) -> List[float]:
    """Deterministic 384-dim vector from text using word-level hashing."""
    vec = np.zeros(EMBEDDING_DIM, dtype="float32")
    for word in text.lower().split():
        digest = hashlib.md5(word.encode()).digest()
        for i, b in enumerate(digest):
            idx = (hash(word) + i * 37) % EMBEDDING_DIM
            vec[idx] += (b / 255.0) - 0.5
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec.tolist()


def _mock_embed_batch(texts: List[str]) -> List[List[float]]:
    return [_mock_embed(t) for t in texts]


# ---------------------------------------------------------------------------
# Sentence-transformers provider (used for MODEL_PROVIDER=anthropic)
# ---------------------------------------------------------------------------

_st_model = None


def _get_st_model():
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer(settings.embedding_model)
    return _st_model


def _st_embed_batch(texts: List[str]) -> List[List[float]]:
    model = _get_st_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


# ---------------------------------------------------------------------------
# Vertex AI provider
# ---------------------------------------------------------------------------

_vertex_model = None


def _get_vertex_model():
    global _vertex_model
    if _vertex_model is None:
        import vertexai
        from vertexai.language_models import TextEmbeddingModel

        vertexai.init(
            project=settings.vertex_project_id,
            location=settings.vertex_location,
        )
        _vertex_model = TextEmbeddingModel.from_pretrained(settings.embedding_model)
    return _vertex_model


def _vertex_embed_batch(texts: List[str]) -> List[List[float]]:
    model = _get_vertex_model()
    return [e.values for e in model.get_embeddings(texts)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts into vectors.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each a list of floats).
    """
    if not texts:
        return []
    if settings.model_provider == "mock":
        return _mock_embed_batch(texts)
    if settings.model_provider == "anthropic":
        return _st_embed_batch(texts)
    return _vertex_embed_batch(texts)


def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]
