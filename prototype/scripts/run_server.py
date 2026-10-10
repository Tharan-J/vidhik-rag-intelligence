#!/usr/bin/env python3
"""
Vidhik Legal RAG API Server CLI Runner
======================================
Usage:
    python scripts/run_server.py [--host 0.0.0.0] [--port 8000] [--reload]
"""

import sys
import argparse
from pathlib import Path

# Add prototype root to python path
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

import uvicorn
from api.config import load_api_config


def main():
    parser = argparse.ArgumentParser(
        description="Run the Vidhik Legal RAG FastAPI Backend Server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Bind socket host (e.g. 0.0.0.0 or 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Bind socket port (e.g. 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code change (development only)",
    )
    args = parser.parse_args()

    cfg = load_api_config()
    host = args.host or cfg.server.host
    port = args.port or cfg.server.port
    reload = args.reload or cfg.server.reload

    print("=" * 80)
    print("STARTING VIDHIK LEGAL RAG BACKEND API SERVER")
    print("=" * 80)
    print(f"Host     : {host}")
    print(f"Port     : {port}")
    print(f"Docs URL : http://{host if host != '0.0.0.0' else '127.0.0.1'}:{port}/docs")
    print(f"CORS     : {cfg.cors.allowed_origins}")
    print("=" * 80)

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
