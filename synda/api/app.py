import os
import uuid
import yaml
import tempfile
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
import threading
from pathlib import Path

from synda.api.models import (
    RunRequest, 
    RunResponse,
    RunResult,
    PipelineStatus,
    InputType
)

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Synda API",
    description="API for generating synthetic data with Synda",
    version="0.1.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store runs in memory (would be a database in production)
runs: Dict[str, Dict[str, Any]] = {}

# Input type specifications (could be dynamically generated)
input_types = {
    "csv": {
        "name": "csv",
        "description": "CSV file input",
        "properties": {
            "path": {"type": "string", "description": "Path to the CSV file"},
            "target_column": {"type": "string", "description": "Column to extract"},
            "separator": {"type": "string", "description": "Column separator", "default": ";"}
        }
    },
    "xls": {
        "name": "xls",
        "description": "Excel file input",
        "properties": {
            "path": {"type": "string", "description": "Path to the Excel file"},
            "target_column": {"type": "string", "description": "Column to extract"},
            "sheet_name": {"type": "string", "description": "Sheet name", "default": "Sheet1"}
        }
    },
    "pdf": {
        "name": "pdf",
        "description": "PDF file input",
        "properties": {
            "path": {"type": "string", "description": "Path to the PDF file"},
            "pages": {"type": "array", "description": "Pages to extract (e.g. ['1-3', '5', '10-12'])", "default": []}
        }
    }
}


def run_pipeline_task(run_id: str, config: Dict[str, Any]):
    """Execute a Synda pipeline in a background task."""
    try:
        # Save config to a temporary file
        fd, config_path = tempfile.mkstemp(suffix='.yaml')
        os.close(fd)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Update status
        runs[run_id]["status"] = PipelineStatus.RUNNING
        
        # Log the command for debugging
        cmd = ["poetry", "run", "synda", "generate", config_path]
        cmd_str = " ".join(cmd)
        runs[run_id]["command"] = cmd_str
        print(f"Executing command: {cmd_str}")
        
        # Run in debug mode with higher verbosity
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"  # Force unbuffered output
        
        # Run the synda command
        result = subprocess.run(
            cmd, 
            capture_output=True,
            text=True,
            env=env
        )
        
        # Always capture both stdout and stderr
        runs[run_id]["stdout"] = result.stdout
        runs[run_id]["stderr"] = result.stderr
        runs[run_id]["returncode"] = result.returncode
        
        if result.returncode == 0:
            # Success
            runs[run_id]["status"] = PipelineStatus.COMPLETED
            runs[run_id]["result"] = result.stdout
        else:
            # Failure
            runs[run_id]["status"] = PipelineStatus.FAILED
            error_detail = result.stderr or "Aucune erreur retournée dans stderr"
            
            # Add detailed information about why it failed
            if not error_detail.strip():
                if result.stdout:
                    error_detail = f"Aucune erreur dans stderr, mais stdout contenait: {result.stdout[:500]}..."
                else:
                    error_detail = "Ni stderr ni stdout n'ont retourné d'informations"
            
            runs[run_id]["error"] = error_detail
        
        # Clean up
        os.unlink(config_path)
    
    except Exception as e:
        import traceback
        error_detail = f"Erreur d'exécution: {str(e)}\n\nStacktrace: {traceback.format_exc()}"
        runs[run_id]["status"] = PipelineStatus.FAILED
        runs[run_id]["error"] = error_detail


@app.get("/health")
def health_check():
    """Check if API is running."""
    return {"status": "ok"}


@app.post("/pipelines/run", response_model=RunResponse)
def run_pipeline(run_request: RunRequest, background_tasks: BackgroundTasks):
    """Start a new pipeline run with the provided configuration."""
    run_id = str(uuid.uuid4())
    
    # Initialize run entry
    runs[run_id] = {
        "run_id": run_id,
        "status": PipelineStatus.PENDING,
        "name": run_request.name,
        "config": run_request.config
    }
    
    # Execute in background
    background_tasks.add_task(run_pipeline_task, run_id, run_request.config)
    
    return {"run_id": run_id, "status": PipelineStatus.PENDING}


@app.get("/runs/{run_id}", response_model=RunResult)
def get_run(run_id: str):
    """Get the status or result of a run."""
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_data = runs[run_id]
    result = {
        "run_id": run_id,
        "status": run_data["status"],
    }
    
    # Ajouter les champs supplémentaires s'ils existent
    for field in ["result", "error", "stdout", "stderr", "command", "returncode"]:
        if field in run_data:
            result[field] = run_data[field]
    
    return result


@app.get("/runs", response_model=List[RunResponse])
def list_runs():
    """List all runs."""
    return [{"run_id": run_id, "status": data["status"]} for run_id, data in runs.items()]


@app.get("/inputs/types", response_model=List[InputType])
def get_input_types():
    """Get available input types."""
    return [input_types[k] for k in input_types]


@app.get("/inputs/types/{type_name}", response_model=InputType)
def get_input_type(type_name: str):
    """Get details for a specific input type."""
    if type_name not in input_types:
        raise HTTPException(status_code=404, detail=f"Input type '{type_name}' not found")
    
    return input_types[type_name]


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file and store it in the uploads directory.
    Returns the path to the stored file.
    """
    # Generate a unique filename to avoid collisions
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        # Read the file content and save it
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return {
            "filename": file.filename,
            "stored_path": str(file_path),
            "file_size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}") 