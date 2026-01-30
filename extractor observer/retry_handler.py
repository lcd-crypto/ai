"""
Retry handler for extractor agent reruns when validation fails.
"""
from typing import Callable, Optional, Dict, Any, Tuple
from models import ExtractedData, ValidationResult
from validators import DataValidator


class RetryHandler:
    """Handler for retrying extractor agent operations when validation fails."""
    
    def __init__(self, max_retries: int = 2):
        """
        Initialize the retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts (default: 2)
        """
        self.max_retries = max_retries
        self.validator = DataValidator()
    
    def execute_with_retry(
        self,
        extractor_func: Callable,
        extractor_args: Dict[str, Any],
        validation_func: Callable[[ExtractedData], ValidationResult],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ExtractedData, ValidationResult, int]:
        """
        Execute extractor function with retry logic.
        
        Args:
            extractor_func: Function to call for extraction (e.g., extractor.extract_from_commit)
            extractor_args: Arguments to pass to extractor function
            validation_func: Function to validate extracted data
            context: Optional context for tracking
            
        Returns:
            Tuple of (extracted_data, validation_result, retry_count)
        """
        retry_count = 0
        last_result = None
        last_extracted_data = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                # Execute extraction
                extracted_info = extractor_func(**extractor_args)
                
                # Convert to ExtractedData model
                extracted_data = ExtractedData(
                    repo_owner=extracted_info.repo_owner,
                    date=extracted_info.date,
                    version_change=extracted_info.version_change,
                    description=extracted_info.description
                )
                
                # Validate
                validation_result = validation_func(extracted_data)
                
                # Store for potential retry
                last_result = validation_result
                last_extracted_data = extracted_data
                
                # If validation passes, return immediately
                if validation_result.is_valid:
                    return extracted_data, validation_result, retry_count
                
                # If validation fails and we have retries left, prepare for retry
                if attempt < self.max_retries:
                    retry_count += 1
                    print(f"Validation failed. Retrying extraction (attempt {retry_count}/{self.max_retries})...")
                    # Could add delay here if needed
                    continue
                else:
                    # No more retries, return failure
                    return extracted_data, validation_result, retry_count
                    
            except Exception as e:
                # If extraction fails, try again if retries available
                if attempt < self.max_retries:
                    retry_count += 1
                    print(f"Extraction failed: {e}. Retrying (attempt {retry_count}/{self.max_retries})...")
                    continue
                else:
                    # Re-raise exception if no retries left
                    raise
        
        # Return last attempt's result
        return last_extracted_data, last_result, retry_count
    
    def should_retry(self, validation_result: ValidationResult) -> bool:
        """
        Determine if a retry should be attempted based on validation result.
        
        Args:
            validation_result: The validation result to check
            
        Returns:
            True if retry should be attempted, False otherwise
        """
        # Retry if validation failed (has errors)
        return not validation_result.is_valid and len(validation_result.errors) > 0
    
    def get_retry_recommendations(self, validation_result: ValidationResult) -> list:
        """
        Get recommendations for improving extraction based on validation errors.
        
        Args:
            validation_result: The validation result with errors
            
        Returns:
            List of recommendations for the extractor
        """
        recommendations = []
        
        for error in validation_result.errors:
            if "repository owner" in error.lower() or "repo_owner" in error.lower():
                recommendations.append("Ensure repository owner is extracted from source context")
            elif "date" in error.lower():
                recommendations.append("Ensure date is properly extracted from commit/PR metadata")
            elif "description" in error.lower():
                recommendations.append("Extract more detailed description from commit message or PR body")
            elif "version change" in error.lower():
                recommendations.append("Look for version patterns in commit message or PR title/body")
        
        return recommendations
