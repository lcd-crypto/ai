"""
GitHub integration for fetching pull requests and commits.
"""
from typing import Optional
from datetime import datetime
from github import Github
from config import Config
from agentic_ai_agent import AgenticAIAgent


class GitHubIntegration:
    """Integration with GitHub API to fetch and process PRs and commits."""

    def __init__(self):
        self.github = Github(Config.GITHUB_TOKEN) if Config.GITHUB_TOKEN else None
        self.agent = AgenticAIAgent()

    # ------------------------------------------------------------------
    # Private helpers — fetch real source data for the agent's tools
    # ------------------------------------------------------------------

    def _get_pr_diff(self, pr) -> Optional[str]:
        """
        Fetch the unified diff for a PR via the GitHub API.
        Capped at 8000 chars to stay within context limits.
        """
        try:
            import requests
            headers = {
                "Authorization": f"token {Config.GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3.diff",
            }
            url = pr.url  # e.g. https://api.github.com/repos/owner/repo/pulls/123
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text[:8000]
        except Exception as e:
            print(f"[GitHubIntegration] Could not fetch PR diff: {e}")
        return None

    def _get_commit_diff(self, commit) -> Optional[str]:
        """
        Build a diff string from a GitHub commit's files list.
        Capped at 8000 chars.
        """
        try:
            lines = []
            for f in commit.files:
                lines.append(f"--- {f.filename}")
                if f.patch:
                    lines.append(f.patch)
                if sum(len(l) for l in lines) >= 8000:
                    break
            return "\n".join(lines)[:8000] or None
        except Exception as e:
            print(f"[GitHubIntegration] Could not build commit diff: {e}")
        return None

    def _get_changelog(self, repo, ref: str) -> Optional[str]:
        """
        Try to read a CHANGELOG file from the repo at the given ref.
        Returns first 3000 chars or None if not found.
        """
        for name in ("CHANGELOG.md", "CHANGELOG", "CHANGES.md", "RELEASE_NOTES.md"):
            try:
                content = repo.get_contents(name, ref=ref)
                return content.decoded_content.decode("utf-8", errors="replace")[:3000]
            except Exception:
                pass
        return None

    # ------------------------------------------------------------------
    # Public extraction methods
    # ------------------------------------------------------------------

    def extract_from_pr_number(
        self,
        repo_name: str,
        pr_number: int,
        use_ai: bool = True,
        repair_hint: Optional[str] = None,  # ← passed by observer on retry
    ):
        """
        Extract information from a pull request by PR number.

        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: Pull request number
            use_ai: Whether to use AI extraction
            repair_hint: Diagnosis from observer; changes agent strategy on retry

        Returns:
            ExtractedInfo object
        """
        if not self.github:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN in .env file.")

        repo = self.github.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        repo_owner = repo_name.split("/")[0]

        return self.agent.extract_from_pr(
            title=pr.title,
            body=pr.body or "",
            repo_owner=repo_owner,
            date=pr.created_at,
            use_ai=use_ai,
            repair_hint=repair_hint,
            diff=self._get_pr_diff(pr),
            changelog=self._get_changelog(repo, pr.head.sha),
        )

    def extract_from_commit_sha(
        self,
        repo_name: str,
        commit_sha: str,
        use_ai: bool = True,
        repair_hint: Optional[str] = None,  # ← passed by observer on retry
    ):
        """
        Extract information from a commit by SHA.

        Args:
            repo_name: Repository name in format "owner/repo"
            commit_sha: Commit SHA
            use_ai: Whether to use AI extraction
            repair_hint: Diagnosis from observer; changes agent strategy on retry

        Returns:
            ExtractedInfo object
        """
        if not self.github:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN in .env file.")

        repo = self.github.get_repo(repo_name)
        commit = repo.get_commit(commit_sha)
        repo_owner = repo_name.split("/")[0]

        return self.agent.extract_from_commit(
            commit_message=commit.commit.message,
            repo_owner=repo_owner,
            date=commit.commit.author.date,
            use_ai=use_ai,
            repair_hint=repair_hint,
            diff=self._get_commit_diff(commit),
            changelog=self._get_changelog(repo, commit_sha),
        )
