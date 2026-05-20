"""
Local Git integration for extracting information from commits.
"""
from typing import Optional
from datetime import datetime
from git import Repo
from agentic_ai_agent import AgenticAIAgent


class GitIntegration:
    """Integration with local Git repository."""

    def __init__(self, repo_path: str = ".", repo_owner: str = None):
        self.repo = Repo(repo_path)
        self.agent = AgenticAIAgent()
        self.repo_owner = repo_owner or self._extract_repo_owner()

    def _extract_repo_owner(self) -> str:
        """Try to extract repo owner from git remote."""
        try:
            remote = self.repo.remote()
            url = remote.url
            if "github.com" in url:
                parts = url.replace(".git", "").split("/")
                if len(parts) >= 2:
                    return parts[-2]
            elif "git@" in url:
                parts = url.split(":")
                if len(parts) >= 2:
                    repo_part = parts[1].replace(".git", "")
                    return repo_part.split("/")[0]
        except Exception:
            pass
        return "unknown"

    def _get_diff(self, commit) -> Optional[str]:
        """
        Get the unified diff for a commit as a string.
        Capped at 200 lines so we don't blow the context window.
        """
        try:
            if commit.parents:
                diffs = commit.parents[0].diff(commit, create_patch=True)
            else:
                # Initial commit — diff against empty tree
                diffs = commit.diff(None, create_patch=True)

            lines = []
            for d in diffs:
                try:
                    lines.append(d.diff.decode("utf-8", errors="replace"))
                except Exception:
                    pass
                if len(lines) >= 200:
                    break

            return "\n".join(lines)[:8000]  # hard cap at ~8k chars
        except Exception as e:
            print(f"[GitIntegration] Could not get diff: {e}")
            return None

    def _read_changelog(self, commit) -> Optional[str]:
        """
        Try to read CHANGELOG.md or CHANGELOG from the commit tree.
        Returns first 3000 chars or None if not found.
        """
        for name in ("CHANGELOG.md", "CHANGELOG", "CHANGES.md", "RELEASE_NOTES.md"):
            try:
                blob = commit.tree[name]
                return blob.data_stream.read().decode("utf-8", errors="replace")[:3000]
            except (KeyError, Exception):
                pass
        return None

    def extract_from_commit_sha(
        self,
        commit_sha: str,
        use_ai: bool = True,
        repair_hint: Optional[str] = None,   # ← passed by observer on retry
    ):
        """
        Extract information from a commit by SHA.

        Args:
            commit_sha: Commit SHA (full or short)
            use_ai: Whether to use AI extraction
            repair_hint: Diagnosis from observer; changes agent strategy on retry

        Returns:
            ExtractedInfo object
        """
        commit = self.repo.commit(commit_sha)

        return self.agent.extract_from_commit(
            commit_message=commit.message,
            repo_owner=self.repo_owner,
            date=datetime.fromtimestamp(commit.committed_date),
            use_ai=use_ai,
            repair_hint=repair_hint,
            # Real data sources for the agent's tool calls
            diff=self._get_diff(commit),
            changelog=self._read_changelog(commit),
        )

    def extract_from_head(
        self,
        use_ai: bool = True,
        repair_hint: Optional[str] = None,
    ):
        """Extract information from the HEAD commit."""
        return self.extract_from_commit_sha("HEAD", use_ai=use_ai, repair_hint=repair_hint)

    def extract_from_latest_commit(
        self,
        use_ai: bool = True,
        repair_hint: Optional[str] = None,
    ):
        """Alias for extract_from_head."""
        return self.extract_from_head(use_ai=use_ai, repair_hint=repair_hint)
