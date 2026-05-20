"""
Patch for agentic_ai_agent.py — update extract_from_commit to accept
diff and changelog so git_integration can pass real data through.

Replace the existing extract_from_commit method with this one.
Everything else in agentic_ai_agent.py stays the same.
"""

def extract_from_commit(
    self,
    commit_message: str,
    repo_owner: str,
    date,
    use_ai: bool = True,
    repair_hint=None,
    diff=None,          # ← real diff from GitIntegration._get_diff()
    changelog=None,     # ← real changelog from GitIntegration._read_changelog()
):
    if not use_ai:
        from extractors import CommitExtractor
        return CommitExtractor.extract_from_commit_message(commit_message, repo_owner, date)

    sources = {
        "commit_message": commit_message,
        "pr_body": None,
        "diff": diff,           # now populated when called from GitIntegration
        "changelog": changelog, # now populated when called from GitIntegration
    }
    return self._run_agentic_loop(sources, repo_owner, date, "commit", repair_hint)

