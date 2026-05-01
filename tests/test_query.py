import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.vector_store import reset

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_store():
    reset()
    yield
    reset()


def _get_token() -> str:
    return client.post("/login", json={"username": "analyst", "password": "riskpass123"}).json()["access_token"]


def _ingest(text: str, source: str = "test.pdf", doc_type: str = "report") -> dict:
    token = _get_token()
    return client.post(
        "/ingest/",
        json={"text": text, "source": source, "doc_type": doc_type},
        headers={"Authorization": f"Bearer {token}"},
    ).json()


def test_query_requires_auth():
    resp = client.post("/query/", json={"question": "What is the risk level?"})
    assert resp.status_code == 401


def test_query_with_no_documents():
    token = _get_token()
    resp = client.post(
        "/query/",
        json={"question": "What is the default rate?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert data["risk_level"] in ["low", "medium", "high", "critical"]
    assert data["sources"] == []


def test_query_returns_answer_after_ingest():
    _ingest("Fraud cases surged by 60% in Q3. Default rate reached 4.1%. Immediate action required.")

    token = _get_token()
    resp = client.post(
        "/query/",
        json={"question": "What happened to fraud cases?", "top_k": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sources"]) >= 1
    assert data["risk_level"] in ["low", "medium", "high", "critical"]
    assert isinstance(data["confidence"], float)


def test_query_response_schema():
    _ingest("Late payments increased by 30% across the retail portfolio.")

    token = _get_token()
    resp = client.post(
        "/query/",
        json={"question": "Are there any late payment issues?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp.json()

    assert "answer" in data
    assert "risk_level" in data
    assert "risk_summary" in data
    assert "sources" in data
    assert "confidence" in data

    # Check source chunk fields
    if data["sources"]:
        source = data["sources"][0]
        assert "doc_id" in source
        assert "source" in source
        assert "doc_type" in source
        assert "chunk_index" in source
        assert "text" in source
        assert "score" in source


def test_query_high_risk_detected():
    _ingest("Fraud detected in 200 accounts. Sanctions violation confirmed. Immediate escalation required.")

    token = _get_token()
    resp = client.post(
        "/query/",
        json={"question": "Is there any fraud or violation?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp.json()
    assert data["risk_level"] in ["high", "critical"]


def test_query_rejects_short_question():
    token = _get_token()
    resp = client.post(
        "/query/",
        json={"question": "hi"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
