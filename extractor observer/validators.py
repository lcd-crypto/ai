"""
Validators for extracted data from the extractor agent.
"""
from typing import List
from datetime import datetime, timedelta
import re
from models import ExtractedData, ValidationResult


class DataValidator:
    """Validator for extracted data from the extractor agent."""
    
    @staticmethod
    def validate_extracted_data(extracted_data: ExtractedData) -> ValidationResult:
        """
        Validate that extracted data is complete and valid.
        
        Main check: No data extracted can be empty or invalid.
        
        Args:
            extracted_data: The extracted data to validate
            
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []
        
        # Check repo_owner - REQUIRED, cannot be empty
        if not extracted_data.repo_owner or not extracted_data.repo_owner.strip():
            errors.append("Repository owner is empty or missing")
        elif len(extracted_data.repo_owner.strip()) < 2:
            warnings.append("Repository owner is very short (less than 2 characters)")
        elif not any(c.isalpha() for c in extracted_data.repo_owner):
            warnings.append("Repository owner contains no alphabetic characters")
        
        # Check date - REQUIRED, cannot be empty or invalid
        if not extracted_data.date:
            errors.append("Date is missing")
        else:
            # Validate date is reasonable
            now = datetime.now()
            if extracted_data.date > now:
                warnings.append(f"Date is in the future: {extracted_data.date}")
            # Check if date is too old (more than 100 years)
            if extracted_data.date < now - timedelta(days=36500):
                warnings.append(f"Date is very old: {extracted_data.date}")
        
        # Check description - REQUIRED, cannot be empty
        if not extracted_data.description or not extracted_data.description.strip():
            errors.append("Description is empty or missing")
        elif len(extracted_data.description.strip()) < 10:
            warnings.append("Description is very short (less than 10 characters)")
        elif len(extracted_data.description.strip()) > 10000:
            warnings.append("Description is very long (more than 10000 characters)")
        
        # Check version_change - OPTIONAL, but if present should be valid format
        if extracted_data.version_change is not None:
            if not extracted_data.version_change.strip():
                errors.append("Version change is specified but empty")
            else:
                # Validate version change format
                version_str = extracted_data.version_change.strip()
                
                # Check for version change patterns: "1.2.3 -> 2.0.0" or single version "1.2.3"
                if "->" in version_str or "→" in version_str:
                    # Version change format
                    parts = re.split(r'[-→>]', version_str)
                    if len(parts) != 2:
                        warnings.append(f"Version change format may be invalid: {version_str}")
                    else:
                        old_version = parts[0].strip()
                        new_version = parts[1].strip()
                        if not DataValidator._is_valid_version_format(old_version):
                            warnings.append(f"Old version format may be invalid: {old_version}")
                        if not DataValidator._is_valid_version_format(new_version):
                            warnings.append(f"New version format may be invalid: {new_version}")
                else:
                    # Single version
                    if not DataValidator._is_valid_version_format(version_str):
                        warnings.append(f"Version format may be invalid: {version_str}")
        
        # Additional quality checks
        if extracted_data.description:
            desc_lower = extracted_data.description.lower()
            # Check for placeholder text
            placeholder_indicators = ["todo", "fixme", "placeholder", "example", "test", "n/a", "none"]
            for indicator in placeholder_indicators:
                if indicator in desc_lower and len(extracted_data.description.strip()) < 50:
                    warnings.append(f"Description may contain placeholder text: '{indicator}'")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def _is_valid_version_format(version: str) -> bool:
        """Check if version string matches valid format (X.Y.Z or X.Y)."""
        # Remove 'v' prefix if present
        version = version.strip().lstrip('vV')
        # Check format: X.Y.Z or X.Y
        pattern = r'^\d+\.\d+(\.\d+)?$'
        return bool(re.match(pattern, version))
    
    @staticmethod
    def validate_completeness(extracted_data: ExtractedData) -> ValidationResult:
        """
        Validate that all required fields are present and non-empty.
        
        Args:
            extracted_data: The extracted data to validate
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        
        # Required fields that cannot be empty
        required_fields = {
            "repo_owner": extracted_data.repo_owner,
            "date": extracted_data.date,
            "description": extracted_data.description
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
