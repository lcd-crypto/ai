"""
Main entry point for the AI agent.
"""
import json
import sys
import argparse
from datetime import datetime
from ai_agent import AIAgent
from github_integration import GitHubIntegration
from git_integration import GitIntegration


def main():
    """Main function to run the AI agent."""
    parser = argparse.ArgumentParser(
        description="Extract information from pull requests or commits"
    )
    
    parser.add_argument(
        "--source",
        choices=["commit", "pr", "github-pr", "github-commit"],
        required=True,
        help="Source type: commit, pr, github-pr, or github-commit"
    )
    
    parser.add_argument(
        "--message",
        type=str,
        help="Commit message or PR title/body (for local commit/pr)"
    )
    
    parser.add_argument(
        "--body",
        type=str,
        help="PR body (required for --source pr)"
    )
    
    parser.add_argument(
        "--repo-owner",
        type=str,
        help="Repository owner name"
    )
    
    parser.add_argument(
        "--date",
        type=str,
        help="Date in ISO format (YYYY-MM-DDTHH:MM:SS)"
    )
    
    parser.add_argument(
        "--sha",
        type=str,
        help="Commit SHA (for commit or github-commit)"
    )
    
    parser.add_argument(
        "--repo",
        type=str,
        help="Repository path (for commit) or owner/repo (for github-pr/github-commit)"
    )
    
    parser.add_argument(
        "--pr-number",
        type=int,
        help="Pull request number (for github-pr)"
    )
    
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Use rule-based extraction instead of AI"
    )
    
    parser.add_argument(
        "--output",
        choices=["json", "pretty"],
        default="pretty",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    use_ai = not args.no_ai
    
    try:
        if args.source == "commit":
            # Local commit extraction
            if args.sha and args.repo:
                git = GitIntegration(args.repo, repo_owner=args.repo_owner)
                result = git.extract_from_commit_sha(args.sha, use_ai=use_ai)
            elif args.message and args.repo_owner:
                date = datetime.fromisoformat(args.date) if args.date else datetime.now()
                agent = AIAgent()
                result = agent.extract_from_commit(
                    commit_message=args.message,
                    repo_owner=args.repo_owner,
                    date=date,
                    use_ai=use_ai
                )
            else:
                parser.error("For commit: provide either (--sha and --repo) or (--message and --repo-owner)")
        
        elif args.source == "pr":
            # Local PR extraction
            if not args.message or not args.repo_owner:
                parser.error("For pr: --message and --repo-owner are required")
            
            date = datetime.fromisoformat(args.date) if args.date else datetime.now()
            agent = AIAgent()
            result = agent.extract_from_pr(
                title=args.message,
                body=args.body or "",
                repo_owner=args.repo_owner,
                date=date,
                use_ai=use_ai
            )
        
        elif args.source == "github-pr":
            # GitHub PR extraction
            if not args.repo or not args.pr_number:
                parser.error("For github-pr: --repo and --pr-number are required")
            
            github = GitHubIntegration()
            result = github.extract_from_pr_number(
                repo_name=args.repo,
                pr_number=args.pr_number,
                use_ai=use_ai
            )
        
        elif args.source == "github-commit":
            # GitHub commit extraction
            if not args.repo or not args.sha:
                parser.error("For github-commit: --repo and --sha are required")
            
            github = GitHubIntegration()
            result = github.extract_from_commit_sha(
                repo_name=args.repo,
                commit_sha=args.sha,
                use_ai=use_ai
            )
        
        # Output results
        if args.output == "json":
            print(json.dumps(result.dict(), indent=2, default=str))
        else:
            print("\n" + "="*50)
            print("EXTRACTED INFORMATION")
            print("="*50)
            print(f"Repository Owner: {result.repo_owner}")
            print(f"Date: {result.date}")
            print(f"Version Change: {result.version_change or 'Not specified'}")
            print(f"Description: {result.description}")
            print("="*50 + "\n")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
