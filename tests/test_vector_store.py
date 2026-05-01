import pytest

from app.services.embedder import embed_query, embed_texts
from app.services.vector_store import add_documents, reset, search


@pytest.fixture(autouse=True)
def clean_store():
    """Reset the vector store before every test."""
    reset()
    yield
    reset()


def test_empty_store_returns_no_results():
    query_vec = embed_query("what is the risk?")
    results = search(query_vec, top_k=5)
    assert results == []


def test_add_and_retrieve_single_document():
    texts = ["fraud detected in retail loan portfolio"]
    embeddings = embed_texts(texts)
    metadata = [{"doc_id": "doc-1", "source": "report.pdf", "doc_type": "report", "chunk_index": 0, "text": texts[0]}]

    add_documents(embeddings, metadata)

    query_vec = embed_query("fraud in loan portfolio")
    results = search(query_vec, top_k=1)

    assert len(results) == 1
    assert results[0]["doc_id"] == "doc-1"
    assert results[0]["text"] == texts[0]


def test_top_k_limits_results():
    texts = [f"document number {i}" for i in range(10)]
    embeddings = embed_texts(texts)
    metadata = [{"doc_id": f"doc-{i}", "source": "test", "doc_type": "report", "chunk_index": i, "text": t}
                for i, t in enumerate(texts)]

    add_documents(embeddings, metadata)

    results = search(embed_query("document"), top_k=3)
    assert len(results) == 3


def test_relevant_doc_ranks_higher_than_irrelevant():
    # Use texts with clear domain word separation so the mock embedder can distinguish them
    texts = [
        "fraud default claim deductible portfolio exposure",   # financial — relevant
        "beach volleyball sunset picnic barbecue hiking",      # unrelated — irrelevant
    ]
    embeddings = embed_texts(texts)
    metadata = [
        {"doc_id": "doc-relevant", "source": "report.pdf", "doc_type": "report", "chunk_index": 0, "text": texts[0]},
        {"doc_id": "doc-irrelevant", "source": "lifestyle.txt", "doc_type": "report", "chunk_index": 0, "text": texts[1]},
    ]
    add_documents(embeddings, metadata)

    results = search(embed_query("fraud claim default exposure"), top_k=2)

    # Lower score = closer = more relevant
    assert results[0]["doc_id"] == "doc-relevant"


def test_score_field_is_present():
    embeddings = embed_texts(["some financial text"])
    metadata = [{"doc_id": "d1", "source": "s", "doc_type": "report", "chunk_index": 0, "text": "some financial text"}]
    add_documents(embeddings, metadata)

    results = search(embed_query("financial"), top_k=1)
    assert "score" in results[0]
    assert isinstance(results[0]["score"], float)


def test_multiple_adds_accumulate():
    for i in range(3):
        embeddings = embed_texts([f"chunk {i} about risk"])
        metadata = [{"doc_id": f"doc-{i}", "source": "s", "doc_type": "report", "chunk_index": 0, "text": f"chunk {i}"}]
        add_documents(embeddings, metadata)

    results = search(embed_query("risk"), top_k=10)
    assert len(results) == 3
