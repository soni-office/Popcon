import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for API keys and settings"""
    
    # API Keys
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # SMTP Settings (default to SSL port 465 for Gmail)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # Default to 465 for SSL
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Job Seeker")
    
    # Rate Limiting
    TAVILY_RATE_LIMIT = 5  # requests per second
    HUNTER_RATE_LIMIT = 10  # requests per second
    
    # Retry Settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    @classmethod
    def validate(cls):
        """Validate that all required API keys are present"""
        missing = []
        if not cls.TAVILY_API_KEY:
            missing.append("TAVILY_API_KEY")
        if not cls.HUNTER_API_KEY:
            missing.append("HUNTER_API_KEY")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.SMTP_USERNAME:
            missing.append("SMTP_USERNAME")
        if not cls.SMTP_PASSWORD:
            missing.append("SMTP_PASSWORD")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
