# Observer Agent

The observer agent monitors and validates data extraction from the extractor agent. Its role is to verify that **no data extracted from the extractor are empty or invalid**.

## Features

- ✅ Validates that all required fields are present and non-empty
- ✅ Checks data quality and format validity
- ✅ Provides detailed error and warning messages
- ✅ Supports batch observation
- ✅ Maintains observation history
- ✅ Strict mode for raising exceptions on failures
- 🤖 Optional AI-powered validation for additional checks
- 📄 **Automatic report generation when monitoring conditions are not met**

## Required Fields (Cannot Be Empty)

1. **repo_owner**: The repository owner name
2. **date**: The date when the PR/commit was created
3. **description**: Description of the changes

## Optional Fields

- **version_change**: Version change information (can be None, but if present must be valid format)

## Report Generation

When monitoring conditions are not met (validation fails), the observer agent automatically generates detailed reports. Reports are saved in the `reports/` directory.

### Report Formats

- **Text** (default): Human-readable text format
- **JSON**: Machine-readable JSON format
- **HTML**: Formatted HTML report with styling

### Report Contents

Each failure report includes:
- Validation status and timestamp
- Extracted data that failed validation
- Source context (if available)
- List of validation errors
- List of validation warnings
- Recommendations for fixing the issues

## Usage

### Command Line Interface

#### Basic observation
```bash
python main.py \
  --repo-owner "microsoft" \
  --date "2024-01-15T10:30:00" \
  --description "Added new authentication feature"
```

#### With version change
```bash
python main.py \
  --repo-owner "github" \
  --date "2024-01-15T10:30:00" \
  --description "Release v2.0.0 with new features" \
  --version-change "1.2.3 -> 2.0.0"
```

#### Strict mode (raises exceptions on failure)
```bash
python main.py \
  --repo-owner "microsoft" \
  --date "2024-01-15T10:30:00" \
  --description "Fixed critical bug" \
  --strict
```

#### Generate HTML report
```bash
python main.py \
  --repo-owner "github" \
  --date "2024-01-15T10:30:00" \
  --description "Updated dependencies" \
  --report-format html
```

#### Disable report generation
```bash
python main.py \
  --repo-owner "microsoft" \
  --date "2024-01-15T10:30:00" \
  --description "Added new feature" \
  --no-reports
```

#### Generate summary report
```bash
python main.py \
  --repo-owner "microsoft" \
  --date "2024-01-15T10:30:00" \
  --description "Added new feature" \
  --generate-summary-report
```

### Python API

#### Basic usage with automatic reporting
```python
from datetime import datetime
from models import ExtractedData
from observer_agent import ObserverAgent

# Create extracted data (from extractor agent)
extracted_data = ExtractedData(
    repo_owner="microsoft",
    date=datetime.now(),
    version_change="1.2.3 -> 2.0.0",
    description="Added new feature"
)

# Create observer agent (reports enabled by default)
observer = ObserverAgent(strict_mode=False, generate_reports=True)

# Observe and validate (report generated automatically if validation fails)
result = observer.observe_extraction(extracted_data)

if not result.is_valid:
    print(f"Validation failed: {result.errors}")
    # Report has been automatically generated in reports/ directory
```

#### Generate summary report
```python
from observer_agent import ObserverAgent

observer = ObserverAgent()

# Perform multiple observations...
# ...

# Generate summary report of all failures
summary_report_path = observer.generate_summary_report(format="html")
if summary_report_path:
    print(f"Summary report: {summary_report_path}")
```

#### Custom report format
```python
from reporter import ReportGenerator
from models import ExtractedData, ValidationResult

# Create report generator
reporter = ReportGenerator(reports_dir="custom_reports")

# Generate report
report_path = reporter.generate_report(
    extracted_data=extracted_data,
    validation_result=validation_result,
    source_context={"type": "commit"},
    format="json"  # or "text", "html"
)
```

## Report Examples

### Text Report
```
================================================================================
MONITORING CONDITION FAILURE REPORT
================================================================================
Generated: 2024-01-15 14:30:00

VALIDATION STATUS: FAILED

--------------------------------------------------------------------------------
EXTRACTED DATA
--------------------------------------------------------------------------------
Repository Owner: microsoft
Date: 2024-01-15 14:30:00
Version Change: Not specified
Description: 

--------------------------------------------------------------------------------
VALIDATION ERRORS
--------------------------------------------------------------------------------
1. Description is empty or missing

--------------------------------------------------------------------------------
RECOMMENDATIONS
--------------------------------------------------------------------------------
- Ensure the description field is provided and contains meaningful content
```

### JSON Report
```json
{
  "report_type": "monitoring_condition_failure",
  "generated_at": "2024-01-15T14:30:00",
  "validation_status": "failed",
  "extracted_data": {
    "repo_owner": "microsoft",
    "date": "2024-01-15T14:30:00",
    "version_change": null,
    "description": ""
  },
  "validation_result": {
    "is_valid": false,
    "errors": ["Description is empty or missing"],
    "warnings": []
  },
  "recommendations": [
    "Ensure the description field is provided and contains meaningful content"
  ]
}
```

