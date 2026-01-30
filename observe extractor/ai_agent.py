"""
AI Agent for extracting information from pull requests and commits.
"""
from typing import Optional
from datetime import datetime
from openai import OpenAI
from config import Config
from models import ExtractedInfo
from extractors import CommitExtractor, PullRequestExtractor


class AIAgent:
    """AI agent that extracts structured information from PRs and commits."""
    
    def __init__(self):
        """Initialize the AI agent with OpenAI client."""
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.temperature = Config.OPENAI_TEMPERATURE
    
    def extract_from_commit(
        self,
        commit_message: str,
        author: str,
        date: datetime,
        use_ai: bool = True
    ) -> ExtractedInfo:
        """
        Extract information from a commit using AI or rule-based extraction.
        
        Args:
            commit_message: The commit message
            author: The commit author
            date: The commit date
            use_ai: Whether to use AI extraction (default: True)
            
        Returns:
            ExtractedInfo object with extracted data
        """
        if use_ai:
            return self._extract_with_ai(
                text=commit_message,
                author=author,
                date=date,
                source_type="commit"
            )
        else:
            return CommitExtractor.extract_from_commit_message(
                commit_message=commit_message,
                author=author,
                date=date
            )
    
    def extract_from_pr(
        self,
        title: str,
        body: str,
        author: str,
        date: datetime,
        use_ai: bool = True
    ) -> ExtractedInfo:
        """
        Extract information from a pull request using AI or rule-based extraction.
        
        Args:
            title: The PR title
            body: The PR body/description
            author: The PR author
            date: The PR creation date
            use_ai: Whether to use AI extraction (default: True)
            
        Returns:
            ExtractedInfo object with extracted data
        """
        if use_ai:
            full_text = f"Title: {title}\n\nDescription: {body}"
            return self._extract_with_ai(
                text=full_text,
                author=author,
                date=date,
                source_type="pull request"
            )
        else:
            return PullRequestExtractor.extract_from_pr(
                title=title,
                body=body,
                author=author,
                date=date
            )
    
    def _extract_with_ai(
        self,
        text: str,
        author: str,
        date: datetime,
        source_type: str
    ) -> ExtractedInfo:
        """
        Use AI to extract structured information from text.
        
        Args:
            text: The text to analyze
            author: The author/requestor name
            date: The date
            source_type: Type of source (commit or pull request)
            
        Returns:
            ExtractedInfo object with extracted data
        """
        prompt = f"""Extract the following information from this {source_type}:

Text to analyze:
{text}

Please extract:
1. New version (if mentioned, format as X.Y.Z or X.Y, e.g., "1.2.3" or "2.0")
2. Description of change (a clear, concise description of what changed)

Author: {author}
Date: {date.isoformat()}

Respond in JSON format:
{{
    "new_version": "version number or null",
    "description": "description of the change"
}}

If version is not found, use null. Make the description clear and informative."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from software development texts. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return ExtractedInfo(
                requestor_name=author,
                date=date,
                new_version=result.get("new_version") if result.get("new_version") != "null" else None,
                description=result.get("description", text)
            )
        except Exception as e:
            # Fallback to rule-based extraction if AI fails
            print(f"AI extraction failed: {e}. Falling back to rule-based extraction.")
            if source_type == "commit":
                return CommitExtractor.extract_from_commit_message(text, author, date)
            else:
                # Split title and body for PR
                lines = text.split("\n", 1)
                title = lines[0].replace("Title: ", "")
                body = lines[1].replace("Description: ", "") if len(lines) > 1 else ""
                return PullRequestExtractor.extract_from_pr(title, body, author, date)
