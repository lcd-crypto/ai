"""
Example of using observer agent with retry functionality.
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


def extract_with_retry_example(commit_message: str, repo_owner: str, date: datetime):
    """
    Example of extraction with automatic retry when validation fails.
    
    Args:
        commit_message: The commit message
        repo_owner: The repository owner
        date: The commit date
    """
    print("=" * 60)
    print("EXTRACTION WITH RETRY EXAMPLE")
    print("=" * 60)
    print(f"\nCommit Message: {commit_message}")
    print(f"Repository Owner: {repo_owner}")
    print(f"Date: {date}\n")
    
    # Step 1: Create extractor and observer agents
    print("Step 1: Initializing agents...")
    extractor = AIAgent()
    observer = ObserverAgent(
        strict_mode=False,
        generate_reports=True,
        max_retries=2  # Allow up to 2 retry iterations
    )
    print("✓ Agents initialized")
    print(f"  - Max retries: {observer.max_retries}")
    
    # Step 2: Extract with automatic retry
    print("\nStep 2: Extracting with automatic retry on validation failure...")
    try:
        extracted_data, validation_result, retry_count = observer.observe_with_retry(
            extractor_func=extractor.extract_from_commit,
            extractor_args={
                "commit_message": commit_message,
                "repo_owner": repo_owner,
                "date": date,
                "use_ai": True
            },
            source_context={
                "type": "commit",
                "repo_owner": repo_owner,
                "commit_message": commit_message
            }
        )
        
        print(f"✓ Extraction completed after {retry_count} retry attempts")
        
        if validation_result.is_valid:
            print("\n✅ VALIDATION PASSED")
            print(f"  - Repository Owner: {extracted_data.repo_owner}")
            print(f"  - Date: {extracted_data.date}")
            print(f"  - Version Change: {extracted_data.version_change or 'Not specified'}")
            print(f"  - Description: {extracted_data.description[:50]}...")
        else:
            print("\n❌ VALIDATION FAILED")
            print(f"  - Retry attempts: {retry_count}/{observer.max_retries}")
            print(f"  - Errors: {', '.join(validation_result.errors)}")
            if validation_result.warnings:
                print(f"  - Warnings: {', '.join(validation_result.warnings)}")
            
            if retry_count >= observer.max_retries:
                print("\n⚠️  All retry attempts exhausted. Report should have been generated.")
        
    except Exception as e:
        print(f"✗ Error during extraction: {e}")
    
    print()


def extract_with_retry_invalid_data():
    """Example with invalid data that will trigger retries."""
    print("=" * 60)
    print("EXAMPLE: Invalid Data with Retries")
    print("=" * 60 + "\n")
    
    # This commit message has minimal information, likely to fail validation
    extract_with_retry_example(
        commit_message="fix",  # Very short, likely to fail
        repo_owner="microsoft",
        date=datetime.now()
    )


def extract_with_retry_valid_data():
    """Example with valid data that should pass on first attempt."""
    print("=" * 60)
    print("EXAMPLE: Valid Data (Should Pass)")
    print("=" * 60 + "\n")
    
    # This commit message has good information, should pass validation
    extract_with_retry_example(
        commit_message="Release v2.1.0: Added new authentication system with OAuth2 support. Version change: 1.2.3 -> 2.1.0",
        repo_owner="microsoft",
        date=datetime.now()
    )


if __name__ == "__main__":
    # Example 1: Valid data (should pass)
    extract_with_retry_valid_data()
    
    # Example 2: Invalid data (will trigger retries)
    extract_with_retry_invalid_data()
    
    print("=" * 60)
    print("RETRY EXAMPLES COMPLETED")
    print("=" * 60)
