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
    def extract_from_commit_message(
        commit_message: str,
        repo_owner: str,
        date: datetime
    ) -> ExtractedInfo:
        """
        Extract information from a commit message.
        
        Args:
            commit_message: The commit message text
            repo_owner: The repository owner name
            date: The commit date
            
        Returns:
            ExtractedInfo object with extracted data
        """
        # Try to extract version change from commit message
        version_change = CommitExtractor._extract_version_change(commit_message)
        
        # Clean up the description
        description = CommitExtractor._clean_description(commit_message)
        
        return ExtractedInfo(
            repo_owner=repo_owner,
            date=date,
            version_change=version_change,
            description=description
        )
    
    @staticmethod
    def _extract_version_change(text: str) -> Optional[str]:
        """Extract version change information from text."""
        # Patterns for version changes: v1.2.3 -> v2.0.0, 1.2.3 -> 2.0.0, etc.
        patterns = [
            r'v?(\d+\.\d+\.\d+)\s*[-→>]\s*v?(\d+\.\d+\.\d+)',  # 1.2.3 -> 2.0.0
            r'v?(\d+\.\d+)\s*[-→>]\s*v?(\d+\.\d+)',  # 1.2 -> 2.0
            r'version\s+(\d+\.\d+\.\d+)\s*to\s*(\d+\.\d+\.\d+)',  # version 1.2.3 to 2.0.0
            r'upgrade.*?v?(\d+\.\d+\.\d+).*?v?(\d+\.\d+\.\d+)',  # upgrade from 1.2.3 to 2.0.0
            r'bump.*?v?(\d+\.\d+\.\d+).*?v?(\d+\.\d+\.\d+)',  # bump version 1.2.3 to 2.0.0
            r'v?(\d+\.\d+\.\d+)',  # Single version (assume it's the new version)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # Version change from X to Y
                    return f"{match.group(1)} -> {match.group(2)}"
                else:
                    # Single version found
                    return match.group(1)
        
        return None
    
    @staticmethod
    def _clean_description(text: str) -> str:
        """Clean and format the description."""
        # Remove version patterns if they're at the start
        text = re.sub(r'^v?\d+\.\d+\.\d+\s*[-→>]\s*v?\d+\.\d+\.\d+\s*[-:]?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^v?\d+\.\d+\.\d+\s*[-:]?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^version\s+\d+\.\d+\.\d+\s*[-:]?\s*', '', text, flags=re.IGNORECASE)
        
        # Strip whitespace
        text = text.strip()
        
        return text


class PullRequestExtractor:
    """Extract information from pull requests."""
    
    @staticmethod
    def extract_from_pr(
        title: str,
        body: str,
        repo_owner: str,
        date: datetime
    ) -> ExtractedInfo:
        """
        Extract information from a pull request.
        
        Args:
            title: The PR title
            body: The PR body/description
            repo_owner: The repository owner name
            date: The PR creation date
            
        Returns:
            ExtractedInfo object with extracted data
        """
        # Combine title and body for analysis
        full_text = f"{title}\n{body}"
        
        # Try to extract version change
        version_change = PullRequestExtractor._extract_version_change(full_text)
        
        # Clean up the description
        description = PullRequestExtractor._clean_description(title, body)
        
        return ExtractedInfo(
            repo_owner=repo_owner,
            date=date,
            version_change=version_change,
            description=description
        )
    
    @staticmethod
    def _extract_version_change(text: str) -> Optional[str]:
        """Extract version change information from text."""
        # Patterns for version changes: v1.2.3 -> v2.0.0, 1.2.3 -> 2.0.0, etc.
        patterns = [
            r'v?(\d+\.\d+\.\d+)\s*[-→>]\s*v?(\d+\.\d+\.\d+)',  # 1.2.3 -> 2.0.0
            r'v?(\d+\.\d+)\s*[-→>]\s*v?(\d+\.\d+)',  # 1.2 -> 2.0
            r'version\s+(\d+\.\d+\.\d+)\s*to\s*(\d+\.\d+\.\d+)',  # version 1.2.3 to 2.0.0
            r'upgrade.*?v?(\d+\.\d+\.\d+).*?v?(\d+\.\d+\.\d+)',  # upgrade from 1.2.3 to 2.0.0
            r'bump.*?v?(\d+\.\d+\.\d+).*?v?(\d+\.\d+\.\d+)',  # bump version 1.2.3 to 2.0.0
            r'v?(\d+\.\d+\.\d+)',  # Single version (assume it's the new version)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # Version change from X to Y
                    return f"{match.group(1)} -> {match.group(2)}"
                else:
                    # Single version found
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
        description = re.sub(r'^v?\d+\.\d+\.\d+\s*[-→>]\s*v?\d+\.\d+\.\d+\s*[-:]?\s*', '', description, flags=re.IGNORECASE)
        description = re.sub(r'^v?\d+\.\d+\.\d+\s*[-:]?\s*', '', description, flags=re.IGNORECASE)
        description = re.sub(r'^version\s+\d+\.\d+\.\d+\s*[-:]?\s*', '', description, flags=re.IGNORECASE)
        
        # Strip whitespace
        description = description.strip()
        
        return description
