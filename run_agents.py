"""
Script to run extractor and observer agents on a repository.
"""
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Add extractor and observer directories to path
base_dir = os.path.dirname(__file__)
extractor_path = os.path.join(base_dir, 'extractor')
observer_path = os.path.join(base_dir, 'extractor observer')
sys.path.insert(0, extractor_path)
sys.path.insert(0, observer_path)

from extractor.ai_agent import AIAgent
from extractor.git_integration import GitIntegration
from extractor.github_integration import GitHubIntegration
from extractor.models import ExtractedInfo

# Import observer modules (handle space in directory name)
import importlib.util

observer_models_path = os.path.join(observer_path, 'models.py')
spec_models = importlib.util.spec_from_file_location("observer_models", observer_models_path)
observer_models = importlib.util.module_from_spec(spec_models)
spec_models.loader.exec_module(observer_models)
ExtractedData = observer_models.ExtractedData

observer_agent_path = os.path.join(observer_path, 'observer_agent.py')
spec_agent = importlib.util.spec_from_file_location("observer_agent", observer_agent_path)
observer_agent = importlib.util.module_from_spec(spec_agent)
spec_agent.loader.exec_module(observer_agent)
ObserverAgent = observer_agent.ObserverAgent


def run_on_local_repo(repo_path: str, commit_sha: str = None, max_retries: int = 2):
    """
    Run extractor and observer agents on a local Git repository.
    
    Args:
        repo_path: Path to the local Git repository
        commit_sha: Specific commit SHA to process (None for HEAD)
        max_retries: Maximum retry attempts
    """
    print("=" * 70)
    print("RUNNING EXTRACTOR AND OBSERVER AGENTS ON LOCAL REPOSITORY")
    print("=" * 70)
    print(f"\nRepository Path: {repo_path}")
    print(f"Commit SHA: {commit_sha or 'HEAD (latest)'}\n")
    
    try:
        # Step 1: Extract using extractor agent
        print("Step 1: Extracting information from repository...")
        git = GitIntegration(repo_path=repo_path)
        
        if commit_sha:
            extracted_info = git.extract_from_commit_sha(commit_sha, use_ai=True)
        else:
            extracted_info = git.extract_from_head(use_ai=True)
        
        print("✓ Extraction completed")
        print(f"  - Repository Owner: {extracted_info.repo_owner}")
        print(f"  - Date: {extracted_info.date}")
        print(f"  - Version Change: {extracted_info.version_change or 'Not specified'}")
        print(f"  - Description: {extracted_info.description[:100]}...")
        
        # Step 2: Convert to observer data model
        print("\nStep 2: Converting to observer data model...")
        extracted_data = ExtractedData(
            repo_owner=extracted_info.repo_owner,
            date=extracted_info.date,
            version_change=extracted_info.version_change,
            description=extracted_info.description
        )
        
        # Step 3: Observe with retry
        print("\nStep 3: Observing and validating with automatic retry...")
        observer = ObserverAgent(
            strict_mode=False,
            generate_reports=True,
            max_retries=max_retries
        )
        
        extracted_data, validation_result, retry_count = observer.observe_with_retry(
            extractor_func=git.extract_from_commit_sha if commit_sha else git.extract_from_head,
            extractor_args={"commit_sha": commit_sha or "HEAD", "use_ai": True},
            source_context={
                "type": "local_repository",
                "repo_path": repo_path,
                "commit_sha": commit_sha or "HEAD"
            }
        )
        
        # Step 4: Display results
        print("\n" + "=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        
        if validation_result.is_valid:
            print("✅ VALIDATION PASSED")
            print(f"  - Retry attempts: {retry_count}")
            print(f"  - All data is valid and non-empty")
        else:
            print("❌ VALIDATION FAILED")
            print(f"  - Retry attempts: {retry_count}/{max_retries}")
            print(f"  - Errors: {', '.join(validation_result.errors)}")
            if validation_result.warnings:
                print(f"  - Warnings: {', '.join(validation_result.warnings)}")
            
            if retry_count >= max_retries:
                print(f"\n⚠️  All retry attempts exhausted.")
                print(f"📄 Report generated in: extractor observer/reports/")
        
        print("=" * 70 + "\n")
        
        return validation_result.is_valid
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_on_github_repo(repo_name: str, pr_number: int = None, commit_sha: str = None, max_retries: int = 2):
    """
    Run extractor and observer agents on a GitHub repository.
    
    Args:
        repo_name: Repository name in format "owner/repo"
        pr_number: Pull request number (optional)
        commit_sha: Commit SHA (optional, required if pr_number not provided)
        max_retries: Maximum retry attempts
    """
    print("=" * 70)
    print("RUNNING EXTRACTOR AND OBSERVER AGENTS ON GITHUB REPOSITORY")
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
        # Step 1: Extract using GitHub integration
        print("Step 1: Extracting information from GitHub...")
        github = GitHubIntegration()
        
        if pr_number:
            extracted_info = github.extract_from_pr_number(repo_name, pr_number, use_ai=True)
            source_type = "pull_request"
            source_id = f"PR #{pr_number}"
        else:
            extracted_info = github.extract_from_commit_sha(repo_name, commit_sha, use_ai=True)
            source_type = "commit"
            source_id = commit_sha
        
        print("✓ Extraction completed")
        print(f"  - Repository Owner: {extracted_info.repo_owner}")
        print(f"  - Date: {extracted_info.date}")
        print(f"  - Version Change: {extracted_info.version_change or 'Not specified'}")
        print(f"  - Description: {extracted_info.description[:100]}...")
        
        # Step 2: Convert and observe
        print("\nStep 2: Observing and validating with automatic retry...")
        extracted_data = ExtractedData(
            repo_owner=extracted_info.repo_owner,
            date=extracted_info.date,
            version_change=extracted_info.version_change,
            description=extracted_info.description
        )
        
        observer = ObserverAgent(
            strict_mode=False,
            generate_reports=True,
            max_retries=max_retries
        )
        
        # For GitHub, we need to re-extract on retry
        def extract_func(**kwargs):
            if pr_number:
                return github.extract_from_pr_number(repo_name, pr_number, use_ai=True)
            else:
                return github.extract_from_commit_sha(repo_name, commit_sha, use_ai=True)
        
        extracted_data, validation_result, retry_count = observer.observe_with_retry(
            extractor_func=extract_func,
            extractor_args={},
            source_context={
                "type": source_type,
                "repo_name": repo_name,
                "source_id": source_id
            }
        )
        
        # Step 3: Display results
        print("\n" + "=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        
        if validation_result.is_valid:
            print("✅ VALIDATION PASSED")
            print(f"  - Retry attempts: {retry_count}")
        else:
            print("❌ VALIDATION FAILED")
            print(f"  - Retry attempts: {retry_count}/{max_retries}")
            print(f"  - Errors: {', '.join(validation_result.errors)}")
            
            if retry_count >= max_retries:
                print(f"\n⚠️  All retry attempts exhausted.")
                print(f"📄 Report generated in: extractor observer/reports/")
        
        print("=" * 70 + "\n")
        
        return validation_result.is_valid
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run extractor and observer agents on a repository"
    )
    
    parser.add_argument(
        "--repo-path",
        type=str,
        help="Path to local Git repository"
    )
    
    parser.add_argument(
        "--github-repo",
        type=str,
        help="GitHub repository in format 'owner/repo'"
    )
    
    parser.add_argument(
        "--commit-sha",
        type=str,
        help="Commit SHA to process (for local or GitHub repo)"
    )
    
    parser.add_argument(
        "--pr-number",
        type=int,
        help="Pull request number (for GitHub repo)"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum retry attempts (default: 2)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
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
