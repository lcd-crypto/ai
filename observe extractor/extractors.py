"""
Extractors for pull requests and commits.
"""
from typing import Optional
from datetime import datetime
import re
from models import ExtractedInfo


class CommitExtractor:
    """Extract information from git commits."""
    
    @staticmethod
    def extract_from_commit_message(commit_message: str, author: str, date: datetime) -> ExtractedInfo:
        """
        Extract information from a commit message.
        
        Args:
            commit_message: The commit message text
            author: The author/requestor name
            date: The commit date
            
        Returns:
            ExtractedInfo object with extracted data
        """
        # Try to extract version from commit message
        version = CommitExtractor._extract_version(commit_message)
        
        # Clean up the description
        description = CommitExtractor._clean_description(commit_message)
        
        return ExtractedInfo(
            requestor_name=author,
            date=date,
            new_version=version,
            description=description
        )
    
    @staticmethod
    def _extract_version(text: str) -> Optional[str]:
        """Extract version number from text."""
        # Common version patterns: v1.2.3, version 1.2.3, 1.2.3, etc.
        patterns = [
            r'v(\d+\.\d+\.\d+)',
            r'version\s+(\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+)',
            r'v(\d+\.\d+)',
            r'version\s+(\d+\.\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _clean_description(text: str) -> str:
        """Clean and format the description."""
        # Remove version patterns if they're at the start
        text = re.sub(r'^v?\d+\.\d+\.\d+\s*[-:]?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^version\s+\d+\.\d+\.\d+\s*[-:]?\s*', '', text, flags=re.IGNORECASE)
        
        # Strip whitespace
        text = text.strip()
        
        return text


class PullRequestExtractor:
    """Extract information from pull requests."""
    
    @staticmethod
    def extract_from_pr(title: str, body: str, author: str, date: datetime) -> ExtractedInfo:
        """
        Extract information from a pull request.
        
        Args:
            title: The PR title
            body: The PR body/description
            author: The PR author/requestor name
            date: The PR creation date
            
        Returns:
            ExtractedInfo object with extracted data
        """
        # Combine title and body for analysis
        full_text = f"{title}\n{body}"
        
        # Try to extract version
        version = PullRequestExtractor._extract_version(full_text)
        
        # Clean up the description
        description = PullRequestExtractor._clean_description(title, body)
        
        return ExtractedInfo(
            requestor_name=author,
            date=date,
            new_version=version,
            description=description
        )
    
    @staticmethod
    def _extract_version(text: str) -> Optional[str]:
        """Extract version number from text."""
        # Common version patterns: v1.2.3, version 1.2.3, 1.2.3, etc.
        patterns = [
            r'v(\d+\.\d+\.\d+)',
            r'version\s+(\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+)',
            r'v(\d+\.\d+)',
            r'version\s+(\d+\.\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def _clean_description(title: str, body: str) -> str:
        """Clean and format the description."""
        # Combine title and body
        description = f"{title}"
        if body:
            description += f"\n\n{body}"
        
        # Remove version patterns if they're at the start
        description = re.sub(r'^v?\d+\.\d+\.\d+\s*[-:]?\s*', '', description, flags=re.IGNORECASE)
        description = re.sub(r'^version\s+\d+\.\d+\.\d+\s*[-:]?\s*', '', description, flags=re.IGNORECASE)
        
        # Strip whitespace
        description = description.strip()
        
        return description
