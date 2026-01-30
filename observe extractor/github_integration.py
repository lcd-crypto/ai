"""
GitHub integration for fetching pull requests and commits.
"""
from typing import Optional
from datetime import datetime
from github import Github
from github.PullRequest import PullRequest
from github.Commit import Commit
from config import Config
from ai_agent import AIAgent


class GitHubIntegration:
    """Integration with GitHub API to fetch and process PRs and commits."""
    
    def __init__(self):
        """Initialize GitHub client."""
        self.github = Github(Config.GITHUB_TOKEN) if Config.GITHUB_TOKEN else None
        self.agent = AIAgent()
    
    def extract_from_pr_number(
        self,
        repo_name: str,
        pr_number: int,
        use_ai: bool = True
    ):
        """
        Extract information from a pull request by PR number.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: Pull request number
            use_ai: Whether to use AI extraction
            
        Returns:
            ExtractedInfo object
        """
        if not self.github:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN in .env file.")
        
        repo = self.github.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        return self.agent.extract_from_pr(
            title=pr.title,
            body=pr.body or "",
            author=pr.user.login,
            date=pr.created_at,
            use_ai=use_ai
        )
    
    def extract_from_commit_sha(
        self,
        repo_name: str,
        commit_sha: str,
        use_ai: bool = True
    ):
        """
        Extract information from a commit by SHA.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            commit_sha: Commit SHA
            use_ai: Whether to use AI extraction
            
        Returns:
            ExtractedInfo object
        """
        if not self.github:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN in .env file.")
        
        repo = self.github.get_repo(repo_name)
        commit = repo.get_commit(commit_sha)
        
        return self.agent.extract_from_commit(
            commit_message=commit.commit.message,
            author=commit.commit.author.name,
            date=commit.commit.author.date,
            use_ai=use_ai
        )
