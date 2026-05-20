"""
Script to run extractor and observer agents on a repository.
"""
import sys
import os
import argparse

base_dir = os.path.dirname(__file__)
extractor_path = os.path.join(base_dir, 'extractor')
observer_path = os.path.join(base_dir, 'extractor observer')
sys.path.insert(0, extractor_path)
sys.path.insert(0, observer_path)

from extractor.agentic_ai_agent import AgenticAIAgent
from extractor.git_integration import GitIntegration
from extractor.github_integration import GitHubIntegration
from extractor.models import ExtractedInfo

import importlib.util

observer_models_path = os.path.join(observer_path, 'models.py')
spec_models = importlib.util.spec_from_file_location("observer_models", observer_models_path)
observer_models = importlib.util.module_from_spec(spec_models)
spec_models.loader.exec_module(observer_models)
ExtractedData = observer_models.ExtractedData

observer_agent_path = os.path.join(observer_path, 'observer_agent.py')
spec_agent = importlib.util.spec_from_file_location("observer_agent", observer_agent_path)
observer_agent_mod = importlib.util.module_from_spec(spec_agent)
spec_agent.loader.exec_module(observer_agent_mod)
ObserverAgent = observer_agent_mod.ObserverAgent


def run_on_local_repo(repo_path: str, commit_sha: str = None, max_retries: int = 2):
    """
    Run agentic extractor and observer on a local Git repository.
    The observer owns the retry loop and passes repair_hint to the agent on failure.
    """
    print("=" * 70)
    print("RUNNING AGENTIC EXTRACTOR + OBSERVER ON LOCAL REPOSITORY")
    print("=" * 70)
    print(f"\nRepository Path: {repo_path}")
    print(f"Commit SHA: {commit_sha or 'HEAD (latest)'}\n")

    try:
        git = GitIntegration(repo_path=repo_path)
        agent = AgenticAIAgent()

        # Build the extractor function the observer will call (and retry).
        # repair_hint is injected by the observer on failed attempts.
        if commit_sha:
            def extractor_func(repair_hint=None, **kwargs):
                return git.extract_from_commit_sha(
                    commit_sha, use_ai=True, repair_hint=repair_hint
                )
        else:
            def extractor_func(repair_hint=None, **kwargs):
                return git.extract_from_head(
                    use_ai=True, repair_hint=repair_hint
                )

        observer = ObserverAgent(
            strict_mode=False,
            generate_reports=True,
            max_retries=max_retries
        )

        print("Running agentic extraction with observer validation...\n")

        extracted_data, validation_result, retry_count = observer.observe_with_retry(
            extractor_func=extractor_func,
            extractor_args={},
            source_context={
                "type": "local_repository",
                "repo_path": repo_path,
                "commit_sha": commit_sha or "HEAD"
            }
        )

        _print_results(validation_result, retry_count, max_retries, extracted_data)
        return validation_result.is_valid

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_on_github_repo(
    repo_name: str,
    pr_number: int = None,
    commit_sha: str = None,
    max_retries: int = 2
):
    """
    Run agentic extractor and observer on a GitHub repository.
    The observer owns the retry loop and passes repair_hint to the agent on failure.
    """
    print("=" * 70)
    print("RUNNING AGENTIC EXTRACTOR + OBSERVER ON GITHUB REPOSITORY")
    print("=" * 70)
    print(f"\nRepository: {repo_name}")

    if pr_number:
        print(f"Pull Request: #{pr_number}")
    elif commit_sha:
        print(f"Commit SHA: {commit_sha}")
    else:
        print("❌ Error: Either --pr-number or --commit-sha must be provided")
        return False
    print()

    try:
        github = GitHubIntegration()

        # repair_hint flows from observer → extractor on each retry
        if pr_number:
            source_type, source_id = "pull_request", f"PR #{pr_number}"

            def extractor_func(repair_hint=None, **kwargs):
                return github.extract_from_pr_number(
                    repo_name, pr_number, use_ai=True, repair_hint=repair_hint
                )
        else:
            source_type, source_id = "commit", commit_sha

            def extractor_func(repair_hint=None, **kwargs):
                return github.extract_from_commit_sha(
                    repo_name, commit_sha, use_ai=True, repair_hint=repair_hint
                )

        observer = ObserverAgent(
            strict_mode=False,
            generate_reports=True,
            max_retries=max_retries
        )

        print("Running agentic extraction with observer validation...\n")

        extracted_data, validation_result, retry_count = observer.observe_with_retry(
            extractor_func=extractor_func,
            extractor_args={},
            source_context={
                "type": source_type,
                "repo_name": repo_name,
                "source_id": source_id
            }
        )

        _print_results(validation_result, retry_count, max_retries, extracted_data)
        return validation_result.is_valid

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def _print_results(validation_result, retry_count, max_retries, extracted_data):
    """Print final validation results."""
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    if validation_result.is_valid:
        print("✅ VALIDATION PASSED")
        print(f"  - Attempts needed: {retry_count + 1}")
        print(f"  - Repository Owner: {extracted_data.repo_owner}")
        print(f"  - Version Change: {extracted_data.version_change or 'Not specified'}")
        print(f"  - Description: {extracted_data.description[:120]}...")
    else:
        print("❌ VALIDATION FAILED")
        print(f"  - Attempts made: {retry_count + 1}/{max_retries + 1}")
        print(f"  - Errors: {', '.join(validation_result.errors)}")
        if hasattr(validation_result, 'warnings') and validation_result.warnings:
            print(f"  - Warnings: {', '.join(validation_result.warnings)}")
        if retry_count >= max_retries:
            print("\n⚠️  All retry attempts exhausted.")
            print("📄 Report generated in: extractor observer/reports/")

    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run agentic extractor and observer agents on a repository"
    )
    parser.add_argument("--repo-path", type=str, help="Path to local Git repository")
    parser.add_argument("--github-repo", type=str, help="GitHub repository 'owner/repo'")
    parser.add_argument("--commit-sha", type=str, help="Commit SHA to process")
    parser.add_argument("--pr-number", type=int, help="Pull request number (GitHub only)")
    parser.add_argument("--max-retries", type=int, default=2,
                        help="Maximum retry attempts (default: 2)")

    args = parser.parse_args()

    if args.repo_path and args.github_repo:
        print("❌ Error: Cannot specify both --repo-path and --github-repo")
        return 1

    if not args.repo_path and not args.github_repo:
        print("❌ Error: Must specify either --repo-path or --github-repo")
        return 1

    if args.github_repo:
        if not args.pr_number and not args.commit_sha:
            print("❌ Error: Must specify either --pr-number or --commit-sha for GitHub repo")
            return 1
        success = run_on_github_repo(
            repo_name=args.github_repo,
            pr_number=args.pr_number,
            commit_sha=args.commit_sha,
            max_retries=args.max_retries
        )
    else:
        success = run_on_local_repo(
            repo_path=args.repo_path,
            commit_sha=args.commit_sha,
            max_retries=args.max_retries
        )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
