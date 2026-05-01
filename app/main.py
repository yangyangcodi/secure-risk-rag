from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.security import create_access_token, verify_token
from app.models.schemas import LoginRequest, LoginResponse, ErrorResponse

# ---------------------------------------------------------------------------
# Tag descriptions — shown as sections in Swagger UI
# ---------------------------------------------------------------------------
tags_metadata = [
    {
        "name": "auth",
        "description": "Login and token management. Use `POST /login` to get a JWT, then click **Authorize** (top right) to authenticate all requests.",
    },
    {
        "name": "ingest",
        "description": "Upload financial documents into the knowledge base. Supports reports, transactions, alerts, and filings.",
    },
    {
        "name": "query",
        "description": "Ask risk questions against ingested documents. Returns an AI-generated answer, risk level, and source citations.",
    },
    {
        "name": "ops",
        "description": "System health and operational endpoints.",
    },
]

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Secure Risk Intelligence API",
    description="""
## Overview
An LLM-powered API for financial risk analysis using **Retrieval-Augmented Generation (RAG)**.

## How to use
1. **Login** — call `POST /login` to get an access token
2. **Authorize** — click the 🔒 **Authorize** button, paste your token
3. **Ingest** — upload financial documents via `POST /ingest`
4. **Query** — ask risk questions via `POST /query`

## Risk levels
| Level | Meaning |
|---|---|
| `low` | Routine activity, no material concern |
| `medium` | Warrants monitoring, potential exposure |
| `high` | Action required, significant exposure identified |
| `critical` | Immediate escalation needed, severe risk |
""",
    version="0.1.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

security = HTTPBearer()

# Demo credentials — replace with DB lookup in production
_USERS = {"analyst": "riskpass123"}


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post(
    "/login",
    tags=["auth"],
    response_model=LoginResponse,
    summary="Login and get access token",
    responses={401: {"model": ErrorResponse, "description": "Invalid credentials"}},
)
def login(req: LoginRequest):
    """
    Login with your username and password to receive a JWT access token.

    Use the returned token in the **Authorize** button (🔒) at the top of this page.
    """
    if _USERS.get(req.username) != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": req.username})
    return LoginResponse(access_token=token)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


@app.get(
    "/health",
    tags=["ops"],
    summary="Health check",
)
def health():
    """Returns `ok` if the API is running."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Static files and HTML pages
# ---------------------------------------------------------------------------
_static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/", include_in_schema=False)
def login_page():
    return FileResponse(os.path.join(_static_dir, "login.html"))


@app.get("/dashboard", include_in_schema=False)
def dashboard_page():
    return FileResponse(os.path.join(_static_dir, "dashboard.html"))


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
from app.routers import ingest, query  # noqa: E402
app.include_router(ingest.router)
app.include_router(query.router)
