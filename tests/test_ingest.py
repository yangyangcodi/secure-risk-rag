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
    resp = client.post("/login", json={"username": "analyst", "password": "riskpass123"})
    return resp.json()["access_token"]


def test_ingest_requires_auth():
    resp = client.post("/ingest/", json={"text": "some financial report text here", "source": "test.pdf"})
    assert resp.status_code == 401


def test_ingest_success():
    token = _get_token()
    resp = client.post(
        "/ingest/",
        json={
            "text": "Q3 report: default rates rose to 3.2%. Late payments surged 40% in retail.",
            "source": "q3_report.pdf",
            "doc_type": "report",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "indexed"
    assert data["chunks_indexed"] >= 1
    assert "doc_id" in data


def test_ingest_returns_unique_doc_ids():
    token = _get_token()
    payload = {
        "text": "Transaction data showing high risk exposure in consumer lending.",
        "source": "transactions.csv",
        "doc_type": "transaction",
    }
    resp1 = client.post("/ingest/", json=payload, headers={"Authorization": f"Bearer {token}"})
    resp2 = client.post("/ingest/", json=payload, headers={"Authorization": f"Bearer {token}"})

    assert resp1.json()["doc_id"] != resp2.json()["doc_id"]


def test_ingest_rejects_short_text():
    token = _get_token()
    resp = client.post(
        "/ingest/",
        json={"text": "too short", "source": "test.pdf"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_ingest_valid_doc_types():
    token = _get_token()
    for doc_type in ["report", "transaction", "alert", "filing"]:
        resp = client.post(
            "/ingest/",
            json={"text": "Sample financial document with enough content to pass validation.", "source": "doc.pdf", "doc_type": doc_type},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Failed for doc_type={doc_type}"


def test_ingest_invalid_doc_type():
    token = _get_token()
    resp = client.post(
        "/ingest/",
        json={"text": "Sample financial document with enough content.", "source": "doc.pdf", "doc_type": "unknown"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
