# Changes Made: Report Generation for Monitoring Condition Failures

## Summary
Added comprehensive report generation functionality that automatically creates detailed reports when monitoring conditions are not met (validation fails).

## Files Created

### 1. `reporter.py` (NEW)
- **Purpose**: Report generator module for creating validation failure reports
- **Features**:
  - Generates reports in multiple formats: Text, JSON, HTML
  - Creates individual failure reports for each validation failure
  - Creates summary reports aggregating all failed validations
  - Includes recommendations for fixing validation issues
  - Automatically creates `reports/` directory for storing reports

**Key Classes**:
- `ReportGenerator`: Main class for generating reports
  - `generate_report()`: Creates individual failure reports
  - `generate_summary_report()`: Creates summary reports
  - Supports text, JSON, and HTML formats

## Files Modified

### 2. `observer_agent.py` (MODIFIED)
**Changes**:
- Added `generate_reports` parameter to `__init__()` method
- Integrated `ReportGenerator` import
- Added automatic report generation when validation fails
- Added `generate_summary_report()` method for creating summary reports
- Reports are generated automatically when `generate_reports=True` (default)

**New Features**:
- Automatic report generation on validation failure
- Summary report generation capability
- Configurable report generation (can be disabled)

### 3. `main.py` (MODIFIED)
**Changes**:
- Added `--report-format` argument (choices: text, json, html)
- Added `--no-reports` argument to disable report generation
- Added `--generate-summary-report` argument for summary reports
- Updated `ObserverAgent` initialization to support report generation
- Added summary report generation logic

**New Command Line Options**:
- `--report-format`: Choose report format (text/json/html)
- `--no-reports`: Disable automatic report generation
- `--generate-summary-report`: Generate summary report of all validations

### 4. `config.py` (MODIFIED)
**Changes**:
- Added `GENERATE_REPORTS` configuration option (default: true)
- Added `REPORTS_DIR` configuration option (default: "reports")
- Added `DEFAULT_REPORT_FORMAT` configuration option (default: "text")

**New Configuration Variables**:
- `GENERATE_REPORTS`: Enable/disable automatic report generation
- `REPORTS_DIR`: Directory to store generated reports
- `DEFAULT_REPORT_FORMAT`: Default format for reports

### 5. `README.md` (MODIFIED)
**Changes**:
- Added comprehensive "Report Generation" section
- Added report format descriptions
- Added report content details
- Added usage examples for report generation
- Added configuration options for reports
- Added report file naming conventions
- Added examples of report outputs (text and JSON)

**New Sections**:
- Report Generation
- Report Formats
- Report Contents
- Report Examples
- Report Files

## New Functionality

### Automatic Report Generation
- Reports are automatically generated when validation fails
- Reports saved to `reports/` directory (configurable)
- File naming: `validation_failure_YYYYMMDD_HHMMSS.{format}`

### Report Formats
1. **Text Format**: Human-readable plain text report
2. **JSON Format**: Machine-readable JSON report
3. **HTML Format**: Styled HTML report with formatting

### Report Contents
Each failure report includes:
- Validation status and timestamp
- Complete extracted data that failed
- Source context (if available)
- List of all validation errors
- List of all validation warnings
- Recommendations for fixing issues

### Summary Reports
- Aggregates all failed validations
- Includes summary statistics
- Shows pass/fail rates
- Lists all failed validations with details

## Usage Examples

### Automatic Report Generation
```python
observer = ObserverAgent(generate_reports=True)
result = observer.observe_extraction(extracted_data)
# Report automatically generated if validation fails
```

### Custom Report Format
```python
observer = ObserverAgent()
result = observer.observe_extraction(extracted_data)
# Generate summary report in HTML format
summary_path = observer.generate_summary_report(format="html")
```

### Command Line
```bash
# Generate HTML report on failure
python main.py --repo-owner "microsoft" --date "..." --description "..." --report-format html

# Generate summary report
python main.py --repo-owner "microsoft" --date "..." --description "..." --generate-summary-report
```

## Directory Structure

After changes:
```
extractor observer/
├── reporter.py          # NEW: Report generation module
├── observer_agent.py     # MODIFIED: Added report generation
├── main.py              # MODIFIED: Added report CLI options
├── config.py            # MODIFIED: Added report configuration
├── README.md            # MODIFIED: Added report documentation
└── reports/             # NEW: Directory created automatically for reports
    ├── validation_failure_20240115_143000.txt
    ├── validation_failure_20240115_143000.json
    └── summary_report_20240115_150000.html
```

## Configuration

New environment variables in `.env`:
```
GENERATE_REPORTS=true
REPORTS_DIR=reports
DEFAULT_REPORT_FORMAT=text
```

## Backward Compatibility

- All changes are backward compatible
- Report generation is enabled by default but can be disabled
- Existing code continues to work without modifications
- Reports are only generated when validation fails

## Testing

The reporting system can be tested by:
1. Running validation with invalid data
2. Checking `reports/` directory for generated files
3. Verifying report content and format
4. Testing summary report generation
