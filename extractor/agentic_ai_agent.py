"""
Agentic AI Agent for extracting information from pull requests and commits.

Replaces the single-shot AIAgent with a tool-use loop where the agent:
1. Decides WHICH sources to look at (commit msg, diff, PR body, CHANGELOG, etc.)
2. Calls tools iteratively until it's confident
3. Diagnoses its own failures and changes strategy on retry
4. Reports reasoning steps for observability
"""

import json
from typing import Optional
from datetime import datetime
from openai import OpenAI
from config import Config
from models import ExtractedInfo
from extractors import CommitExtractor, PullRequestExtractor


# ---------------------------------------------------------------------------
# Tool definitions — the agent picks which ones to call
# ---------------------------------------------------------------------------

EXTRACTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_commit_message",
            "description": "Read the raw commit message. Always try this first.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_pr_body",
            "description": "Read the pull request title and body. Use when commit message is sparse or missing version info.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_diff_for_version",
            "description": "Search the file diff for version number changes (e.g. in package.json, setup.py, CHANGELOG). Use when version is not in the message.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_changelog",
            "description": "Read the CHANGELOG or RELEASE_NOTES file at the commit. Use as fallback for description and version.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_extraction",
            "description": "Submit the final extraction result. Call this when you have enough information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_owner": {
                        "type": ["string", "null"],
                        "description": "GitHub username or organization that owns the repo"
                    },
                    "version_change": {
                        "type": ["string", "null"],
                        "description": "Version change string e.g. '1.2.3 -> 2.0.0', or null"
                    },
                    "description": {
                        "type": "string",
                        "description": "Clear, concise description of what changed"
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "How confident you are in this extraction"
                    },
                    "sources_used": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Which tools you called to build this result"
                    }
                },
                "required": ["description", "confidence", "sources_used"]
            }
        }
    }
]


# ---------------------------------------------------------------------------
# AgenticAIAgent
# ---------------------------------------------------------------------------

class AgenticAIAgent:
    """
    Agentic extractor that uses a tool-call loop rather than a single prompt.

    The agent autonomously decides which sources to consult (commit message,
    PR body, diff, CHANGELOG) and calls finalize_extraction when satisfied.
    On retry (triggered by the observer), it receives a diagnosis and adjusts
    its strategy accordingly.
    """

    MAX_STEPS = 3  # cap on tool calls per extraction

    def __init__(self):
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.temperature = Config.OPENAI_TEMPERATURE

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_from_commit(
        self,
        commit_message: str,
        repo_owner: str,
        date: datetime,
        use_ai: bool = True,
        repair_hint: Optional[str] = None,
        diff: Optional[str] = None,
        changelog: Optional[str] = None,
    ) -> ExtractedInfo:
        if not use_ai:
            return CommitExtractor.extract_from_commit_message(commit_message, repo_owner, date)

        sources = {
            "commit_message": commit_message,
            "pr_body": None,
            "diff": diff,
            "changelog": changelog,
        }
        return self._run_agentic_loop(sources, repo_owner, date, "commit", repair_hint)

    def extract_from_pr(
        self,
        title: str,
        body: str,
        repo_owner: str,
        date: datetime,
        use_ai: bool = True,
        repair_hint: Optional[str] = None,
        diff: Optional[str] = None,
        changelog: Optional[str] = None,
    ) -> ExtractedInfo:
        if not use_ai:
            return PullRequestExtractor.extract_from_pr(title, body, repo_owner, date)

        sources = {
            "commit_message": title,
            "pr_body": f"Title: {title}\n\nDescription: {body}",
            "diff": diff,
            "changelog": changelog,
        }
        return self._run_agentic_loop(sources, repo_owner, date, "pull request", repair_hint)

    # ------------------------------------------------------------------
    # Agentic loop
    # ------------------------------------------------------------------

    def _run_agentic_loop(
        self,
        sources: dict,
        repo_owner_hint: str,
        date: datetime,
        source_type: str,
        repair_hint: Optional[str]
    ) -> ExtractedInfo:
        """
        Run the tool-call loop until the agent calls finalize_extraction
        or the step budget is exhausted.
        """
        system_prompt = self._build_system_prompt(source_type, repair_hint)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Extract structured information from this {source_type}. "
                    f"Date: {date.isoformat()}. "
                    f"Repo owner hint (use only as fallback): {repo_owner_hint}. "
                    "Start by reading the commit message, then use other tools if needed."
                )
            }
        ]

        tool_calls_log = []

        for step in range(self.MAX_STEPS):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=EXTRACTION_TOOLS,
                tool_choice="auto",
                temperature=self.temperature,
            )

            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                break

            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                tool_calls_log.append(fn_name)

                print(f"  [Agent step {step + 1}] → {fn_name}")

                if fn_name == "finalize_extraction":
                    print(f"  [Agent] finalized after {step + 1} step(s), "
                          f"confidence={fn_args.get('confidence', '?')}, "
                          f"sources={fn_args.get('sources_used', [])}")
                    return ExtractedInfo(
                        repo_owner=fn_args.get("repo_owner") or repo_owner_hint,
                        date=date,
                        version_change=fn_args.get("version_change") or None,
                        description=fn_args.get("description") or "",
                    )

                tool_result = self._execute_tool(fn_name, sources)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result,
                })

        # Budget exhausted — fall back to rule-based
        print(f"[AgenticAIAgent] Step budget exhausted "
              f"(tools used: {tool_calls_log}). Falling back to rule-based extraction.")
        return CommitExtractor.extract_from_commit_message(
            sources.get("commit_message", ""), repo_owner_hint, date
        )

    # ------------------------------------------------------------------
    # Tool executor
    # ------------------------------------------------------------------

    def _execute_tool(self, tool_name: str, sources: dict) -> str:
        if tool_name == "read_commit_message":
            return sources.get("commit_message") or "No commit message available."

        if tool_name == "read_pr_body":
            return sources.get("pr_body") or "No PR body available."

        if tool_name == "search_diff_for_version":
            diff = sources.get("diff")
            if diff:
                version_lines = [
                    l for l in diff.splitlines()
                    if any(k in l.lower() for k in ["version", "\"version\"", "changelog"])
                ]
                return "\n".join(version_lines[:30]) or "No version changes found in diff."
            return "Diff not available for this extraction context."

        if tool_name == "read_changelog":
            return sources.get("changelog") or "No CHANGELOG file available."

        return f"Unknown tool: {tool_name}"

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------

    def _build_system_prompt(self, source_type: str, repair_hint: Optional[str]) -> str:
        base = f"""You are an expert extraction agent for software {source_type}s.
Your job is to extract: repo_owner, version_change, and description.

STRATEGY:
- Always start with read_commit_message.
- If the commit message is sparse or missing a version, call search_diff_for_version.
- If the PR body might have more detail, call read_pr_body.
- If version still not found, try read_changelog.
- Once you have enough information (or have exhausted sources), call finalize_extraction.
- Set confidence honestly: 'high' if you found explicit data, 'low' if you're guessing.

Do NOT make up version numbers. If genuinely not present, set version_change to null.
"""
        if repair_hint:
            base += f"""
IMPORTANT — PREVIOUS EXTRACTION FAILED:
A validation agent reviewed your last attempt and diagnosed this problem:
{repair_hint}

Adjust your strategy accordingly. For example, if the commit message lacked
a version, prioritize search_diff_for_version before finalizing.
"""
        return base
