"""
Data models for observer validation.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class ValidationResult(BaseModel):
    """Result of validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str] = []
    
    def __str__(self):
        """String representation of validation result."""
        status = "VALID" if self.is_valid else "INVALID"
        result = f"Validation Status: {status}\n"
        
        if self.errors:
            result += f"Errors ({len(self.errors)}):\n"
            for error in self.errors:
                result += f"  - {error}\n"
        
        if self.warnings:
            result += f"Warnings ({len(self.warnings)}):\n"
            for warning in self.warnings:
                result += f"  - {warning}\n"
        
        return result.strip()


class ExtractedData(BaseModel):
    """Model for extracted data from the extractor agent."""
    repo_owner: str
    date: datetime
    version_change: Optional[str] = None
    description: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
