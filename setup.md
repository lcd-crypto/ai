# Setup Guide: Running Extractor and Observer Agents

This guide provides step-by-step instructions for setting up and running the extractor and observer agents, where the observer agent monitors and validates the extractor agent's output.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Setting Up the Two Agents (Monitoring Relationship)](#setting-up-the-two-agents-monitoring-relationship)
4. [Running the Agents](#running-the-agents)
5. [Batch Processing](#batch-processing)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before setting up the agents, ensure you have:

- **Python 3.8+** installed
- **Git** installed (for local repository access)
- **OpenAI API Key** (for AI-powered extraction)
- **GitHub Token** (optional, for GitHub repository access)

---

## Initial Setup

### Step 1: Install Dependencies

Navigate to each agent folder and install the required packages:

```bash
# Install extractor agent dependencies
cd extractor
pip install -r requirements.txt

# Install observer agent dependencies
cd ../extractor observer
pip install -r requirements.txt

# Return to AI root
cd ..
```

### Step 2: Configure Environment Variables

#### For Extractor Agent

1. Navigate to the `extractor` folder:
   ```bash
   cd extractor
   ```

2. Copy the example environment file:
   ```bash
   copy .env.example .env
   # On Unix/Linux/Mac: cp .env.example .env
   ```

3. Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   GITHUB_TOKEN=your_github_token_here
   OPENAI_MODEL=gpt-4
   OPENAI_TEMPERATURE=0.3
   ```

#### For Observer Agent

1. Navigate to the `extractor observer` folder:
   ```bash
   cd "extractor observer"
   ```

2. Create a `.env` file (or copy from example if available):
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   OBSERVER_STRICT_MODE=true
   ENABLE_AI_VALIDATION=false
   GENERATE_REPORTS=true
   REPORTS_DIR=reports
   DEFAULT_REPORT_FORMAT=text
   MAX_RETRIES=2
   ```

### Step 3: Verify Installation

Test that both agents can be imported:

```bash
# Test extractor agent
cd extractor
python -c "from ai_agent import AIAgent; print('Extractor agent OK')"

# Test observer agent
cd "../extractor observer"
python -c "from observer_agent import ObserverAgent; print('Observer agent OK')"
```

---

## Setting Up the Two Agents (Monitoring Relationship)

The observer agent is designed to monitor and validate the extractor agent's output. Here's how to set up this relationship:

### Understanding the Relationship

- **Extractor Agent**: Extracts information from commits/PRs (repo owner, date, version change, description)
- **Observer Agent**: Monitors the extractor's output, validates that no data is empty, and can trigger retries

### Setup Method 1: Using the Integration Script (Recommended)

A helper script (`run_agents.py`) is available in the AI root folder that automatically connects both agents:

```python
# The script handles:
# 1. Running extractor agent
# 2. Converting output to observer format
# 3. Running observer agent with retry capability
# 4. Generating reports on failure
```

**Usage:**
```bash
# From AI root folder
python run_agents.py --repo-path "C:\path\to\repository"
```

### Setup Method 2: Manual Integration in Python

Create your own script to connect the agents:

```python
import sys
import os
from datetime import datetime

# Add paths
sys.path.insert(0, 'extractor')
sys.path.insert(0, 'extractor observer')

from extractor.ai_agent import AIAgent
from extractor.models import ExtractedInfo
from extractor_observer.models import ExtractedData
from extractor_observer.observer_agent import ObserverAgent

# Step 1: Initialize Extractor Agent
extractor = AIAgent()

# Step 2: Extract data
extracted_info = extractor.extract_from_commit(
    commit_message="Your commit message",
    repo_owner="repository_owner",
    date=datetime.now(),
    use_ai=True
)

# Step 3: Convert to Observer format
extracted_data = ExtractedData(
    repo_owner=extracted_info.repo_owner,
    date=extracted_info.date,
    version_change=extracted_info.version_change,
    description=extracted_info.description
)

# Step 4: Initialize Observer Agent (monitors extractor)
observer = ObserverAgent(
    strict_mode=False,        # Don't raise exceptions
    generate_reports=True,    # Generate reports on failure
    max_retries=2             # Retry extractor up to 2 times
)

# Step 5: Observer monitors and validates
result = observer.observe_extraction(extracted_data)

if not result.is_valid:
    print(f"Validation failed: {result.errors}")
    # Report automatically generated in reports/ directory
```

### Setup Method 3: Using observe_with_retry (Automatic Retry)

For automatic retry when validation fails:

```python
from extractor.ai_agent import AIAgent
from extractor_observer.observer_agent import ObserverAgent

# Initialize both agents
extractor = AIAgent()
observer = ObserverAgent(max_retries=2, generate_reports=True)

# Observer automatically retries extractor if validation fails
extracted_data, validation_result, retry_count = observer.observe_with_retry(
    extractor_func=extractor.extract_from_commit,
    extractor_args={
        "commit_message": "Your commit message",
        "repo_owner": "repository_owner",
        "date": datetime.now(),
        "use_ai": True
    },
    source_context={"type": "commit"}
)

# Check results
if validation_result.is_valid:
    print("✅ Validation passed!")
else:
    print(f"❌ Validation failed after {retry_count} retries")
    # Report generated automatically
```

### Configuration for Monitoring

In the observer agent's `.env` file, configure monitoring behavior:

```env
# Monitoring Configuration
OBSERVER_STRICT_MODE=false          # Set to true to raise exceptions on failure
GENERATE_REPORTS=true               # Generate reports when validation fails
MAX_RETRIES=2                       # Number of times to retry extractor
REPORTS_DIR=reports                 # Where to store failure reports
DEFAULT_REPORT_FORMAT=text          # Report format: text, json, or html
```

---

## Running the Agents

### Option 1: Run Both Agents Together (Recommended)

Use the integrated script from the AI root folder:

```bash
# For local repository
python run_agents.py --repo-path "C:\path\to\your\repository"

# For specific commit
python run_agents.py --repo-path "C:\path\to\your\repository" --commit-sha "abc123"

# For GitHub repository
python run_agents.py --github-repo "owner/repo-name" --pr-number 123

# With custom retry count
python run_agents.py --repo-path "C:\path\to\your\repository" --max-retries 3
```

### Option 2: Run Extractor Agent First, Then Observer

#### Step 1: Run Extractor Agent

```bash
cd extractor

# Extract from local commit
python main.py --source commit --sha abc123 --repo "C:\path\to\repo"

# Extract from GitHub PR
python main.py --source github-pr --repo "owner/repo" --pr-number 123
```

#### Step 2: Run Observer Agent

```bash
cd "../extractor observer"

# Validate the extracted data
python main.py \
  --repo-owner "repository_owner" \
  --date "2024-01-15T10:30:00" \
  --description "Extracted description" \
  --version-change "1.2.3 -> 2.0.0"
```

### Option 3: Run Using Integration Example

```bash
cd "extractor observer"
python integration_example.py
```

### Option 4: Run with Retry Example

```bash
cd "extractor observer"
python retry_example.py
```

---

## Monitoring Workflow

Here's how the monitoring relationship works:

```
┌─────────────────┐
│ Extractor Agent │
│   (Extracts)    │
└────────┬────────┘
         │
         │ Extracted Data
         ▼
┌─────────────────┐
│ Observer Agent  │
│   (Monitors)    │
└────────┬────────┘
         │
         │ Validation Result
         ▼
    ┌────────┐
    │ Valid? │
    └───┬────┘
        │
    ┌───┴───┐
    │       │
   Yes     No
    │       │
    │       ├──► Retry Extractor (up to 2 times)
    │       │
    │       └──► Generate Report (if all retries fail)
    │
    └──► Continue Processing
```

### Key Monitoring Features

1. **Automatic Validation**: Observer automatically validates all extracted data
2. **Retry Mechanism**: If validation fails, observer instructs extractor to retry (up to 2 times)
3. **Report Generation**: Reports are generated only after all retries are exhausted
4. **Error Tracking**: All validation failures are tracked in history

---

## Batch Processing

The observer agent supports validating multiple extractions in a single call using `observe_batch()`. This is useful when processing many commits or PRs at once.

### Basic Batch Usage

```python
from extractor_observer.observer_agent import ObserverAgent
from extractor_observer.models import ExtractedData
from datetime import datetime

observer = ObserverAgent(generate_reports=True, max_retries=2)

# Prepare a list of extracted data
extractions = [
    ExtractedData(
        repo_owner="owner-a",
        date=datetime(2024, 1, 15),
        version_change="1.0.0 -> 1.1.0",
        description="Added new feature"
    ),
    ExtractedData(
        repo_owner="owner-b",
        date=datetime(2024, 1, 16),
        version_change=None,
        description="Fixed bug in auth module"
    ),
]

# Validate all at once
results = observer.observe_batch(extractions)

for i, result in enumerate(results):
    if result.is_valid:
        print(f"✅ Extraction {i+1} passed")
    else:
        print(f"❌ Extraction {i+1} failed: {result.errors}")
```

### Batch with Source Contexts

You can optionally pass a context dictionary for each extraction (one per item), which will be included in any failure reports:

```python
contexts = [
    {"type": "commit", "sha": "abc123"},
    {"type": "pull_request", "pr_number": 42},
]

results = observer.observe_batch(extractions, source_contexts=contexts)
```

### Controlling Strict Mode in Batch

By default, `observe_batch()` inherits the `strict_mode` setting from the observer instance. You can override this per batch call using the `strict_mode_override` parameter:

```python
# Suppress exceptions for this batch even if observer has strict_mode=True
results = observer.observe_batch(extractions, strict_mode_override=False)

# Enforce strict mode for this batch even if observer has strict_mode=False
results = observer.observe_batch(extractions, strict_mode_override=True)
```

> **Note**: `observe_batch()` does not support automatic retry. If you need retry behaviour for individual items, call `observe_with_retry()` per extraction instead.

---

## Troubleshooting

### Issue: "OPENAI_API_KEY is required"

**Solution**: Make sure you've created `.env` files in both `extractor` and `extractor observer` folders with your OpenAI API key.

### Issue: "Module not found" errors

**Solution**: 
1. Ensure you've installed all requirements: `pip install -r requirements.txt`
2. Check that you're running from the correct directory
3. Verify Python path includes both agent directories

### Issue: Reports not being generated

**Solution**:
1. Check that `GENERATE_REPORTS=true` in observer's `.env`
2. Verify the `reports/` directory exists or can be created
3. Ensure validation actually failed (reports only generated on failure)
4. **Note on report timing**: The behaviour differs depending on how you call the observer:
   - **`observe_extraction()` called directly**: A report is generated immediately when validation fails, on every call.
   - **`observe_with_retry()` used**: Reports are intentionally suppressed during retry attempts and only generated once all retries are exhausted. This is by design to avoid noise from transient failures.

### Issue: Retry not working

**Solution**:
1. Check `MAX_RETRIES` is set to a value > 0 in observer's `.env`
2. Use `observe_with_retry()` method instead of `observe_extraction()`
3. Verify extractor function is being called correctly

### Issue: GitHub integration not working

**Solution**:
1. Add `GITHUB_TOKEN` to extractor's `.env` file
2. Verify token has appropriate permissions
3. Check repository name format: `owner/repo-name`

### Issue: Import errors with space in directory name

**Solution**: The `run_agents.py` script handles this automatically. If using manual integration, use `importlib.util` to load modules from directories with spaces.

---

## Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed in both folders
- [ ] `.env` files created in both `extractor` and `extractor observer` folders
- [ ] OpenAI API key added to both `.env` files
- [ ] GitHub token added (if using GitHub integration)
- [ ] Tested extractor agent: `python extractor/main.py --help`
- [ ] Tested observer agent: `python "extractor observer/main.py" --help`
- [ ] Ready to run: `python run_agents.py --repo-path "your/repo/path"`

---

## Next Steps

1. **Test with a simple commit**: Run the agents on a known commit to verify setup
2. **Review reports**: Check the `extractor observer/reports/` directory for validation reports
3. **Customize configuration**: Adjust `.env` settings based on your needs
4. **Integrate into workflow**: Add the agents to your CI/CD pipeline or development workflow

---

## Additional Resources

- **Extractor Agent README**: `extractor/README.md`
- **Observer Agent README**: `extractor observer/README.md` (if available)
- **Integration Examples**: `extractor observer/integration_example.py`
- **Retry Examples**: `extractor observer/retry_example.py`

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the README files in each agent folder
3. Check the example scripts for usage patterns
