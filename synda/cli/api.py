import typer
from typing import Optional

from synda.api.server import main as run_server


def api_command(
    host: str = typer.Option("127.0.0.1", help="Host to bind server to"),
    port: int = typer.Option(8000, help="Port to bind server to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
):
    """Launch the Synda API server."""
    import sys
    
    # Replace sys.argv with our options to pass to the server
    sys.argv = [
        "synda_api",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        sys.argv.append("--reload")
    
    # Run the server
    run_server() 