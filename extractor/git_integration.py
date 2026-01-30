"""
Local Git integration for extracting information from commits.
"""
from typing import Optional
from datetime import datetime
from git import Repo
from ai_agent import AIAgent


class GitIntegration:
    """Integration with local Git repository."""
    
    def __init__(self, repo_path: str = ".", repo_owner: str = None):
        """
        Initialize Git repository.
        
        Args:
            repo_path: Path to the git repository
            repo_owner: Repository owner name (if not provided, will try to extract from remote)
        """
        self.repo = Repo(repo_path)
        self.agent = AIAgent()
        self.repo_owner = repo_owner or self._extract_repo_owner()
    
    def _extract_repo_owner(self) -> str:
        """Try to extract repo owner from git remote."""
        try:
            remote = self.repo.remote()
            url = remote.url
            # Extract owner from common URL formats
            if "github.com" in url:
                parts = url.replace(".git", "").split("/")
                if len(parts) >= 2:
                    return parts[-2]
            elif "git@" in url:
                # SSH format: git@github.com:owner/repo.git
                parts = url.split(":")
                if len(parts) >= 2:
                    repo_part = parts[1].replace(".git", "")
                    return repo_part.split("/")[0]
        except:
            pass
        return "unknown"
    
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
            repo_owner=self.repo_owner,
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
