"""
Test script for the monitoring agent.
"""
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ExtractedInfo
from monitor.monitor_agent import MonitorAgent
from monitor.validators import ValidationError


def test_valid_extraction():
    """Test monitoring with valid extraction."""
    print("Test 1: Valid extraction")
    print("-" * 50)
    
    extracted_info = ExtractedInfo(
        requestor_name="John Doe",
        date=datetime.now(),
        new_version="1.2.3",
        description="Added new authentication feature with OAuth2 support"
    )
    
    monitor = MonitorAgent(strict_mode=False)
    result = monitor.monitor_extraction(extracted_info)
    
    print(result)
    print(f"Valid: {result.is_valid}\n")


def test_empty_requestor():
    """Test monitoring with empty requestor name."""
    print("Test 2: Empty requestor name")
    print("-" * 50)
    
    extracted_info = ExtractedInfo(
        requestor_name="",
        date=datetime.now(),
        new_version="1.2.3",
        description="Added new feature"
    )
    
    monitor = MonitorAgent(strict_mode=False)
    result = monitor.monitor_extraction(extracted_info)
    
    print(result)
    print(f"Valid: {result.is_valid}\n")


def test_empty_description():
    """Test monitoring with empty description."""
    print("Test 3: Empty description")
    print("-" * 50)
    
    extracted_info = ExtractedInfo(
        requestor_name="Jane Smith",
        date=datetime.now(),
        new_version="2.0.0",
        description=""
    )
    
    monitor = MonitorAgent(strict_mode=False)
    result = monitor.monitor_extraction(extracted_info)
    
    print(result)
    print(f"Valid: {result.is_valid}\n")


def test_missing_date():
    """Test monitoring with missing date."""
    print("Test 4: Missing date")
    print("-" * 50)
    
    extracted_info = ExtractedInfo(
        requestor_name="Bob Wilson",
        date=None,  # This will fail in Pydantic, but testing the concept
        new_version="1.0.0",
        description="Fixed bug in authentication"
    )
    
    try:
        monitor = MonitorAgent(strict_mode=False)
        result = monitor.monitor_extraction(extracted_info)
        print(result)
        print(f"Valid: {result.is_valid}\n")
    except Exception as e:
        print(f"Error (expected): {e}\n")


def test_short_description():
    """Test monitoring with very short description."""
    print("Test 5: Very short description")
    print("-" * 50)
    
    extracted_info = ExtractedInfo(
        requestor_name="Alice Developer",
        date=datetime.now(),
        new_version=None,
        description="Fix"
    )
    
    monitor = MonitorAgent(strict_mode=False)
    result = monitor.monitor_extraction(extracted_info)
    
    print(result)
    print(f"Valid: {result.is_valid}\n")


def test_batch_validation():
    """Test batch validation."""
    print("Test 6: Batch validation")
    print("-" * 50)
    
    extracted_infos = [
        ExtractedInfo(
            requestor_name="Developer 1",
            date=datetime.now(),
            new_version="1.0.0",
            description="First valid extraction"
        ),
        ExtractedInfo(
            requestor_name="",
            date=datetime.now(),
            new_version="2.0.0",
            description="Second extraction with empty requestor"
        ),
        ExtractedInfo(
            requestor_name="Developer 3",
            date=datetime.now(),
            new_version=None,
            description="Third valid extraction without version"
        )
    ]
    
    monitor = MonitorAgent(strict_mode=False)
    results = monitor.validate_batch(extracted_infos)
    
    for i, result in enumerate(results, 1):
        print(f"Extraction {i}: {'VALID' if result.is_valid else 'INVALID'}")
        if result.errors:
            print(f"  Errors: {', '.join(result.errors)}")
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
    
    print("\nSummary:")
    summary = monitor.get_validation_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("MONITORING AGENT TESTS")
    print("=" * 50 + "\n")
    
    test_valid_extraction()
    test_empty_requestor()
    test_empty_description()
    test_missing_date()
    test_short_description()
    test_batch_validation()
    
    print("=" * 50)
    print("ALL TESTS COMPLETED")
    print("=" * 50)