## Integration with Extractor Agent

The observer agent is designed to work seamlessly with the extractor agent:

```python
from extractor.ai_agent import AIAgent
from observer_agent import ObserverAgent
from models import ExtractedData
from datetime import datetime

# Extract
extractor = AIAgent()
extracted = extractor.extract_from_commit(
    commit_message="Release: version bump 1.2.3 -> 2.0.0",
    repo_owner="microsoft",
    date=datetime.now()
)

# Convert to observer model
extracted_data = ExtractedData(
    repo_owner=extracted.repo_owner,
    date=extracted.date,
    version_change=extracted.version_change,
    description=extracted.description
)

# Observe (reports generated automatically on failure)
observer = ObserverAgent(strict_mode=True, generate_reports=True)
result = observer.observe_extraction(extracted_data)

if not result.is_valid:
    print("Extraction failed validation!")
    print("Check the reports/ directory for detailed failure report")
    for error in result.errors:
        print(f"  - {error}")
```

## Configuration

You can customize behavior in `.env`:
- `OBSERVER_STRICT_MODE`: Enable/disable strict mode (default: true)
- `ENABLE_AI_VALIDATION`: Enable AI-powered validation (default: false)
- `GENERATE_REPORTS`: Enable automatic report generation (default: true)
- `REPORTS_DIR`: Directory to store reports (default: reports)
- `DEFAULT_REPORT_FORMAT`: Default report format (default: text)
- `OPENAI_API_KEY`: Required if AI validation is enabled
- `OPENAI_MODEL`: Model to use for AI validation (default: gpt-4)
- `OPENAI_TEMPERATURE`: Temperature for AI responses (default: 0.3)

## Accessing Your Report

### Report Storage Location

Reports are automatically stored in the **`reports/`** directory within the "extractor observer" folder.

**Default Location:**
```
extractor observer/
└── reports/
    ├── validation_failure_20240115_143000.txt
    ├── validation_failure_20240115_143000.json
    ├── validation_failure_20240115_143000.html
    └── summary_report_20240115_150000.txt
```

**Full Path (Windows):**
```
C:\Users\client\source\repos\newtry\newtry\ai\extractor observer\reports\
```

**Full Path (Unix/Linux/Mac):**
```
/path/to/project/extractor observer/reports/
```

### Customizing Report Location

You can change the report storage location by setting the `REPORTS_DIR` environment variable in your `.env` file:

```env
REPORTS_DIR=custom_reports
```

This will create reports in a `custom_reports/` directory instead of the default `reports/` directory.

### Report File Naming

Reports are automatically named with timestamps to ensure uniqueness:

- **Individual Failure Reports**: `validation_failure_YYYYMMDD_HHMMSS.{format}`
  - Example: `validation_failure_20240115_143000.txt`
  
- **Summary Reports**: `summary_report_YYYYMMDD_HHMMSS.{format}`
  - Example: `summary_report_20240115_150000.html`

The timestamp format is: `YYYYMMDD_HHMMSS` (Year, Month, Day, Hour, Minute, Second)

### Report Formats

Reports can be generated in three formats:

1. **Text (`.txt`)** - Default format, human-readable
2. **JSON (`.json`)** - Machine-readable format for programmatic processing
3. **HTML (`.html`)** - Formatted report viewable in web browsers

### Finding Your Reports

#### From Command Line
After running the observer agent, reports are automatically created in the `reports/` directory. You can access them:

```bash
# Navigate to reports directory
cd "extractor observer/reports"

# List all reports
ls -la  # Unix/Linux/Mac
dir     # Windows

# View a text report
cat validation_failure_20240115_143000.txt  # Unix/Linux/Mac
type validation_failure_20240115_143000.txt  # Windows

# Open HTML report in browser
open validation_failure_20240115_143000.html  # Mac
xdg-open validation_failure_20240115_143000.html  # Linux
start validation_failure_20240115_143000.html  # Windows
```

#### From Python Code
```python
from observer_agent import ObserverAgent

observer = ObserverAgent()
result = observer.observe_extraction(extracted_data)

# Report path is printed to console when generated
# Or access via report generator
if observer.report_generator:
    reports_dir = observer.report_generator.reports_dir
    print(f"Reports stored in: {reports_dir}")
```

### Automatic Directory Creation

The `reports/` directory is automatically created when the first report is generated. You don't need to create it manually.

### Report Retention

Reports are not automatically deleted. You may want to periodically clean up old reports or implement a retention policy based on your needs.

## Error Handling

The observer agent provides two modes:

1. **Non-strict mode**: Returns `ValidationResult` with errors/warnings and generates reports
2. **Strict mode**: Raises `ValueError` exception on validation failure (reports still generated)

Use strict mode when you want to ensure data quality before proceeding with further processing.

## License

MIT License
