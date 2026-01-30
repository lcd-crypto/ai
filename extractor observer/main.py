"""
Main entry point for the observer agent.
"""
import sys
import json
import argparse
from datetime import datetime
from models import ExtractedData
from observer_agent import ObserverAgent


def main():
    """Main function to run the observer agent."""
    parser = argparse.ArgumentParser(
        description="Observe and validate data extraction from the extractor agent"
    )
    
    parser.add_argument(
        "--repo-owner",
        type=str,
        required=True,
        help="Repository owner name"
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
        "--version-change",
        type=str,
        default=None,
        help="Version change (e.g., '1.2.3 -> 2.0.0')"
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (raises exceptions on validation failure)"
    )
    
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Disable strict mode"
    )
    
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Enable AI-powered validation"
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
    
    parser.add_argument(
        "--report-format",
        choices=["text", "json", "html"],
        default="text",
        help="Report format when validation fails"
    )
    
    parser.add_argument(
        "--no-reports",
        action="store_true",
        help="Disable report generation"
    )
    
    parser.add_argument(
        "--generate-summary-report",
        action="store_true",
        help="Generate summary report of all validations"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum number of retry attempts (default: 2)"
    )
    
    parser.add_argument(
        "--no-retry",
        action="store_true",
        help="Disable retry functionality"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse date
        date = datetime.fromisoformat(args.date)
        
        # Create extracted data object
        extracted_data = ExtractedData(
            repo_owner=args.repo_owner,
            date=date,
            version_change=args.version_change,
            description=args.description
        )
        
        # Determine strict mode
        strict_mode = args.strict if args.strict else (not args.no_strict)
        
        # Create observer agent
        max_retries = 0 if args.no_retry else args.max_retries
        observer = ObserverAgent(
            strict_mode=strict_mode,
            use_ai=args.ai,
            generate_reports=not args.no_reports,
            max_retries=max_retries
        )
        
        # Observe and validate
        try:
            result = observer.observe_extraction(extracted_data)
            
            if args.output == "json":
                output = {
                    "is_valid": result.is_valid,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "extracted_data": {
                        "repo_owner": extracted_data.repo_owner,
                        "date": extracted_data.date.isoformat(),
                        "version_change": extracted_data.version_change,
                        "description": extracted_data.description
                    }
                }
                print(json.dumps(output, indent=2))
            else:
                print("\n" + "="*50)
                print("OBSERVATION RESULT")
                print("="*50)
                print(str(result))
                print("="*50 + "\n")
            
            if args.summary:
                summary = observer.get_validation_summary()
                print("\n" + "="*50)
                print("VALIDATION SUMMARY")
                print("="*50)
                for key, value in summary.items():
                    print(f"{key}: {value}")
                print("="*50 + "\n")
            
            # Generate summary report if requested
            if args.generate_summary_report:
                summary_report_path = observer.generate_summary_report(format=args.report_format)
                if summary_report_path:
                    print(f"\nSummary report generated: {summary_report_path}")
                else:
                    print("\nNo failed validations to report.")
            
            return 0 if result.is_valid else 1
        
        except ValueError as e:
            print(f"Validation Error: {e}", file=sys.stderr)
            return 1
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
