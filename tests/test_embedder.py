import numpy as np
import pytest

from app.services.embedder import EMBEDDING_DIM, embed_query, embed_texts


def test_embed_single_text_returns_correct_dim():
    result = embed_texts(["hello world"])
    assert len(result) == 1
    assert len(result[0]) == EMBEDDING_DIM


def test_embed_batch_returns_one_vector_per_text():
    texts = ["first sentence", "second sentence", "third sentence"]
    result = embed_texts(texts)
    assert len(result) == 3


def test_embed_query_returns_flat_vector():
    vec = embed_query("what is the risk level?")
    assert isinstance(vec, list)
    assert len(vec) == EMBEDDING_DIM


def test_embedding_is_normalised():
    vec = embed_query("test normalisation")
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-5


def test_empty_list_returns_empty():
    assert embed_texts([]) == []


def test_deterministic():
    # Same text always produces the same vector
    vec1 = embed_query("default rate increased")
    vec2 = embed_query("default rate increased")
    assert vec1 == vec2


def test_different_texts_produce_different_vectors():
    vec1 = embed_query("fraud detected in claim")
    vec2 = embed_query("routine policy renewal")
    assert vec1 != vec2


def test_similar_texts_are_closer_than_dissimilar():
    # "fraud alert" and "fraud warning" should be closer than "fraud alert" and "sunny day"
    v1 = np.array(embed_query("fraud alert"))
    v2 = np.array(embed_query("fraud warning"))
    v3 = np.array(embed_query("sunny day weather"))

    sim_close = float(np.dot(v1, v2))
    sim_far = float(np.dot(v1, v3))
    assert sim_close > sim_far
