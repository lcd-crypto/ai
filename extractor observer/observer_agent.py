"""
Observer agent for monitoring and validating extractor agent output.
"""
from typing import List, Optional, Dict, Any, Callable, Tuple
from datetime import datetime
from openai import OpenAI
from models import ExtractedData, ValidationResult
from validators import DataValidator
from config import Config
from reporter import ReportGenerator
from retry_handler import RetryHandler


class ObserverAgent:
    """Agent that observes and validates data extraction from the extractor agent."""
    
    def __init__(self, strict_mode: bool = None, use_ai: bool = False, generate_reports: bool = True, max_retries: int = 2):
        """
        Initialize the observer agent.
        
        Args:
            strict_mode: If True, raises exceptions on validation failures.
                        If None, uses Config.STRICT_MODE
            use_ai: If True, uses AI for additional validation checks
            generate_reports: If True, generates reports when validation fails
            max_retries: Maximum number of retry attempts for extractor (default: 2)
        """
        self.strict_mode = strict_mode if strict_mode is not None else Config.STRICT_MODE
        self.use_ai = use_ai and Config.ENABLE_AI_VALIDATION
        self.generate_reports = generate_reports
        self.max_retries = max_retries if max_retries is not None else Config.MAX_RETRIES
        self.validator = DataValidator()
        self.validation_history: List[Dict[str, Any]] = []
        self.report_generator = ReportGenerator() if generate_reports else None
        self.retry_handler = RetryHandler(max_retries=self.max_retries)
        
        if self.use_ai:
            if not Config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for AI validation. Set it in .env file.")
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
            self.model = Config.OPENAI_MODEL
            self.temperature = Config.OPENAI_TEMPERATURE
    
    def observe_extraction(
        self,
        extracted_data: ExtractedData,
        source_context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Observe and validate extracted data from the extractor agent.
        
        Main check: No data extracted can be empty or invalid.
        
        Args:
            extracted_data: The extracted data to validate
            source_context: Optional context about the source
            
        Returns:
            ValidationResult with validation status
            
        Raises:
            ValueError: If strict_mode is True and validation fails
        """
        # Run completeness validation first
        completeness_result = self.validator.validate_completeness(extracted_data)
        
        # Run full validation
        validation_result = self.validator.validate_extracted_data(extracted_data)
        
        # Combine results
        all_errors = completeness_result.errors + validation_result.errors
        all_warnings = completeness_result.warnings + validation_result.warnings
        
        is_valid = completeness_result.is_valid and validation_result.is_valid
        
        # AI-powered validation if enabled
        if self.use_ai and is_valid:
            ai_result = self._ai_validate(extracted_data)
            if ai_result:
                all_warnings.extend(ai_result.get("warnings", []))
                if not ai_result.get("is_valid", True):
                    all_errors.extend(ai_result.get("errors", []))
                    is_valid = False
        
        combined_result = ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings
        )
        
        # Record validation in history
        self._record_validation(extracted_data, combined_result, source_context)
        
        # Generate report if validation failed and reporting is enabled
        # Note: Reports are only generated after retries are exhausted (handled in observe_with_retry)
        if not is_valid and self.generate_reports and self.report_generator:
            # Check if this is after retries (retry_count will be in source_context if set)
            retry_count = source_context.get('retry_count', 0) if source_context else 0
            if retry_count >= self.max_retries:
                report_path = self.report_generator.generate_report(
                    extracted_data=extracted_data,
                    validation_result=combined_result,
                    source_context=source_context,
                    format="text"
                )
                if report_path:
                    print(f"Report generated after {retry_count} retries: {report_path}")
        
        # Raise exception if strict mode and validation failed
        if self.strict_mode and not is_valid:
            error_msg = f"Validation failed: {', '.join(all_errors)}"
            raise ValueError(error_msg)
        
        return combined_result
    
    def _ai_validate(self, extracted_data: ExtractedData) -> Optional[Dict[str, Any]]:
        """
        Use AI to perform additional validation checks.
        
        Args:
            extracted_data: The extracted data to validate
            
        Returns:
            Dictionary with AI validation results or None
        """
        try:
            prompt = f"""Validate the following extracted data from a software repository:

Repository Owner: {extracted_data.repo_owner}
Date: {extracted_data.date.isoformat()}
Version Change: {extracted_data.version_change or 'Not specified'}
Description: {extracted_data.description}

Check for:
1. Logical inconsistencies
2. Unrealistic or suspicious values
3. Missing critical information
4. Data quality issues

Respond in JSON format:
{{
    "is_valid": true/false,
    "errors": ["list of errors if any"],
    "warnings": ["list of warnings if any"]
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at validating software development data. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI validation failed: {e}")
            return None
    
    def _record_validation(
        self,
        extracted_data: ExtractedData,
        result: ValidationResult,
        source_context: Optional[Dict[str, Any]]
    ):
        """Record validation result in history."""
        self.validation_history.append({
            "timestamp": datetime.now(),
            "repo_owner": extracted_data.repo_owner,
            "date": extracted_data.date,
            "version_change": extracted_data.version_change,
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
    
    def observe_with_retry(
        self,
        extractor_func: Callable,
        extractor_args: Dict[str, Any],
        source_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ExtractedData, ValidationResult, int]:
        """
        Observe extraction with automatic retry if validation fails.
        
        This method instructs the extractor agent to rerun up to max_retries times
        if validation conditions are not met. Reports are only generated after all
        retries are exhausted.
        
        Args:
            extractor_func: The extractor function to call (e.g., extractor.extract_from_commit)
            extractor_args: Arguments to pass to the extractor function
            source_context: Optional context about the source
            
        Returns:
            Tuple of (extracted_data, validation_result, retry_count)
        """
        # Prepare validation function
        def validate_data(data: ExtractedData) -> ValidationResult:
            return self.observe_extraction(data, source_context)
        
        # Execute with retry
        extracted_data, validation_result, retry_count = self.retry_handler.execute_with_retry(
            extractor_func=extractor_func,
            extractor_args=extractor_args,
            validation_func=self._validate_for_retry,
            context=source_context
        )
        
        # If still invalid after retries, generate report
        if not validation_result.is_valid and retry_count >= self.max_retries:
            if self.generate_reports and self.report_generator:
                # Update context with retry information
                retry_context = source_context.copy() if source_context else {}
                retry_context['retry_count'] = retry_count
                retry_context['max_retries'] = self.max_retries
                retry_context['retry_exhausted'] = True
                
                report_path = self.report_generator.generate_report(
                    extracted_data=extracted_data,
                    validation_result=validation_result,
                    source_context=retry_context,
                    format="text"
                )
                if report_path:
                    print(f"\n⚠️  All retry attempts exhausted. Report generated: {report_path}")
        
        return extracted_data, validation_result, retry_count
    
    def _validate_for_retry(self, extracted_data: ExtractedData) -> ValidationResult:
        """
        Internal validation method for retry handler.
        Does not generate reports or raise exceptions.
        
        Args:
            extracted_data: The extracted data to validate
            
        Returns:
            ValidationResult
        """
        # Run completeness validation first
        completeness_result = self.validator.validate_completeness(extracted_data)
        
        # Run full validation
        validation_result = self.validator.validate_extracted_data(extracted_data)
        
        # Combine results
        all_errors = completeness_result.errors + validation_result.errors
        all_warnings = completeness_result.warnings + validation_result.warnings
        
        is_valid = completeness_result.is_valid and validation_result.is_valid
        
        # AI-powered validation if enabled
        if self.use_ai and is_valid:
            ai_result = self._ai_validate(extracted_data)
            if ai_result:
                all_warnings.extend(ai_result.get("warnings", []))
                if not ai_result.get("is_valid", True):
                    all_errors.extend(ai_result.get("errors", []))
                    is_valid = False
        
        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings
        )
    
    def generate_summary_report(self, format: str = "text") -> Optional[str]:
        """
        Generate a summary report of all failed validations.
        
        Args:
            format: Report format ('text', 'json', 'html')
            
        Returns:
            Path to the generated report file, or None if no failures
        """
        if not self.generate_reports or not self.report_generator:
            return None
        
        failed_validations = self.get_failed_validations()
        if not failed_validations:
            return None
        
        summary_stats = self.get_validation_summary()
        
        return self.report_generator.generate_summary_report(
            failed_validations=failed_validations,
            summary_stats=summary_stats,
            format=format
        )
    
    def clear_history(self):
        """Clear validation history."""
        self.validation_history.clear()
    
    def observe_batch(
        self,
        extracted_data_list: List[ExtractedData],
        source_contexts: Optional[List[Dict[str, Any]]] = None
    ) -> List[ValidationResult]:
        """
        Observe and validate multiple extractions in batch.
        
        Args:
            extracted_data_list: List of extracted data to validate
            source_contexts: Optional list of source contexts (one per extraction)
            
        Returns:
            List of ValidationResult objects
        """
        if source_contexts is None:
            source_contexts = [None] * len(extracted_data_list)
        
        results = []
        for extracted_data, context in zip(extracted_data_list, source_contexts):
            try:
                result = self.observe_extraction(extracted_data, context)
                results.append(result)
            except ValueError as e:
                # In strict mode, exception is raised, but we catch it here for batch processing
                failed_result = ValidationResult(
                    is_valid=False,
                    errors=[str(e)],
                    warnings=[]
                )
                results.append(failed_result)
        
        return results
