from typing import Optional

from pydantic import BaseModel, ConfigDict

__all__ = ["Result"]


class Result(BaseModel):
    id: Optional[str] = None
    job_id: str
    mol_id: int

    model_config = ConfigDict(extra="allow")
