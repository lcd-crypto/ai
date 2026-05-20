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
        self.strict_mode = strict_mode if strict_mode is not None else Config.STRICT_MODE
        self.use_ai = use_ai and Config.ENABLE_AI_VALIDATION
        self.generate_reports = generate_reports
        self.max_retries = max_retries
        self.validator = DataValidator()
        self.validation_history: List[Dict[str, Any]] = []
        self.report_generator = ReportGenerator() if generate_reports else None
        self.retry_handler = RetryHandler(max_retries=self.max_retries)

        # Always initialise an OpenAI client — used for diagnosis even when
        # use_ai (AI validation) is disabled.
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Set it in .env file.")
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.temperature = Config.OPENAI_TEMPERATURE

    # ------------------------------------------------------------------
    # Core validation pipeline
    # ------------------------------------------------------------------

    def _run_validation(self, extracted_data: ExtractedData) -> ValidationResult:
        """Shared validation pipeline used by all observe methods."""
        completeness_result = self.validator.validate_completeness(extracted_data)
        validation_result = self.validator.validate_extracted_data(extracted_data)

        all_errors = completeness_result.errors + validation_result.errors
        all_warnings = completeness_result.warnings + validation_result.warnings
        is_valid = completeness_result.is_valid and validation_result.is_valid

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
        Observe and validate extracted data.

        Args:
            extracted_data: The extracted data to validate.
            source_context: Optional context about the source.
            _generate_report: Set False during retries to suppress premature reports.

        Returns:
            ValidationResult with validation status.
        """
        combined_result = self._run_validation(extracted_data)
        self._record_validation(extracted_data, combined_result, source_context)

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
            raise ValueError(f"Validation failed: {', '.join(combined_result.errors)}")

        return combined_result

    # ------------------------------------------------------------------
    # Diagnose-and-repair retry loop  ← KEY CHANGE
    # ------------------------------------------------------------------

    def observe_with_retry(
        self,
        extractor_func: Callable,
        extractor_args: Dict[str, Any],
        source_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ExtractedData, ValidationResult, int]:
        """
        Run extraction → validate → diagnose failure → retry with repair hint.

        On each failed attempt the observer asks the LLM to diagnose WHY the
        extraction failed and produces a repair_hint.  That hint is passed back
        into extractor_func on the next attempt so the agentic extractor can
        change its tool-call strategy rather than blindly repeating itself.

        Args:
            extractor_func: Callable that accepts repair_hint=None and returns
                            an ExtractedInfo-compatible object.
            extractor_args: Base keyword arguments for extractor_func.
            source_context: Optional metadata about the source (for reports).

        Returns:
            Tuple of (extracted_data, validation_result, attempts_made).
        """
        repair_hint = None
        last_extracted = None
        last_result = None

        for attempt in range(self.max_retries + 1):
            # Build call args — inject repair_hint on retry attempts
            call_args = {**extractor_args}
            if repair_hint:
                call_args["repair_hint"] = repair_hint
                print(f"\n[Observer] Retry {attempt} — diagnosis passed to extractor:\n"
                      f"  → {repair_hint[:120]}{'...' if len(repair_hint) > 120 else ''}\n")

            # Run extraction
            raw_result = extractor_func(**call_args)

            # Convert ExtractedInfo → ExtractedData for the observer
            extracted_data = self._to_extracted_data(raw_result)
            last_extracted = extracted_data

            # Validate — suppress report during mid-loop attempts
            is_final_attempt = attempt == self.max_retries
            validation_result = self.observe_extraction(
                extracted_data,
                source_context=source_context,
                _generate_report=False  # always suppress here; we emit below
            )
            last_result = validation_result

            if validation_result.is_valid:
                print(f"[Observer] ✅ Validation passed on attempt {attempt + 1}")
                return extracted_data, validation_result, attempt

            print(f"[Observer] ❌ Attempt {attempt + 1} failed — "
                  f"errors: {', '.join(validation_result.errors)}")

            if not is_final_attempt:
                # Ask LLM to diagnose before next attempt
                repair_hint = self._diagnose_failure(
                    bad_result=raw_result,
                    validation_errors=validation_result.errors,
                    source_context=source_context or {}
                )

        # All retries exhausted — emit one final report
        if self.generate_reports and self.report_generator and last_extracted and last_result:
            final_context = (source_context or {}).copy()
            final_context.update({
                "retry_count": self.max_retries,
                "max_retries": self.max_retries,
                "retry_exhausted": True
            })
            report_path = self.report_generator.generate_report(
                extracted_data=last_extracted,
                validation_result=last_result,
                source_context=final_context,
                format="text"
            )
            if report_path:
                print(f"\n⚠️  All {self.max_retries} retry attempts exhausted. "
                      f"Report generated: {report_path}")

        return last_extracted, last_result, self.max_retries

    def _diagnose_failure(
        self,
        bad_result,
        validation_errors: List[str],
        source_context: Dict[str, Any]
    ) -> str:
        """
        Ask the LLM to diagnose why extraction failed and suggest a repair.

        Returns a short, concrete instruction for the extractor to use on
        its next attempt — e.g. which tool to call, which file to look at.
        """
        import json

        prompt = f"""An extraction pipeline produced invalid output. Diagnose the root cause
