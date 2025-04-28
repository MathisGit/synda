import os
import uvicorn
import argparse

from synda.api.app import app


def main():
    """Launch the API server."""
    parser = argparse.ArgumentParser(description="Synda API Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    print(f"Starting Synda API server at http://{args.host}:{args.port}")
    print("API documentation available at: http://127.0.0.1:8000/docs")
    
    uvicorn.run(
        "synda.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main() 