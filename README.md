# Secure Risk Intelligence API

An LLM-powered financial risk analysis API using **Retrieval-Augmented Generation (RAG)**. Ingest financial documents, ask risk questions, and get structured answers with risk levels and source citations.

---

## Features

- **JWT authentication** — secure login with Bearer token
- **Document ingestion** — plain text or PDF upload (up to 20 MB)
- **Semantic search** — FAISS vector store with sentence-transformer embeddings
- **Risk assessment** — LLM-generated answers with `low / medium / high / critical` risk levels
- **Multiple LLM providers** — Ollama (free, local), Anthropic Claude, or Vertex AI
- **Web dashboard** — drag-and-drop PDF upload, risk query UI

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Auth | JWT (python-jose) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector store | FAISS |
| LLM | Ollama / Anthropic Claude / Vertex AI |
| PDF parsing | pypdf |
| Testing | pytest (37 tests) |

---

## Getting Started

### 1. Clone and set up the environment

```bash
git clone <your-repo-url>
cd secure-risk-rag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
APP_ENV=dev
JWT_SECRET=your-secret-key

MODEL_PROVIDER=ollama        # ollama | anthropic | vertex | mock
EMBEDDING_MODEL=all-MiniLM-L6-v2
GEN_MODEL=llama3.2

# Only needed when MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=

# Only needed when MODEL_PROVIDER=vertex
VERTEX_PROJECT_ID=
VERTEX_LOCATION=us-central1
```

### 3. Set up your LLM provider

**Option A — Ollama (free, local)**
```bash
# Install Ollama from https://ollama.com
ollama pull llama3.2
ollama serve
```

**Option B — Anthropic Claude**
Get an API key at [console.anthropic.com](https://console.anthropic.com) and set `ANTHROPIC_API_KEY` in `.env`.

**Option C — Mock (no LLM, for testing)**
Set `MODEL_PROVIDER=mock` — uses keyword-based risk scoring, no external calls.

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

Open **http://localhost:8000**

---

## Usage

### Web UI

1. Go to `http://localhost:8000`
2. Log in with your credentials
3. **Ingest** — upload a PDF or paste text
4. **Query** — ask a risk question and get a structured answer

### API

**Login**
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst", "password": "riskpass123"}'
```

**Ingest a document**
```bash
curl -X POST http://localhost:8000/ingest/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"text": "Fraud cases surged 60% in Q3.", "source": "q3-report", "doc_type": "report"}'
```

**Ask a risk question**
```bash
curl -X POST http://localhost:8000/query/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What happened to fraud cases in Q3?", "top_k": 5}'
```

**Upload a PDF**
```bash
curl -X POST http://localhost:8000/ingest/file \
  -H "Authorization: Bearer <token>" \
  -F "file=@report.pdf" \
  -F "doc_type=report"
```

Full interactive docs at **http://localhost:8000/docs**

---

## Risk Levels

| Level | Meaning |
|---|---|
| `low` | Routine activity, no material concern |
| `medium` | Warrants monitoring, potential exposure |
| `high` | Action required, significant exposure identified |
| `critical` | Immediate escalation needed, severe risk |

---

## Project Structure

```
secure-risk-rag/
├── app/
│   ├── core/
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   └── security.py      # JWT create/verify
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   ├── routers/
│   │   ├── ingest.py        # POST /ingest, POST /ingest/file
│   │   └── query.py         # POST /query
│   ├── services/
│   │   ├── chunker.py       # Text splitting
│   │   ├── embedder.py      # Embedding providers
│   │   ├── risk.py          # LLM risk generation
│   │   └── vector_store.py  # FAISS index + docstore
│   ├── static/
│   │   ├── login.html
│   │   └── dashboard.html
│   └── main.py              # FastAPI app, auth endpoints
└── tests/                   # 37 pytest tests
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use the `mock` provider — no external API calls or LLM needed.

---

## Demo Credentials

| Username | Password |
|---|---|
| `analyst` | `riskpass123` |

> Replace with a real user database before deploying to production.