and return a SHORT, concrete instruction (2-3 sentences) telling the extractor
what to do differently on its next attempt.

Failed extraction:
- repo_owner: {getattr(bad_result, 'repo_owner', None)!r}
- version_change: {getattr(bad_result, 'version_change', None)!r}
- description: {getattr(bad_result, 'description', None)!r}

Validation errors: {validation_errors}
Source context: {json.dumps(source_context, default=str)}

Be specific: name alternative sources (diff, changelog, PR body) or patterns
to look for. Do NOT repeat the error messages verbatim."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a debugging agent for LLM extraction pipelines. "
                            "Be terse and actionable. Return plain text, no JSON."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Observer] Diagnosis call failed: {e}")
            return "Retry with a different extraction strategy — check the diff and changelog."

    def _to_extracted_data(self, raw_result) -> ExtractedData:
        """Convert ExtractedInfo (extractor model) → ExtractedData (observer model)."""
        return ExtractedData(
            repo_owner=raw_result.repo_owner,
            date=raw_result.date,
            version_change=raw_result.version_change,
            description=raw_result.description,
        )

    def _validate_for_retry(self, extracted_data: ExtractedData) -> ValidationResult:
        """Kept for backward compatibility with RetryHandler (no longer used internally)."""
        return self.observe_extraction(
            extracted_data,
            source_context=None,
            _generate_report=False
        )

    # ------------------------------------------------------------------
    # AI validation
    # ------------------------------------------------------------------

    def _ai_validate(self, extracted_data: ExtractedData) -> Optional[Dict[str, Any]]:
        """Use AI for additional validation checks."""
        try:
            import json
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
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"AI validation failed: {e}")
            return None

    # ------------------------------------------------------------------
    # History and reporting
    # ------------------------------------------------------------------

    def _record_validation(
        self,
        extracted_data: ExtractedData,
        result: ValidationResult,
        source_context: Optional[Dict[str, Any]]
    ):
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
        if not self.validation_history:
            return {"total_validations": 0, "passed": 0, "failed": 0,
                    "total_errors": 0, "total_warnings": 0}

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
        return [v for v in self.validation_history if not v["is_valid"]]

    def generate_summary_report(self, format: str = "text") -> Optional[str]:
        if not self.generate_reports or not self.report_generator:
            return None
        failed_validations = self.get_failed_validations()
        if not failed_validations:
            return None
        return self.report_generator.generate_summary_report(
            failed_validations=failed_validations,
            summary_stats=self.get_validation_summary(),
            format=format
        )

    def clear_history(self):
        self.validation_history.clear()

    def observe_batch(
        self,
        extracted_data_list: List[ExtractedData],
        source_contexts: Optional[List[Dict[str, Any]]] = None,
        strict_mode_override: Optional[bool] = None
    ) -> List[ValidationResult]:
        if source_contexts is None:
            source_contexts = [None] * len(extracted_data_list)

        effective_strict = strict_mode_override if strict_mode_override is not None else self.strict_mode
        original_strict = self.strict_mode
        self.strict_mode = effective_strict

        results = []
        try:
            for extracted_data, context in zip(extracted_data_list, source_contexts):
                try:
                    result = self.observe_extraction(extracted_data, context)
                    results.append(result)
                except ValueError as e:
                    results.append(ValidationResult(is_valid=False, errors=[str(e)], warnings=[]))
                    if effective_strict:
                        raise
        finally:
            self.strict_mode = original_strict

        return results
