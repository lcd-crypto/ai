# AI Agent for PR/Commit Information Extraction

An AI-powered agent that extracts structured information from pull requests and commits, including:
- **Repository Owner**: The owner of the repository
- **Date**: When the PR/commit was created
- **Version Change**: Version change information (e.g., "1.2.3 -> 2.0.0")
- **Description**: Clear description of the changes

## Features

- 🤖 AI-powered extraction using OpenAI GPT models
- 📝 Rule-based fallback extraction
- 🔗 GitHub API integration
- 💻 Local Git repository support
- 📊 Structured JSON output
- 🎯 Supports both pull requests and commits

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
```

3. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
GITHUB_TOKEN=your_github_token_here  # Optional, for GitHub integration
```

## Usage

### Command Line Interface

#### Extract from a local commit (using Git)
```bash
python main.py --source commit --sha abc123 --repo /path/to/repo
```

#### Extract from a commit message directly
```bash
python main.py --source commit --message "feat: version bump 1.2.3 -> 2.0.0" --repo-owner "microsoft" --date "2024-01-15T10:30:00"
```

#### Extract from a pull request
```bash
python main.py --source pr --message "Add authentication" --body "Implements OAuth2 authentication" --repo-owner "github" --date "2024-01-15T10:30:00"
```

#### Extract from a GitHub pull request
```bash
python main.py --source github-pr --repo owner/repo-name --pr-number 123
```

#### Extract from a GitHub commit
```bash
python main.py --source github-commit --repo owner/repo-name --sha abc123def456
```

#### Use rule-based extraction (no AI)
```bash
python main.py --source commit --message "..." --repo-owner "..." --no-ai
```

#### Output as JSON
```bash
python main.py --source commit --message "..." --repo-owner "..." --output json
```

### Python API

#### Using the AI Agent directly
```python
from ai_agent import AIAgent
from datetime import datetime

agent = AIAgent()

# Extract from commit
result = agent.extract_from_commit(
    commit_message="feat: version bump 1.2.3 -> 2.0.0",
    repo_owner="microsoft",
    date=datetime.now(),
    use_ai=True
)

print(f"Version Change: {result.version_change}")
print(f"Description: {result.description}")
```

#### Using GitHub integration
```python
from github_integration import GitHubIntegration

github = GitHubIntegration()
result = github.extract_from_pr_number(
    repo_name="owner/repo",
    pr_number=123,
    use_ai=True
)
```

#### Using local Git integration
```python
from git_integration import GitIntegration

git = GitIntegration(repo_path=".", repo_owner="microsoft")
result = git.extract_from_commit_sha("abc123", use_ai=True)
```

## Project Structure

```
extractor/
├── main.py                 # CLI entry point
├── ai_agent.py             # Main AI agent class
├── extractors.py           # Rule-based extractors
├── models.py               # Data models (Pydantic)
├── config.py               # Configuration management
├── github_integration.py   # GitHub API integration
├── git_integration.py      # Local Git integration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Output Format

The extracted information is returned as an `ExtractedInfo` object with:
- `repo_owner`: str
- `date`: datetime
- `version_change`: Optional[str] (e.g., "1.2.3 -> 2.0.0")
- `description`: str

## Examples

### Example 1: Commit with version change
```bash
python main.py --source commit \
  --message "Release: version bump 1.2.3 -> 2.0.0 - Added new authentication system" \
  --repo-owner "microsoft" \
  --date "2024-01-15T14:30:00"
```

Output:
```
==================================================
EXTRACTED INFORMATION
==================================================
Repository Owner: microsoft
Date: 2024-01-15 14:30:00
Version Change: 1.2.3 -> 2.0.0
Description: Added new authentication system
==================================================
```

### Example 2: GitHub Pull Request
```bash
python main.py --source github-pr \
  --repo microsoft/vscode \
  --pr-number 12345
```

## Version Change Detection

The agent can detect version changes in various formats:
- `1.2.3 -> 2.0.0`
- `v1.2.3 -> v2.0.0`
- `version 1.2.3 to 2.0.0`
- `upgrade from 1.2.3 to 2.0.0`
- `bump version 1.2.3 to 2.0.0`
- Single version: `v2.0.0` (assumed to be the new version)

## Configuration

You can customize the AI model and behavior in `.env`:
- `OPENAI_MODEL`: Model to use (default: gpt-4)
- `OPENAI_TEMPERATURE`: Temperature for AI responses (default: 0.3)

## Error Handling

The agent includes fallback mechanisms:
- If AI extraction fails, it falls back to rule-based extraction
- If GitHub token is missing, GitHub integration features are disabled
- Validation errors provide clear messages

## License

MIT License
