from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunRequest(BaseModel):
    """Model for a pipeline run request."""
    config: Dict[str, Any] = Field(..., description="The pipeline configuration")
    name: Optional[str] = Field(None, description="Optional name for this run")


class RunResponse(BaseModel):
    """Model for a pipeline run response."""
    run_id: str = Field(..., description="The ID of the run")
    status: PipelineStatus = Field(..., description="The status of the run")


class RunResult(RunResponse):
    """Model for pipeline run results."""
    result: Optional[Any] = Field(None, description="The run results if available")
    error: Optional[str] = Field(None, description="Error message if the run failed")
    stdout: Optional[str] = Field(None, description="Standard output of the command")
    stderr: Optional[str] = Field(None, description="Standard error of the command")
    command: Optional[str] = Field(None, description="Command that was executed")
    returncode: Optional[int] = Field(None, description="Return code of the command")


class InputType(BaseModel):
    """Model for input type information."""
    name: str
    description: str
    properties: Dict[str, Dict[str, Any]] 