"""
Test script for the observer agent.
"""
from datetime import datetime
from models import ExtractedData
from observer_agent import ObserverAgent


def test_valid_extraction():
    """Test observation with valid extraction."""
    print("Test 1: Valid extraction")
    print("-" * 50)
    
    extracted_data = ExtractedData(
        repo_owner="microsoft",
        date=datetime.now(),
        version_change="1.2.3 -> 2.0.0",
        description="Added new authentication feature with OAuth2 support"
    )
    
    observer = ObserverAgent(strict_mode=False)
    result = observer.observe_extraction(extracted_data)
    
    print(result)
    print(f"Valid: {result.is_valid}\n")


def test_empty_repo_owner():
    """Test observation with empty repo owner."""
    print("Test 2: Empty repository owner")
    print("-" * 50)
    
    extracted_data = ExtractedData(
        repo_owner="",
        date=datetime.now(),
        version_change="1.2.3 -> 2.0.0",
        description="Added new feature"
    )
    
    observer = ObserverAgent(strict_mode=False)
    result = observer.observe_extraction(extracted_data)
    
    print(result)
    print(f"Valid: {result.is_valid}\n")


def test_empty_description():
    """Test observation with empty description."""
    print("Test 3: Empty description")
    print("-" * 50)
    
    extracted_data = ExtractedData(
        repo_owner="github",
        date=datetime.now(),
        version_change="2.0.0",
        description=""
    )
    
    observer = ObserverAgent(strict_mode=False)
    result = observer.observe_extraction(extracted_data)
    
    print(result)
    print(f"Valid: {result.is_valid}\n")


def test_missing_date():
    """Test observation with missing date."""
    print("Test 4: Missing date")
    print("-" * 50)
    
    try:
        extracted_data = ExtractedData(
            repo_owner="microsoft",
            date=None,  # This will fail in Pydantic, but testing the concept
            version_change="1.0.0",
            description="Fixed bug"
        )
        
        observer = ObserverAgent(strict_mode=False)
        result = observer.observe_extraction(extracted_data)
        print(result)
        print(f"Valid: {result.is_valid}\n")
    except Exception as e:
        print(f"Error (expected): {e}\n")


def test_invalid_version_change():
    """Test observation with invalid version change format."""
    print("Test 5: Invalid version change format")
    print("-" * 50)
    
    extracted_data = ExtractedData(
        repo_owner="microsoft",
        date=datetime.now(),
        version_change="invalid-version-format",
        description="Version change with invalid format"
    )
    
    observer = ObserverAgent(strict_mode=False)
    result = observer.observe_extraction(extracted_data)
    
    print(result)
    print(f"Valid: {result.is_valid}\n")


def test_batch_observation():
    """Test batch observation."""
    print("Test 6: Batch observation")
    print("-" * 50)
    
    extracted_data_list = [
        ExtractedData(
            repo_owner="microsoft",
            date=datetime.now(),
            version_change="1.0.0 -> 2.0.0",
            description="First valid extraction"
        ),
        ExtractedData(
            repo_owner="",
            date=datetime.now(),
            version_change="2.0.0",
            description="Second extraction with empty repo owner"
        ),
        ExtractedData(
            repo_owner="github",
            date=datetime.now(),
            version_change=None,
            description="Third valid extraction without version change"
        )
    ]
    
    observer = ObserverAgent(strict_mode=False)
    results = observer.observe_batch(extracted_data_list)
    
    for i, result in enumerate(results, 1):
        print(f"Extraction {i}: {'VALID' if result.is_valid else 'INVALID'}")
        if result.errors:
            print(f"  Errors: {', '.join(result.errors)}")
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
    
    print("\nSummary:")
    summary = observer.get_validation_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("OBSERVER AGENT TESTS")
    print("=" * 50 + "\n")
    
    test_valid_extraction()
    test_empty_repo_owner()
    test_empty_description()
    test_missing_date()
    test_invalid_version_change()
    test_batch_observation()
    
    print("=" * 50)
    print("ALL TESTS COMPLETED")
    print("=" * 50)
