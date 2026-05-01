"""
Force MODEL_PROVIDER=mock for all tests so they never call external APIs.

This file is loaded by pytest before any test modules are imported,
so setting os.environ here takes effect before pydantic-settings reads them.
"""

import os

# Override before any app module is imported
os.environ["MODEL_PROVIDER"] = "mock"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["VERTEX_PROJECT_ID"] = ""
os.environ["EMBEDDING_MODEL"] = "all-MiniLM-L6-v2"
os.environ["GEN_MODEL"] = "claude-opus-4-6"
os.environ["VECTOR_INDEX_PATH"] = "./app/data/faiss.index"
os.environ["DOC_STORE_PATH"] = "./app/data/docstore.json"
