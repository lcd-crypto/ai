"""
Local Git integration for extracting information from commits.
"""
from typing import Optional
from datetime import datetime
from git import Repo
from ai_agent import AIAgent


class GitIntegration:
    """Integration with local Git repository."""
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize Git repository.
        
        Args:
            repo_path: Path to the git repository
        """
        self.repo = Repo(repo_path)
        self.agent = AIAgent()
    
    def extract_from_commit_sha(
        self,
        commit_sha: str,
        use_ai: bool = True
    ):
        """
        Extract information from a commit by SHA.
        
        Args:
            commit_sha: Commit SHA (can be full or short SHA)
            use_ai: Whether to use AI extraction
            
        Returns:
            ExtractedInfo object
        """
        commit = self.repo.commit(commit_sha)
        
        return self.agent.extract_from_commit(
            commit_message=commit.message,
            author=commit.author.name,
            date=datetime.fromtimestamp(commit.committed_date),
            use_ai=use_ai
        )
    
    def extract_from_head(self, use_ai: bool = True):
        """
        Extract information from the HEAD commit.
        
        Args:
            use_ai: Whether to use AI extraction
            
        Returns:
            ExtractedInfo object
        """
        return self.extract_from_commit_sha("HEAD", use_ai=use_ai)
    
    def extract_from_latest_commit(self, use_ai: bool = True):
        """
        Extract information from the latest commit.
        
        Args:
            use_ai: Whether to use AI extraction
            
        Returns:
            ExtractedInfo object
        """
        return self.extract_from_head(use_ai=use_ai)
