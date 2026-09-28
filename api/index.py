"""Vercel serverless entry point for the DevVault API.

Vercel's Python runtime serves the ASGI `app` exported here. All /api/* requests are
rewritten to this function (see vercel.json); FastAPI still sees the original path.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402

__all__ = ["app"]
