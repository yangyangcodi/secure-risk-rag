"""
Pydantic schemas — defines the shape of API request and response bodies.
"""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DocType(str, Enum):
    report = "report"
    transaction = "transaction"
    alert = "alert"
    filing = "filing"


class LoginRequest(BaseModel):
    username: str = Field(..., description="Your username", examples=["analyst"])
    password: str = Field(..., description="Your password", examples=["riskpass123"])


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="JWT token — include in Authorization: Bearer <token>")
    token_type: str = Field(default="bearer")


class IngestRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        max_length=100_000,
        description="Raw document text to ingest",
        examples=["Q3 2024 Report: Default rates surged to 4.1%. Fraud cases up 60% in retail lending. Immediate escalation recommended."],
    )
    source: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Origin of the document e.g. filename or URL",
        examples=["q3_risk_report.pdf"],
    )
    doc_type: DocType = Field(
        default=DocType.report,
        description="Category of the document",
    )


class IngestResponse(BaseModel):
    doc_id: str = Field(..., description="Unique ID assigned to this document")
    status: str = Field(..., description="Result of the ingestion")
    chunks_indexed: int = Field(..., description="Number of chunks stored in the vector index")


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The risk question to answer",
        examples=["What is the default rate trend and what risk does it pose?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of document chunks to retrieve (1–20)",
    )


class SourceChunk(BaseModel):
    doc_id: str = Field(..., description="ID of the source document")
    source: str = Field(..., description="Original filename or URL")
    doc_type: str = Field(..., description="Document category")
    chunk_index: int = Field(..., description="Position of this chunk in the original document")
    text: str = Field(..., description="The retrieved chunk text")
    score: float = Field(..., description="Similarity score — lower means more relevant")


class QueryResponse(BaseModel):
    answer: str = Field(..., description="Answer generated from retrieved context")
    risk_level: RiskLevel = Field(..., description="Assessed risk level: low | medium | high | critical")
    risk_summary: str = Field(..., description="1–2 sentence explanation of the risk finding")
    sources: List[SourceChunk] = Field(..., description="Document chunks used to generate the answer")
    confidence: float = Field(..., description="Model confidence between 0.0 and 1.0")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
