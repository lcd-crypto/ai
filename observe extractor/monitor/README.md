# Monitoring Agent

The monitoring agent validates data extraction accuracy from the extractor agent. The main validation rule is: **no data extracted can be empty** (except `new_version` which is optional).

## Features

- ✅ Validates that all required fields are present and non-empty
- ✅ Checks data quality and accuracy
- ✅ Provides detailed error and warning messages
- ✅ Supports batch validation
- ✅ Maintains validation history
- ✅ Strict mode for raising exceptions on failures

## Required Fields (Cannot Be Empty)

1. **requestor_name**: The name of the person who created the PR/commit
2. **date**: The date when the PR/commit was created
3. **description**: Description of the changes

## Optional Fields

- **new_version**: Version number (can be None or empty)

## Usage

### Command Line Interface

#### Basic validation
```bash
python monitor/monitor_main.py \
  --requestor "John Doe" \
  --date "2024-01-15T10:30:00" \
  --description "Added new authentication feature"
```

#### With version
```bash
python monitor/monitor_main.py \
  --requestor "Jane Smith" \
  --date "2024-01-15T10:30:00" \
  --description "Release v2.0.0 with new features" \
  --version "2.0.0"
```

#### Strict mode (raises exceptions on failure)
```bash
python monitor/monitor_main.py \
  --requestor "Bob Wilson" \
  --date "2024-01-15T10:30:00" \
  --description "Fixed critical bug" \
  --strict
```

#### JSON output
```bash
python monitor/monitor_main.py \
  --requestor "Alice Developer" \
  --date "2024-01-15T10:30:00" \
  --description "Updated dependencies" \
  --output json
```

### Python API

#### Basic usage
```python
from datetime import datetime
from models import ExtractedInfo
from monitor.monitor_agent import MonitorAgent

# Create extracted info
extracted_info = ExtractedInfo(
    requestor_name="John Doe",
    date=datetime.now(),
    new_version="1.2.3",
    description="Added new feature"
)

# Create monitor agent
monitor = MonitorAgent(strict_mode=False)

# Validate
result = monitor.monitor_extraction(extracted_info)

if result.is_valid:
    print("Validation passed!")
else:
    print(f"Validation failed: {result.errors}")
```

#### With extractor agent integration
```python
from ai_agent import AIAgent
from monitor.monitor_agent import MonitorAgent
from datetime import datetime

# Extract data
extractor = AIAgent()
extracted_info = extractor.extract_from_commit(
    commit_message="feat: add new feature v1.2.3",
    author="John Doe",
    date=datetime.now()
)

# Monitor and validate
monitor = MonitorAgent(strict_mode=True)
try:
    result = monitor.monitor_extraction(extracted_info)
    print("Extraction validated successfully!")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

#### Batch validation
```python
from monitor.monitor_agent import MonitorAgent

monitor = MonitorAgent()

# Validate multiple extractions
results = monitor.validate_batch(extracted_infos)

# Get summary
summary = monitor.get_validation_summary()
print(f"Pass rate: {summary['pass_rate']}%")
```

## Validation Checks

### Completeness Checks
- ✅ Requestor name is not None and not empty
- ✅ Date is not None
- ✅ Description is not None and not empty

### Quality Checks
- ⚠️ Requestor name is at least 2 characters
- ⚠️ Description is at least 10 characters (recommended: 20+)
- ⚠️ Date is not in the future
- ⚠️ Date is not too old (>100 years)
- ⚠️ Version format is valid (X.Y.Z or X.Y) if provided
- ⚠️ Description doesn't contain placeholder text

## Output Format

### Pretty Output
```
==================================================
VALIDATION RESULT
==================================================
Validation Status: VALID
Warnings (1):
  - Description is very short (less than 10 characters)
==================================================
```

### JSON Output
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    "Description is very short (less than 10 characters)"
  ],
  "extracted_data": {
    "requestor_name": "John Doe",
    "date": "2024-01-15T10:30:00",
    "new_version": "1.2.3",
    "description": "Fix"
  }
}
```

## Running Tests

```bash
python monitor/test_monitor.py
```

This will run various test cases including:
- Valid extractions
- Empty requestor names
- Empty descriptions
- Short descriptions
- Batch validation

## Integration with Extractor Agent

The monitoring agent is designed to work seamlessly with the extractor agent:

```python
from ai_agent import AIAgent
from monitor.monitor_agent import MonitorAgent
from datetime import datetime

# Extract
extractor = AIAgent()
extracted = extractor.extract_from_commit(
    commit_message="Release v2.0.0",
    author="Developer",
    date=datetime.now()
)

# Monitor
monitor = MonitorAgent(strict_mode=True)
result = monitor.monitor_extraction(extracted)

if not result.is_valid:
    print("Extraction failed validation!")
    for error in result.errors:
        print(f"  - {error}")
```

## Error Handling

The monitoring agent provides two modes:

1. **Non-strict mode** (default): Returns `ValidationResult` with errors/warnings
2. **Strict mode**: Raises `ValidationError` exception on validation failure

Use strict mode when you want to ensure data quality before proceeding with further processing.
