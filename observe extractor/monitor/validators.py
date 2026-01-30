"""
Validators for extracted data accuracy and completeness.
"""
from typing import List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ExtractedInfo


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class ValidationResult:
    """Result of validation check."""
    
    def __init__(
        self,
        is_valid: bool,
        errors: List[str],
        warnings: List[str] = None
    ):
        """
        Initialize validation result.
        
        Args:
            is_valid: Whether the validation passed
            errors: List of error messages
            warnings: List of warning messages
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def __bool__(self):
        """Return True if validation passed."""
        return self.is_valid
    
    def __str__(self):
        """String representation of validation result."""
        status = "VALID" if self.is_valid else "INVALID"
        result = f"Validation Status: {status}\n"
        
        if self.errors:
            result += f"Errors ({len(self.errors)}):\n"
            for error in self.errors:
                result += f"  - {error}\n"
        
        if self.warnings:
            result += f"Warnings ({len(self.warnings)}):\n"
            for warning in self.warnings:
                result += f"  - {warning}\n"
        
        return result.strip()


class DataValidator:
    """Validator for extracted data."""
    
    @staticmethod
    def validate_extracted_info(extracted_info: ExtractedInfo) -> ValidationResult:
        """
        Validate that extracted information is complete and accurate.
        
        Main check: No data extracted can be empty (except new_version which is optional).
        
        Args:
            extracted_info: The extracted information to validate
            
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []
        
        # Check requestor_name - REQUIRED, cannot be empty
        if not extracted_info.requestor_name or not extracted_info.requestor_name.strip():
            errors.append("Requestor name is empty or missing")
        elif len(extracted_info.requestor_name.strip()) < 2:
            warnings.append("Requestor name is very short (less than 2 characters)")
        
        # Check date - REQUIRED, cannot be empty
        if not extracted_info.date:
            errors.append("Date is missing")
        else:
            # Validate date is reasonable (not too far in future/past)
            now = datetime.now()
            if extracted_info.date > now:
                warnings.append(f"Date is in the future: {extracted_info.date}")
            # Check if date is too old (more than 100 years)
            from datetime import timedelta
            if extracted_info.date < now - timedelta(days=36500):
                warnings.append(f"Date is very old: {extracted_info.date}")
        
        # Check description - REQUIRED, cannot be empty
        if not extracted_info.description or not extracted_info.description.strip():
            errors.append("Description is empty or missing")
        elif len(extracted_info.description.strip()) < 10:
            warnings.append("Description is very short (less than 10 characters)")
        
        # Check new_version - OPTIONAL, but if present should be valid format
        if extracted_info.new_version is not None:
            if not extracted_info.new_version.strip():
                errors.append("New version is specified but empty")
            else:
                # Validate version format (should be X.Y.Z or X.Y)
                import re
                version_pattern = r'^\d+\.\d+(\.\d+)?$'
                if not re.match(version_pattern, extracted_info.new_version.strip()):
                    warnings.append(f"Version format may be invalid: {extracted_info.new_version}")
        
        # Additional quality checks
        if extracted_info.description:
            # Check for placeholder text
            placeholder_indicators = ["TODO", "FIXME", "placeholder", "example", "test"]
            desc_lower = extracted_info.description.lower()
            for indicator in placeholder_indicators:
                if indicator in desc_lower and len(extracted_info.description.strip()) < 50:
                    warnings.append(f"Description may contain placeholder text: '{indicator}'")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_completeness(extracted_info: ExtractedInfo) -> ValidationResult:
        """
        Validate that all required fields are present and non-empty.
        
        Args:
            extracted_info: The extracted information to validate
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        
        # Required fields that cannot be empty
        required_fields = {
            "requestor_name": extracted_info.requestor_name,
            "date": extracted_info.date,
            "description": extracted_info.description
        }
        
        for field_name, field_value in required_fields.items():
            if field_value is None:
                errors.append(f"{field_name} is None")
            elif isinstance(field_value, str) and not field_value.strip():
                errors.append(f"{field_name} is empty")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors
        )
    
    @staticmethod
    def validate_data_quality(extracted_info: ExtractedInfo) -> ValidationResult:
        """
        Validate data quality and accuracy.
        
        Args:
            extracted_info: The extracted information to validate
            
        Returns:
            ValidationResult with warnings about data quality
        """
        warnings = []
        
        # Check description quality
        if extracted_info.description:
            desc = extracted_info.description.strip()
            
            # Too short
            if len(desc) < 20:
                warnings.append("Description is very short and may lack detail")
            
            # Too long (might be copy-paste error)
            if len(desc) > 5000:
                warnings.append("Description is very long and may contain unnecessary content")
            
            # Check for common issues
            if desc.lower() == "none" or desc.lower() == "n/a":
                warnings.append("Description appears to be a placeholder")
        
        # Check requestor name format
        if extracted_info.requestor_name:
            name = extracted_info.requestor_name.strip()
            # Should not be just numbers or special characters
            if name.isdigit():
                warnings.append("Requestor name appears to be only numbers")
            elif not any(c.isalpha() for c in name):
                warnings.append("Requestor name contains no alphabetic characters")
        
        return ValidationResult(
            is_valid=True,  # Quality checks don't fail validation
            errors=[],
            warnings=warnings
        )
