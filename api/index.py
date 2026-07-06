"""Vercel serverless entry point. Vercel's Python runtime looks for an `app` (ASGI) or
`handler` callable in files under /api; this file just re-exports the real FastAPI app defined
in api/main.py, which is also what local dev runs directly via `uvicorn api.main:app`.
"""
from api.main import app  # noqa: F401
