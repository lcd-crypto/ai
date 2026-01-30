"""
Configuration settings for the observer agent.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    # OpenAI Configuration (optional, for AI-powered validation)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    
    # Observer Configuration
    STRICT_MODE = os.getenv("OBSERVER_STRICT_MODE", "true").lower() == "true"
    ENABLE_AI_VALIDATION = os.getenv("ENABLE_AI_VALIDATION", "false").lower() == "true"
    GENERATE_REPORTS = os.getenv("GENERATE_REPORTS", "true").lower() == "true"
    REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
    DEFAULT_REPORT_FORMAT = os.getenv("DEFAULT_REPORT_FORMAT", "text")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
