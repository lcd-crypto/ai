# AI Agent for PR/Commit Information Extraction

An AI-powered agent that extracts structured information from pull requests and commits, including:
- **Requestor name**: The person who created the PR or commit
- **Date**: When the PR/commit was created
- **New version**: Version number if mentioned (e.g., 1.2.3)
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
python main.py --source commit --message "feat: add new feature v1.2.3" --author "John Doe" --date "2024-01-15T10:30:00"
```

#### Extract from a pull request
```bash
python main.py --source pr --message "Add authentication" --body "Implements OAuth2 authentication" --author "Jane Smith" --date "2024-01-15T10:30:00"
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
python main.py --source commit --message "..." --author "..." --no-ai
```

#### Output as JSON
```bash
python main.py --source commit --message "..." --author "..." --output json
```

### Python API

#### Using the AI Agent directly
```python
from ai_agent import AIAgent
from datetime import datetime

agent = AIAgent()

# Extract from commit
result = agent.extract_from_commit(
    commit_message="feat: add new feature v1.2.3",
    author="John Doe",
    date=datetime.now(),
    use_ai=True
)

print(f"Version: {result.new_version}")
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

git = GitIntegration(repo_path=".")
result = git.extract_from_commit_sha("abc123", use_ai=True)
```

## Project Structure

```
ai/
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
- `requestor_name`: str
- `date`: datetime
- `new_version`: Optional[str]
- `description`: str

## Examples

### Example 1: Commit with version
```bash
python main.py --source commit \
  --message "Release v2.1.0: Added new authentication system" \
  --author "Alice Developer" \
  --date "2024-01-15T14:30:00"
```

Output:
```
==================================================
EXTRACTED INFORMATION
==================================================
Requestor: Alice Developer
Date: 2024-01-15 14:30:00
New Version: 2.1.0
Description: Added new authentication system
==================================================
```

### Example 2: GitHub Pull Request
```bash
python main.py --source github-pr \
  --repo microsoft/vscode \
  --pr-number 12345
```

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
