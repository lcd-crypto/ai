"""
Report generator for monitoring condition failures.
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from models import ExtractedData, ValidationResult


class ReportGenerator:
    """Generator for validation failure reports."""
    
    def __init__(self, reports_dir: str = "reports"):
        """
        Initialize the report generator.
        
        Args:
            reports_dir: Directory to store generated reports
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_report(
        self,
        extracted_data: ExtractedData,
        validation_result: ValidationResult,
        source_context: Optional[Dict[str, Any]] = None,
        format: str = "text"
    ) -> str:
        """
        Generate a report when monitoring conditions are not met.
        
        Args:
            extracted_data: The extracted data that failed validation
            validation_result: The validation result
            source_context: Optional context about the source
            format: Report format ('text', 'json', 'html')
            
        Returns:
            Path to the generated report file
        """
        if validation_result.is_valid:
            return None  # No report needed if validation passed
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_failure_{timestamp}.{format}"
        filepath = self.reports_dir / filename
        
        if format == "text":
            content = self._generate_text_report(extracted_data, validation_result, source_context)
        elif format == "json":
            content = self._generate_json_report(extracted_data, validation_result, source_context)
        elif format == "html":
            content = self._generate_html_report(extracted_data, validation_result, source_context)
        else:
            raise ValueError(f"Unsupported report format: {format}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
    
    def _generate_text_report(
        self,
        extracted_data: ExtractedData,
        validation_result: ValidationResult,
        source_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate a text format report."""
        report = []
        report.append("=" * 80)
        report.append("MONITORING CONDITION FAILURE REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("VALIDATION STATUS: FAILED")
        report.append("")
        
        report.append("-" * 80)
        report.append("EXTRACTED DATA")
        report.append("-" * 80)
        report.append(f"Repository Owner: {extracted_data.repo_owner}")
        report.append(f"Date: {extracted_data.date}")
        report.append(f"Version Change: {extracted_data.version_change or 'Not specified'}")
        report.append(f"Description: {extracted_data.description}")
        report.append("")
        
        if source_context:
            report.append("-" * 80)
            report.append("SOURCE CONTEXT")
            report.append("-" * 80)
            for key, value in source_context.items():
                report.append(f"{key}: {value}")
            report.append("")
        
        report.append("-" * 80)
        report.append("VALIDATION ERRORS")
        report.append("-" * 80)
        if validation_result.errors:
            for i, error in enumerate(validation_result.errors, 1):
                report.append(f"{i}. {error}")
        else:
            report.append("No errors found.")
        report.append("")
        
        if validation_result.warnings:
            report.append("-" * 80)
            report.append("VALIDATION WARNINGS")
            report.append("-" * 80)
            for i, warning in enumerate(validation_result.warnings, 1):
                report.append(f"{i}. {warning}")
            report.append("")
        
        report.append("-" * 80)
        report.append("RECOMMENDATIONS")
        report.append("-" * 80)
        report.append(self._generate_recommendations(validation_result))
        report.append("")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def _generate_json_report(
        self,
        extracted_data: ExtractedData,
        validation_result: ValidationResult,
        source_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate a JSON format report."""
        report_data = {
            "report_type": "monitoring_condition_failure",
            "generated_at": datetime.now().isoformat(),
            "validation_status": "failed",
            "extracted_data": {
                "repo_owner": extracted_data.repo_owner,
                "date": extracted_data.date.isoformat(),
                "version_change": extracted_data.version_change,
                "description": extracted_data.description
            },
            "source_context": source_context or {},
            "validation_result": {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings
            },
            "recommendations": self._generate_recommendations_list(validation_result)
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def _generate_html_report(
        self,
        extracted_data: ExtractedData,
        validation_result: ValidationResult,
        source_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate an HTML format report."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<title>Monitoring Condition Failure Report</title>")
        html.append("<style>")
        html.append("""
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #d32f2f; border-bottom: 3px solid #d32f2f; padding-bottom: 10px; }
            h2 { color: #1976d2; margin-top: 20px; }
            .status { background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 5px; font-weight: bold; }
            .section { margin: 20px 0; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #1976d2; }
            .error { color: #d32f2f; margin: 5px 0; }
            .warning { color: #f57c00; margin: 5px 0; }
            .data-item { margin: 5px 0; }
            .recommendations { background-color: #e3f2fd; padding: 15px; border-radius: 5px; }
            ul { margin: 10px 0; }
            li { margin: 5px 0; }
        """)
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        html.append("<div class='container'>")
        
        html.append("<h1>Monitoring Condition Failure Report</h1>")
        html.append(f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html.append("<div class='status'>VALIDATION STATUS: FAILED</div>")
        
        html.append("<h2>Extracted Data</h2>")
        html.append("<div class='section'>")
        html.append(f"<div class='data-item'><strong>Repository Owner:</strong> {extracted_data.repo_owner}</div>")
        html.append(f"<div class='data-item'><strong>Date:</strong> {extracted_data.date}</div>")
        html.append(f"<div class='data-item'><strong>Version Change:</strong> {extracted_data.version_change or 'Not specified'}</div>")
        html.append(f"<div class='data-item'><strong>Description:</strong> {extracted_data.description}</div>")
        html.append("</div>")
        
        if source_context:
            html.append("<h2>Source Context</h2>")
            html.append("<div class='section'>")
            for key, value in source_context.items():
                html.append(f"<div class='data-item'><strong>{key}:</strong> {value}</div>")
            html.append("</div>")
        
        html.append("<h2>Validation Errors</h2>")
        html.append("<div class='section'>")
        if validation_result.errors:
            html.append("<ul>")
            for error in validation_result.errors:
                html.append(f"<li class='error'>{error}</li>")
            html.append("</ul>")
        else:
            html.append("<p>No errors found.</p>")
        html.append("</div>")
        
        if validation_result.warnings:
            html.append("<h2>Validation Warnings</h2>")
            html.append("<div class='section'>")
            html.append("<ul>")
            for warning in validation_result.warnings:
                html.append(f"<li class='warning'>{warning}</li>")
            html.append("</ul>")
            html.append("</div>")
        
        html.append("<h2>Recommendations</h2>")
        html.append("<div class='recommendations'>")
        recommendations = self._generate_recommendations_list(validation_result)
        html.append("<ul>")
        for rec in recommendations:
            html.append(f"<li>{rec}</li>")
        html.append("</ul>")
        html.append("</div>")
        
        html.append("</div>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    def _generate_recommendations(self, validation_result: ValidationResult) -> str:
        """Generate recommendations text."""
        recommendations = self._generate_recommendations_list(validation_result)
        return "\n".join(f"- {rec}" for rec in recommendations)
    
    def _generate_recommendations_list(self, validation_result: ValidationResult) -> List[str]:
        """Generate list of recommendations based on errors."""
        recommendations = []
        
        for error in validation_result.errors:
            if "repository owner" in error.lower() or "repo_owner" in error.lower():
                recommendations.append("Ensure the repository owner field is provided and not empty")
            elif "date" in error.lower():
                recommendations.append("Ensure the date field is provided and valid")
            elif "description" in error.lower():
                recommendations.append("Ensure the description field is provided and contains meaningful content")
            elif "version change" in error.lower() or "version_change" in error.lower():
                recommendations.append("If version change is specified, ensure it follows the format 'X.Y.Z -> A.B.C' or 'X.Y.Z'")
        
        for warning in validation_result.warnings:
            if "short" in warning.lower():
                if "description" in warning.lower():
                    recommendations.append("Provide a more detailed description (at least 20 characters recommended)")
                elif "owner" in warning.lower():
                    recommendations.append("Verify the repository owner name is correct")
            elif "format" in warning.lower():
                recommendations.append("Verify the data format matches expected patterns")
            elif "placeholder" in warning.lower():
                recommendations.append("Replace placeholder text with actual content")
        
        if not recommendations:
            recommendations.append("Review the extracted data and ensure all required fields are properly populated")
        
        return recommendations
    
    def generate_summary_report(
        self,
        failed_validations: List[Dict[str, Any]],
        summary_stats: Dict[str, Any],
        format: str = "text"
    ) -> str:
        """
        Generate a summary report of all failed validations.
        
        Args:
            failed_validations: List of failed validation records
            summary_stats: Summary statistics
            format: Report format ('text', 'json', 'html')
            
        Returns:
            Path to the generated report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_report_{timestamp}.{format}"
        filepath = self.reports_dir / filename
        
        if format == "text":
            content = self._generate_summary_text(failed_validations, summary_stats)
        elif format == "json":
            content = self._generate_summary_json(failed_validations, summary_stats)
        elif format == "html":
            content = self._generate_summary_html(failed_validations, summary_stats)
        else:
            raise ValueError(f"Unsupported report format: {format}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
    
    def _generate_summary_text(
        self,
        failed_validations: List[Dict[str, Any]],
        summary_stats: Dict[str, Any]
    ) -> str:
        """Generate summary report in text format."""
        report = []
        report.append("=" * 80)
        report.append("MONITORING SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("-" * 80)
        report.append("SUMMARY STATISTICS")
        report.append("-" * 80)
        report.append(f"Total Validations: {summary_stats.get('total_validations', 0)}")
        report.append(f"Passed: {summary_stats.get('passed', 0)}")
        report.append(f"Failed: {summary_stats.get('failed', 0)}")
        report.append(f"Pass Rate: {summary_stats.get('pass_rate', 0):.2f}%")
        report.append(f"Total Errors: {summary_stats.get('total_errors', 0)}")
        report.append(f"Total Warnings: {summary_stats.get('total_warnings', 0)}")
        report.append("")
        
        if failed_validations:
            report.append("-" * 80)
            report.append("FAILED VALIDATIONS")
            report.append("-" * 80)
            for i, validation in enumerate(failed_validations, 1):
                report.append(f"\n{i}. Timestamp: {validation.get('timestamp', 'N/A')}")
                report.append(f"   Repository Owner: {validation.get('repo_owner', 'N/A')}")
                report.append(f"   Date: {validation.get('date', 'N/A')}")
                report.append(f"   Errors: {', '.join(validation.get('errors', []))}")
                if validation.get('warnings'):
                    report.append(f"   Warnings: {', '.join(validation.get('warnings', []))}")
        
        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def _generate_summary_json(
        self,
        failed_validations: List[Dict[str, Any]],
        summary_stats: Dict[str, Any]
    ) -> str:
        """Generate summary report in JSON format."""
        report_data = {
            "report_type": "monitoring_summary",
            "generated_at": datetime.now().isoformat(),
            "summary_statistics": summary_stats,
            "failed_validations": failed_validations
        }
        
        return json.dumps(report_data, indent=2, default=str, ensure_ascii=False)
    
    def _generate_summary_html(
        self,
        failed_validations: List[Dict[str, Any]],
        summary_stats: Dict[str, Any]
    ) -> str:
        """Generate summary report in HTML format."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<title>Monitoring Summary Report</title>")
        html.append("<style>")
        html.append("""
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #1976d2; border-bottom: 3px solid #1976d2; padding-bottom: 10px; }
            h2 { color: #1976d2; margin-top: 20px; }
            .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 20px 0; }
            .stat-item { background-color: #e3f2fd; padding: 15px; border-radius: 5px; }
            .stat-label { font-weight: bold; color: #1976d2; }
            .stat-value { font-size: 24px; color: #0d47a1; }
            .failed-item { background-color: #ffebee; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #d32f2f; }
            .error { color: #d32f2f; }
        """)
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        html.append("<div class='container'>")
        
        html.append("<h1>Monitoring Summary Report</h1>")
        html.append(f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        
        html.append("<h2>Summary Statistics</h2>")
        html.append("<div class='stats'>")
        html.append(f"<div class='stat-item'><div class='stat-label'>Total Validations</div><div class='stat-value'>{summary_stats.get('total_validations', 0)}</div></div>")
        html.append(f"<div class='stat-item'><div class='stat-label'>Passed</div><div class='stat-value'>{summary_stats.get('passed', 0)}</div></div>")
        html.append(f"<div class='stat-item'><div class='stat-label'>Failed</div><div class='stat-value'>{summary_stats.get('failed', 0)}</div></div>")
        html.append(f"<div class='stat-item'><div class='stat-label'>Pass Rate</div><div class='stat-value'>{summary_stats.get('pass_rate', 0):.2f}%</div></div>")
        html.append("</div>")
        
        if failed_validations:
            html.append("<h2>Failed Validations</h2>")
            for i, validation in enumerate(failed_validations, 1):
                html.append("<div class='failed-item'>")
                html.append(f"<h3>Failure #{i}</h3>")
                html.append(f"<p><strong>Timestamp:</strong> {validation.get('timestamp', 'N/A')}</p>")
                html.append(f"<p><strong>Repository Owner:</strong> {validation.get('repo_owner', 'N/A')}</p>")
                html.append(f"<p><strong>Date:</strong> {validation.get('date', 'N/A')}</p>")
                html.append("<p><strong>Errors:</strong></p>")
                html.append("<ul>")
                for error in validation.get('errors', []):
                    html.append(f"<li class='error'>{error}</li>")
                html.append("</ul>")
                html.append("</div>")
        
        html.append("</div>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
