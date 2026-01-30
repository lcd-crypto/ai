"""
Monitoring agent for data extraction accuracy.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ExtractedInfo
from .validators import DataValidator, ValidationResult, ValidationError


class MonitorAgent:
    """Agent that monitors and validates data extraction accuracy."""
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the monitoring agent.
        
        Args:
            strict_mode: If True, raises exceptions on validation failures.
                        If False, returns validation results without raising.
        """
        self.strict_mode = strict_mode
        self.validator = DataValidator()
        self.validation_history: List[Dict[str, Any]] = []
    
    def monitor_extraction(
        self,
        extracted_info: ExtractedInfo,
        source_context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Monitor and validate extracted information.
        
        Main check: No data extracted can be empty (except new_version which is optional).
        
        Args:
            extracted_info: The extracted information to validate
            source_context: Optional context about the source (e.g., commit SHA, PR number)
            
        Returns:
            ValidationResult with validation status
            
        Raises:
            ValidationError: If strict_mode is True and validation fails
        """
        # Run all validation checks
        completeness_result = self.validator.validate_completeness(extracted_info)
        accuracy_result = self.validator.validate_extracted_info(extracted_info)
        quality_result = self.validator.validate_data_quality(extracted_info)
        
        # Combine all results
        all_errors = completeness_result.errors + accuracy_result.errors
        all_warnings = (
            completeness_result.warnings +
            accuracy_result.warnings +
            quality_result.warnings
        )
        
        is_valid = completeness_result.is_valid and accuracy_result.is_valid
        
        combined_result = ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings
        )
        
        # Record validation in history
        self._record_validation(extracted_info, combined_result, source_context)
        
        # Raise exception if strict mode and validation failed
        if self.strict_mode and not is_valid:
            error_msg = f"Validation failed: {', '.join(all_errors)}"
            raise ValidationError(error_msg)
        
        return combined_result
    
    def _record_validation(
        self,
        extracted_info: ExtractedInfo,
        result: ValidationResult,
        source_context: Optional[Dict[str, Any]]
    ):
        """Record validation result in history."""
        self.validation_history.append({
            "timestamp": datetime.now(),
            "requestor": extracted_info.requestor_name,
            "date": extracted_info.date,
            "version": extracted_info.new_version,
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "source_context": source_context
        })
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all validations performed.
        
        Returns:
            Dictionary with validation statistics
        """
        if not self.validation_history:
            return {
                "total_validations": 0,
                "passed": 0,
                "failed": 0,
                "total_errors": 0,
                "total_warnings": 0
            }
        
        total = len(self.validation_history)
        passed = sum(1 for v in self.validation_history if v["is_valid"])
        failed = total - passed
        total_errors = sum(len(v["errors"]) for v in self.validation_history)
        total_warnings = sum(len(v["warnings"]) for v in self.validation_history)
        
        return {
            "total_validations": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "average_errors_per_validation": total_errors / total if total > 0 else 0,
            "average_warnings_per_validation": total_warnings / total if total > 0 else 0
        }
    
    def get_failed_validations(self) -> List[Dict[str, Any]]:
        """
        Get list of all failed validations.
        
        Returns:
            List of validation records that failed
        """
        return [v for v in self.validation_history if not v["is_valid"]]
    
    def clear_history(self):
        """Clear validation history."""
        self.validation_history.clear()
    
    def validate_batch(
        self,
        extracted_infos: List[ExtractedInfo],
        source_contexts: Optional[List[Dict[str, Any]]] = None
    ) -> List[ValidationResult]:
        """
        Validate multiple extractions in batch.
        
        Args:
            extracted_infos: List of extracted information to validate
            source_contexts: Optional list of source contexts (one per extraction)
            
        Returns:
            List of ValidationResult objects
        """
        if source_contexts is None:
            source_contexts = [None] * len(extracted_infos)
        
        results = []
        for extracted_info, context in zip(extracted_infos, source_contexts):
            try:
                result = self.monitor_extraction(extracted_info, context)
                results.append(result)
            except ValidationError as e:
                # In strict mode, exception is raised, but we catch it here for batch processing
                # Create a failed result
                failed_result = ValidationResult(
                    is_valid=False,
                    errors=[str(e)],
                    warnings=[]
                )
                results.append(failed_result)
        
        return results
