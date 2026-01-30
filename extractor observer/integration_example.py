"""
Example of integrating the observer agent with the extractor agent.
"""
import sys
import os
from datetime import datetime

# Add extractor directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'extractor'))

from extractor.ai_agent import AIAgent
from extractor.models import ExtractedInfo
from models import ExtractedData
from observer_agent import ObserverAgent


def extract_and_observe_commit(commit_message: str, repo_owner: str, date: datetime):
    """
    Extract information from a commit and observe/validate it.
    
    Args:
        commit_message: The commit message
        repo_owner: The repository owner
        date: The commit date
    """
    print("=" * 60)
    print("EXTRACTION AND OBSERVATION EXAMPLE")
    print("=" * 60)
    print(f"\nCommit Message: {commit_message}")
    print(f"Repository Owner: {repo_owner}")
    print(f"Date: {date}\n")
    
    # Step 1: Extract information using extractor agent
    print("Step 1: Extracting information with extractor agent...")
    extractor = AIAgent()
    try:
        extracted_info = extractor.extract_from_commit(
            commit_message=commit_message,
            repo_owner=repo_owner,
            date=date,
            use_ai=True
        )
        print("✓ Extraction completed")
        print(f"  - Repository Owner: {extracted_info.repo_owner}")
        print(f"  - Date: {extracted_info.date}")
        print(f"  - Version Change: {extracted_info.version_change or 'Not specified'}")
        print(f"  - Description: {extracted_info.description[:50]}...")
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return
    
    # Step 2: Convert to observer's data model
    print("\nStep 2: Converting to observer data model...")
    extracted_data = ExtractedData(
        repo_owner=extracted_info.repo_owner,
        date=extracted_info.date,
        version_change=extracted_info.version_change,
        description=extracted_info.description
    )
    print("✓ Conversion completed")
    
    # Step 3: Observe and validate using observer agent (with retry capability)
    print("\nStep 3: Observing and validating extraction (with retry support)...")
    observer = ObserverAgent(strict_mode=False, max_retries=2)
    try:
        result = observer.observe_extraction(
            extracted_data,
            source_context={"type": "commit", "repo_owner": repo_owner}
        )
        
        if result.is_valid:
            print("✓ Validation passed - all data is valid and non-empty")
        else:
            print("✗ Validation failed - some data is empty or invalid")
            print(f"  Errors: {', '.join(result.errors)}")
        
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
        
        # Show full validation result
        print("\n" + "=" * 60)
        print("OBSERVATION RESULT")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
    except ValueError as e:
        print(f"✗ Validation error: {e}")
    
    # Step 4: Show summary
    print("\nStep 4: Validation summary")
    summary = observer.get_validation_summary()
    print(f"  Total validations: {summary['total_validations']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Pass rate: {summary['pass_rate']:.1f}%")
    print()


def extract_and_observe_pr(title: str, body: str, repo_owner: str, date: datetime):
    """
    Extract information from a PR and observe/validate it.
    
    Args:
        title: The PR title
        body: The PR body
        repo_owner: The repository owner
        date: The PR creation date
    """
    print("=" * 60)
    print("PR EXTRACTION AND OBSERVATION EXAMPLE")
    print("=" * 60)
    print(f"\nPR Title: {title}")
    print(f"Repository Owner: {repo_owner}")
    print(f"Date: {date}\n")
    
    # Step 1: Extract information
    print("Step 1: Extracting information with extractor agent...")
    extractor = AIAgent()
    try:
        extracted_info = extractor.extract_from_pr(
            title=title,
            body=body,
            repo_owner=repo_owner,
            date=date,
            use_ai=True
        )
        print("✓ Extraction completed")
        print(f"  - Repository Owner: {extracted_info.repo_owner}")
        print(f"  - Date: {extracted_info.date}")
        print(f"  - Version Change: {extracted_info.version_change or 'Not specified'}")
        print(f"  - Description: {extracted_info.description[:50]}...")
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return
    
    # Step 2: Convert and observe
    print("\nStep 2: Observing and validating extraction...")
    extracted_data = ExtractedData(
        repo_owner=extracted_info.repo_owner,
        date=extracted_info.date,
        version_change=extracted_info.version_change,
        description=extracted_info.description
    )
    
    observer = ObserverAgent(strict_mode=True)  # Use strict mode for PRs
    try:
        result = observer.observe_extraction(
            extracted_data,
            source_context={"type": "pull_request", "repo_owner": repo_owner}
        )
        print("✓ Validation passed - data is complete and valid")
        
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
    except ValueError as e:
        print(f"✗ Validation failed: {e}")
        print("  Action: Extracted data is incomplete or invalid")
        return
    
    print("\n✓ All checks passed - extraction is valid!")


if __name__ == "__main__":
    # Example 1: Valid commit
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Valid Commit")
    print("=" * 60 + "\n")
    extract_and_observe_commit(
        commit_message="Release: version bump 1.2.3 -> 2.0.0 - Added new authentication system",
        repo_owner="microsoft",
        date=datetime.now()
    )
    
    # Example 2: PR with version change
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Pull Request")
    print("=" * 60 + "\n")
    extract_and_observe_pr(
        title="Feature: Add user authentication",
        body="This PR implements OAuth2 authentication. Version change: 1.2.3 -> 2.0.0",
        repo_owner="github",
        date=datetime.now()
    )
