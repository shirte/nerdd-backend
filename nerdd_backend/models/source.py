from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel

__all__ = ["Source", "SourcePublic"]


class Source(BaseModel):
    id: str
    format: Optional[str] = None
    # the filename that was provided by the user
    filename: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)


class SourcePublic(Source):
    pass
