"""
Example of integrating the monitoring agent with the extractor agent.
"""
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent import AIAgent
from monitor.monitor_agent import MonitorAgent
from monitor.validators import ValidationError


def extract_and_monitor_commit(commit_message: str, author: str, date: datetime):
    """
    Extract information from a commit and validate it.
    
    Args:
        commit_message: The commit message
        author: The commit author
        date: The commit date
    """
    print("=" * 60)
    print("EXTRACTION AND MONITORING EXAMPLE")
    print("=" * 60)
    print(f"\nCommit Message: {commit_message}")
    print(f"Author: {author}")
    print(f"Date: {date}\n")
    
    # Step 1: Extract information
    print("Step 1: Extracting information...")
    extractor = AIAgent()
    try:
        extracted_info = extractor.extract_from_commit(
            commit_message=commit_message,
            author=author,
            date=date,
            use_ai=True
        )
        print("✓ Extraction completed")
        print(f"  - Requestor: {extracted_info.requestor_name}")
        print(f"  - Date: {extracted_info.date}")
        print(f"  - Version: {extracted_info.new_version or 'Not specified'}")
        print(f"  - Description: {extracted_info.description[:50]}...")
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return
    
    # Step 2: Monitor and validate
    print("\nStep 2: Monitoring and validating extraction...")
    monitor = MonitorAgent(strict_mode=False)
    try:
        result = monitor.monitor_extraction(
            extracted_info,
            source_context={"type": "commit", "author": author}
        )
        
        if result.is_valid:
            print("✓ Validation passed")
        else:
            print("✗ Validation failed")
            print(f"  Errors: {', '.join(result.errors)}")
        
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
        
        # Show full validation result
        print("\n" + "=" * 60)
        print("VALIDATION RESULT")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
    except ValidationError as e:
        print(f"✗ Validation error: {e}")
    
    # Step 3: Show summary
    print("\nStep 3: Validation summary")
    summary = monitor.get_validation_summary()
    print(f"  Total validations: {summary['total_validations']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Pass rate: {summary['pass_rate']:.1f}%")
    print()


def extract_and_monitor_pr(title: str, body: str, author: str, date: datetime):
    """
    Extract information from a PR and validate it.
    
    Args:
        title: The PR title
        body: The PR body
        author: The PR author
        date: The PR creation date
    """
    print("=" * 60)
    print("PR EXTRACTION AND MONITORING EXAMPLE")
    print("=" * 60)
    print(f"\nPR Title: {title}")
    print(f"Author: {author}")
    print(f"Date: {date}\n")
    
    # Step 1: Extract information
    print("Step 1: Extracting information...")
    extractor = AIAgent()
    try:
        extracted_info = extractor.extract_from_pr(
            title=title,
            body=body,
            author=author,
            date=date,
            use_ai=True
        )
        print("✓ Extraction completed")
        print(f"  - Requestor: {extracted_info.requestor_name}")
        print(f"  - Date: {extracted_info.date}")
        print(f"  - Version: {extracted_info.new_version or 'Not specified'}")
        print(f"  - Description: {extracted_info.description[:50]}...")
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return
    
    # Step 2: Monitor and validate
    print("\nStep 2: Monitoring and validating extraction...")
    monitor = MonitorAgent(strict_mode=True)  # Use strict mode for PRs
    try:
        result = monitor.monitor_extraction(
            extracted_info,
            source_context={"type": "pull_request", "author": author}
        )
        print("✓ Validation passed - data is complete and accurate")
        
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
        print("  Action: Extraction data is incomplete or invalid")
        return
    
    print("\n✓ All checks passed - extraction is valid!")


if __name__ == "__main__":
    # Example 1: Valid commit
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Valid Commit")
    print("=" * 60 + "\n")
    extract_and_monitor_commit(
        commit_message="Release v2.1.0: Added new authentication system with OAuth2 support",
        author="Alice Developer",
        date=datetime.now()
    )
    
    # Example 2: PR with version
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Pull Request")
    print("=" * 60 + "\n")
    extract_and_monitor_pr(
        title="Feature: Add user authentication",
        body="This PR implements OAuth2 authentication for user login. Version bump to 2.0.0.",
        author="Bob Smith",
        date=datetime.now()
    )
