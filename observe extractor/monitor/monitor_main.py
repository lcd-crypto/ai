"""
Main entry point for the monitoring agent.
"""
import sys
import json
import argparse
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ExtractedInfo
from monitor.monitor_agent import MonitorAgent
from monitor.validators import ValidationError


def main():
    """Main function to run the monitoring agent."""
    parser = argparse.ArgumentParser(
        description="Monitor and validate data extraction accuracy"
    )
    
    parser.add_argument(
        "--requestor",
        type=str,
        required=True,
        help="Requestor name"
    )
    
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date in ISO format (YYYY-MM-DDTHH:MM:SS)"
    )
    
    parser.add_argument(
        "--description",
        type=str,
        required=True,
        help="Description of change"
    )
    
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="New version (optional)"
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (raises exceptions on validation failure)"
    )
    
    parser.add_argument(
        "--output",
        choices=["json", "pretty"],
        default="pretty",
        help="Output format"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show validation summary"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse date
        date = datetime.fromisoformat(args.date)
        
        # Create extracted info object
        extracted_info = ExtractedInfo(
            requestor_name=args.requestor,
            date=date,
            new_version=args.version,
            description=args.description
        )
        
        # Create monitor agent
        monitor = MonitorAgent(strict_mode=args.strict)
        
        # Validate
        try:
            result = monitor.monitor_extraction(extracted_info)
            
            if args.output == "json":
                output = {
                    "is_valid": result.is_valid,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "extracted_data": {
                        "requestor_name": extracted_info.requestor_name,
                        "date": extracted_info.date.isoformat(),
                        "new_version": extracted_info.new_version,
                        "description": extracted_info.description
                    }
                }
                print(json.dumps(output, indent=2))
            else:
                print("\n" + "="*50)
                print("VALIDATION RESULT")
                print("="*50)
                print(str(result))
                print("="*50 + "\n")
            
            if args.summary:
                summary = monitor.get_validation_summary()
                print("\n" + "="*50)
                print("VALIDATION SUMMARY")
                print("="*50)
                for key, value in summary.items():
                    print(f"{key}: {value}")
                print("="*50 + "\n")
            
            return 0 if result.is_valid else 1
        
        except ValidationError as e:
            print(f"Validation Error: {e}", file=sys.stderr)
            return 1
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
