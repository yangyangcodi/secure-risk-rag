"""
Query router — POST /query
"""

from fastapi import APIRouter, Depends, HTTPException

from app.main import get_current_user
from app.models.schemas import QueryRequest, QueryResponse, RiskLevel, SourceChunk, ErrorResponse
from app.services.embedder import embed_query
from app.services.risk import generate_risk_response
from app.services.vector_store import search

router = APIRouter(prefix="/query", tags=["query"])


@router.post(
    "/",
    response_model=QueryResponse,
    summary="Ask a risk question",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid token"},
        422: {"model": ErrorResponse, "description": "Validation error — question too short or top_k out of range"},
        500: {"model": ErrorResponse, "description": "Internal query error"},
    },
)
def query(req: QueryRequest, user: dict = Depends(get_current_user)):
    """
    Ask a risk question against the ingested knowledge base.

    The system retrieves the most relevant document chunks and generates
    a risk-assessed answer with a confidence score.

    **Steps internally:**
    1. Embed the question into a vector
    2. Search FAISS for the `top_k` most relevant chunks
    3. Pass chunks + question to the LLM
    4. Return structured answer with risk level and source citations

    **Risk levels:** `low` · `medium` · `high` · `critical`

    > Tip: Ingest documents first via `POST /ingest` before querying.
    """
    try:
        query_vec = embed_query(req.question)
        retrieved = search(query_vec, top_k=req.top_k)

        if retrieved:
            context = "\n\n".join(
                f"[Source: {r['source']} | Type: {r['doc_type']}]\n{r['text']}"
                for r in retrieved
            )
        else:
            context = "No relevant documents found in the knowledge base."

        answer, risk_level, risk_summary, confidence = generate_risk_response(
            question=req.question,
            context=context,
        )

        return QueryResponse(
            answer=answer,
            risk_level=RiskLevel(risk_level),
            risk_summary=risk_summary,
            sources=[
                SourceChunk(
                    doc_id=r["doc_id"],
                    source=r["source"],
                    doc_type=r["doc_type"],
                    chunk_index=r["chunk_index"],
                    text=r["text"],
                    score=r["score"],
                )
                for r in retrieved
            ],
            confidence=confidence,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}")
