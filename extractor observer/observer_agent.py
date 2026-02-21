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

    def __init__(
        self,
        strict_mode: bool = None,
        use_ai: bool = False,
        generate_reports: bool = True,
        max_retries: int = 2
    ):
        """
        Initialize the observer agent.

        Args:
            strict_mode: If True, raises exceptions on validation failures.
                         If None, uses Config.STRICT_MODE.
            use_ai: If True, uses AI for additional validation checks.
            generate_reports: If True, generates reports when validation fails.
            max_retries: Maximum number of retry attempts for extractor (default: 2).
        """
        self.strict_mode = strict_mode if strict_mode is not None else Config.STRICT_MODE
        self.use_ai = use_ai and Config.ENABLE_AI_VALIDATION
        self.generate_reports = generate_reports
        # FIX 7: Removed redundant None guard — type hint guarantees int
        self.max_retries = max_retries
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

    # ------------------------------------------------------------------
    # FIX 1: Extracted shared validation logic into one private method
    # ------------------------------------------------------------------
    def _run_validation(self, extracted_data: ExtractedData) -> ValidationResult:
        """
        Core validation pipeline shared by all observe methods.
        Runs completeness check, full validation, and optional AI validation.

        Args:
            extracted_data: The extracted data to validate.

        Returns:
            Combined ValidationResult.
        """
        completeness_result = self.validator.validate_completeness(extracted_data)
        validation_result = self.validator.validate_extracted_data(extracted_data)

        all_errors = completeness_result.errors + validation_result.errors
        all_warnings = completeness_result.warnings + validation_result.warnings
        is_valid = completeness_result.is_valid and validation_result.is_valid

        # FIX 5: AI validation now runs regardless of rule-based result,
        # so it can contribute additional error context on failures too.
        if self.use_ai:
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

    def observe_extraction(
        self,
        extracted_data: ExtractedData,
        source_context: Optional[Dict[str, Any]] = None,
        _generate_report: bool = True
    ) -> ValidationResult:
        """
        Observe and validate extracted data from the extractor agent.

        Main check: No data extracted can be empty or invalid.

        Args:
            extracted_data: The extracted data to validate.
            source_context: Optional context about the source.
            _generate_report: Internal flag — set to False during retries to
                              suppress premature report generation.

        Returns:
            ValidationResult with validation status.

        Raises:
            ValueError: If strict_mode is True and validation fails.
        """
        # FIX 1: Use shared validation pipeline
        combined_result = self._run_validation(extracted_data)

        # Record every call in history (FIX 3: retries now also record via this path)
        self._record_validation(extracted_data, combined_result, source_context)

        # FIX 2: Report generation is now controlled by the _generate_report flag,
        # not a fragile retry_count injected into source_context by the caller.
        # Reports are suppressed during retries and only emitted when truly final.
        if not combined_result.is_valid and self.generate_reports and self.report_generator and _generate_report:
            report_path = self.report_generator.generate_report(
                extracted_data=extracted_data,
                validation_result=combined_result,
                source_context=source_context,
                format="text"
            )
            if report_path:
                print(f"Report generated: {report_path}")

        if self.strict_mode and not combined_result.is_valid:
            error_msg = f"Validation failed: {', '.join(combined_result.errors)}"
            raise ValueError(error_msg)

        return combined_result

    def _ai_validate(self, extracted_data: ExtractedData) -> Optional[Dict[str, Any]]:
        """
        Use AI to perform additional validation checks.

        Args:
            extracted_data: The extracted data to validate.

        Returns:
            Dictionary with AI validation results or None.
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
            Dictionary with validation statistics.
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
            List of validation records that failed.
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

        Retries call observe_extraction() with report generation suppressed.
        A final report is only generated after all retries are exhausted.

        Args:
            extractor_func: The extractor function to call.
            extractor_args: Arguments to pass to the extractor function.
            source_context: Optional context about the source.

        Returns:
            Tuple of (extracted_data, validation_result, retry_count).
        """
        # FIX 3 & 6: Removed dead `validate_data` closure.
        # observe_extraction() is now used directly via _validate_for_retry,
        # which suppresses reports during retry attempts and records history properly.

        extracted_data, validation_result, retry_count = self.retry_handler.execute_with_retry(
            extractor_func=extractor_func,
            extractor_args=extractor_args,
            validation_func=self._validate_for_retry,
            context=source_context
        )

        # Generate final report only after all retries exhausted
        if not validation_result.is_valid and self.generate_reports and self.report_generator:
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
        Validation method used during retry cycles.

        FIX 1 & 3: Now delegates to observe_extraction() with report generation
        suppressed, ensuring history is recorded on every attempt without
        triggering premature reports.

        Args:
            extracted_data: The extracted data to validate.

        Returns:
            ValidationResult.
        """
        return self.observe_extraction(
            extracted_data,
            source_context=None,
            _generate_report=False  # Reports suppressed until retries exhausted
        )

    def generate_summary_report(self, format: str = "text") -> Optional[str]:
        """
        Generate a summary report of all failed validations.

        Args:
            format: Report format ('text', 'json', 'html').

        Returns:
            Path to the generated report file, or None if no failures.
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
        source_contexts: Optional[List[Dict[str, Any]]] = None,
        strict_mode_override: Optional[bool] = None
    ) -> List[ValidationResult]:
        """
        Observe and validate multiple extractions in batch.

        FIX 4: Added strict_mode_override parameter so callers can explicitly
        control strict mode behaviour in batch context rather than having it
        silently ignored.

        Args:
            extracted_data_list: List of extracted data to validate.
            source_contexts: Optional list of source contexts (one per extraction).
            strict_mode_override: If provided, overrides instance strict_mode for
                                  this batch. Pass False to suppress exceptions in
                                  batch; pass True to enforce them.

        Returns:
            List of ValidationResult objects.
        """
        if source_contexts is None:
            source_contexts = [None] * len(extracted_data_list)

        # Determine effective strict mode for this batch
        effective_strict = strict_mode_override if strict_mode_override is not None else self.strict_mode

        # Temporarily override strict_mode if needed
        original_strict = self.strict_mode
        self.strict_mode = effective_strict

        results = []
        try:
            for extracted_data, context in zip(extracted_data_list, source_contexts):
                try:
                    result = self.observe_extraction(extracted_data, context)
                    results.append(result)
                except ValueError as e:
                    # Only reached if strict_mode is True
                    failed_result = ValidationResult(
                        is_valid=False,
                        errors=[str(e)],
                        warnings=[]
                    )
                    results.append(failed_result)
                    if effective_strict:
                        # Re-raise immediately if strict mode is explicitly enforced in batch
                        raise
        finally:
            # Always restore original strict_mode
            self.strict_mode = original_strict

        return results
