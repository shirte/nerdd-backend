from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict

__all__ = ["Job", "JobCreate", "JobPublic", "JobUpdate", "JobInternal", "OutputFile"]


class OutputFile(BaseModel):
    format: str
    url: str


class Job(BaseModel):
    id: str
    job_type: str
    source_id: str
    params: dict
    created_at: datetime = datetime.now(timezone.utc)
    page_size: int = 10
    status: str
    entries_processed: List[Tuple[int, int]] = []
    num_entries_total: Optional[int] = None


class JobInternal(Job):
    user_id: Optional[str] = None
    referer: Optional[str] = None
    checkpoints_processed: List[int] = []
    num_checkpoints_total: Optional[int] = None
    output_formats: List[str] = []


class JobCreate(BaseModel):
    job_type: str
    source_id: str
    params: Dict[str, Any]


class JobPublic(Job):
    num_entries_processed: int = 0
    num_pages_total: Optional[int]
    num_pages_processed: int
    output_files: List[OutputFile]
    job_url: str
    results_url: str


class JobUpdate(BaseModel):
    id: str
    status: Optional[str] = None
    entries_processed: Optional[List[int]] = None
    num_entries_total: Optional[int] = None
    num_checkpoints_total: Optional[int] = None
    # checkpoint list update
    new_checkpoints_processed: Optional[List[int]] = None
    # output formats update
    new_output_formats: Optional[List[str]] = None
