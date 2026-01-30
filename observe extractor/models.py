"""
Data models for extracted information.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ExtractedInfo(BaseModel):
    """Model for extracted information from PR or commit."""
    requestor_name: str
    date: datetime
    new_version: Optional[str] = None
    description: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
