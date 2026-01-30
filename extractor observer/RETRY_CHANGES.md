# Changes Made: Retry Functionality for Extractor Agent

## Summary
Added retry functionality to the observer agent that instructs the extractor agent to rerun its script up to 2 times if validation conditions are not met. Reports are only generated after all retry attempts are exhausted.

## Files Created

### 1. `retry_handler.py` (NEW)
- **Purpose**: Handles retry logic for extractor agent operations
- **Key Features**:
  - Manages retry attempts (default: 2 max retries)
  - Executes extractor function with automatic retry on validation failure
  - Provides retry recommendations based on validation errors
  - Tracks retry count and validation results

**Key Classes**:
- `RetryHandler`: Main class for managing retries
  - `execute_with_retry()`: Executes extractor with retry logic
  - `should_retry()`: Determines if retry should be attempted
  - `get_retry_recommendations()`: Provides recommendations for improving extraction

### 2. `retry_example.py` (NEW)
- **Purpose**: Example demonstrating retry functionality
- **Features**:
  - Shows how to use `observe_with_retry()` method
  - Demonstrates retry behavior with valid and invalid data
  - Shows retry count tracking

## Files Modified

### 3. `observer_agent.py` (MODIFIED)
**Changes**:
- Added `max_retries` parameter to `__init__()` method (default: 2)
- Integrated `RetryHandler` for managing retries
- Added `observe_with_retry()` method for automatic retry functionality
- Added `_validate_for_retry()` internal method for validation without report generation
- Modified report generation to only occur after retries are exhausted
- Updated `observe_extraction()` to check retry count before generating reports

**New Methods**:
- `observe_with_retry()`: Main method for extraction with automatic retries
  - Takes extractor function and arguments
  - Automatically retries up to max_retries times
  - Only generates reports after all retries exhausted
  - Returns tuple: (extracted_data, validation_result, retry_count)

**Key Behavior**:
- If validation fails, extractor is automatically rerun
- Up to 2 retry iterations (configurable)
- Reports generated only after retries exhausted
- Retry count tracked and included in report context

### 4. `config.py` (MODIFIED)
**Changes**:
- Added `MAX_RETRIES` configuration option (default: 2)

**New Configuration Variable**:
- `MAX_RETRIES`: Maximum number of retry attempts (default: 2)

### 5. `main.py` (MODIFIED)
**Changes**:
- Added `--max-retries` argument (default: 2)
- Added `--no-retry` argument to disable retry functionality
- Updated `ObserverAgent` initialization to support retry configuration

**New Command Line Options**:
- `--max-retries N`: Set maximum number of retry attempts
- `--no-retry`: Disable retry functionality (reports generated immediately on failure)

### 6. `integration_example.py` (MODIFIED)
**Changes**:
- Updated to show retry capability in observer initialization
- Added comment about retry support

## New Functionality

### Automatic Retry Logic
1. **Initial Extraction**: Extractor agent runs normally
2. **Validation Check**: Observer validates extracted data
3. **Retry Decision**: If validation fails, extractor is rerun automatically
4. **Retry Loop**: Up to 2 retry attempts (configurable)
5. **Report Generation**: Reports only generated after all retries exhausted

### Retry Flow
```
Extraction → Validation → Failed?
    ↓ Yes
Retry 1 → Validation → Failed?
    ↓ Yes
Retry 2 → Validation → Failed?
    ↓ Yes
Generate Report (all retries exhausted)
```

### Retry Tracking
- Retry count is tracked and included in validation history
- Retry information included in report context
- Summary shows retry attempts for failed validations

## Usage Examples

### Basic Usage with Retry
```python
from extractor.ai_agent import AIAgent
from observer_agent import ObserverAgent
from datetime import datetime

extractor = AIAgent()
observer = ObserverAgent(max_retries=2, generate_reports=True)

# Extract with automatic retry
extracted_data, validation_result, retry_count = observer.observe_with_retry(
    extractor_func=extractor.extract_from_commit,
    extractor_args={
        "commit_message": "fix",
        "repo_owner": "microsoft",
        "date": datetime.now(),
        "use_ai": True
    },
    source_context={"type": "commit"}
)

if not validation_result.is_valid:
    print(f"Failed after {retry_count} retries")
    # Report automatically generated
```

### Disable Retries
```python
# Reports generated immediately on first failure
observer = ObserverAgent(max_retries=0, generate_reports=True)
```

### Command Line Usage
```bash
# Use default 2 retries
python main.py --repo-owner "microsoft" --date "..." --description "..."

# Custom retry count
python main.py --repo-owner "microsoft" --date "..." --description "..." --max-retries 3

# Disable retries
python main.py --repo-owner "microsoft" --date "..." --description "..." --no-retry
```

## Configuration

New environment variable in `.env`:
```
MAX_RETRIES=2
```

## Report Generation Behavior

### Before Retry Feature
- Reports generated immediately on first validation failure

### After Retry Feature
- Reports generated only after all retry attempts exhausted
- Report includes retry count and retry exhaustion status
- Context includes: `retry_count`, `max_retries`, `retry_exhausted`

## Backward Compatibility

- All changes are backward compatible
- `observe_extraction()` method still works without retries
- `observe_with_retry()` is new method for retry functionality
- Default max_retries is 2, can be set to 0 to disable
- Existing code continues to work without modifications

## Testing

The retry functionality can be tested by:
1. Running extraction with data that will fail validation
2. Observing retry attempts in console output
3. Verifying reports are only generated after retries exhausted
4. Checking retry count in validation history and reports

## Example Output

```
Step 2: Extracting with automatic retry on validation failure...
Validation failed. Retrying extraction (attempt 1/2)...
Validation failed. Retrying extraction (attempt 2/2)...
✓ Extraction completed after 2 retry attempts

❌ VALIDATION FAILED
  - Retry attempts: 2/2
  - Errors: Description is empty or missing

⚠️  All retry attempts exhausted. Report generated: reports/validation_failure_20240115_143000.txt
```
