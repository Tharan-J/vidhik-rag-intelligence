"""
Vidhik API Application Package
==============================
Backend API service exposing the Legal RAG Engine via FastAPI.
"""

from .main import app, create_app

__all__ = ["app", "create_app"]
