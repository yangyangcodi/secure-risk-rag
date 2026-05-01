"""
Ingest router — POST /ingest and POST /ingest/file
"""

import io
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.main import get_current_user
from app.models.schemas import IngestRequest, IngestResponse, ErrorResponse
from app.services.chunker import chunk_text
from app.services.embedder import embed_texts
from app.services.vector_store import add_documents

router = APIRouter(prefix="/ingest", tags=["ingest"])

_MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB


def _extract_pdf_text(data: bytes) -> str:
    """Extract plain text from a PDF byte stream using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise HTTPException(status_code=500, detail="pypdf is not installed on the server.")

    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages).strip()
    if not text:
        raise HTTPException(status_code=422, detail="Could not extract any text from the PDF. It may be scanned or image-only.")
    return text


def _ingest_text(text: str, source: str, doc_type: str) -> IngestResponse:
    """Shared ingestion logic used by both endpoints."""
    doc_id = str(uuid.uuid4())
    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=422, detail="Document produced no chunks after splitting.")

    embeddings = embed_texts(chunks)
    metadata = [
        {
            "doc_id": doc_id,
            "source": source,
            "doc_type": doc_type,
            "chunk_index": i,
            "text": chunk,
        }
        for i, chunk in enumerate(chunks)
    ]
    add_documents(embeddings, metadata)
    return IngestResponse(doc_id=doc_id, status="indexed", chunks_indexed=len(chunks))


# ---------------------------------------------------------------------------
# POST /ingest/ — plain text ingestion
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=IngestResponse,
    summary="Ingest a document as text",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid token"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal ingestion error"},
    },
)
def ingest(req: IngestRequest, user: dict = Depends(get_current_user)):
    """
    Ingest raw text into the vector knowledge base.

    The document is split into overlapping chunks, embedded, and stored
    in FAISS for semantic retrieval.

    **Supported doc types:** `report`, `transaction`, `alert`, `filing`
    """
    try:
        return _ingest_text(req.text, req.source, req.doc_type.value)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")


# ---------------------------------------------------------------------------
# POST /ingest/file — PDF file upload
# ---------------------------------------------------------------------------

@router.post(
    "/file",
    response_model=IngestResponse,
    summary="Upload and ingest a PDF file",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid token"},
        413: {"model": ErrorResponse, "description": "File too large (max 20 MB)"},
        422: {"model": ErrorResponse, "description": "Invalid file or no extractable text"},
        500: {"model": ErrorResponse, "description": "Internal ingestion error"},
    },
)
async def ingest_file(
    file: UploadFile = File(..., description="PDF file to upload (max 20 MB)"),
    doc_type: str = "report",
    user: dict = Depends(get_current_user),
):
    """
    Upload a PDF file and ingest its text into the knowledge base.

    The server extracts text from each page, then runs the same
    chunking → embedding → indexing pipeline as the text endpoint.

    **Accepted formats:** `.pdf` only
    **Max size:** 20 MB
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are supported.")

    if doc_type not in {"report", "transaction", "alert", "filing"}:
        doc_type = "report"

    try:
        data = await file.read()
        if len(data) > _MAX_PDF_BYTES:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 20 MB.")

        text = _extract_pdf_text(data)
        return _ingest_text(text, file.filename, doc_type)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"File ingestion failed: {exc}")
