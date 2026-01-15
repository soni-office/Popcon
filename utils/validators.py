import re
from typing import Optional
from email_validator import validate_email as validate_email_format, EmailNotValidError

def validate_email(email: str) -> bool:
    """Validate email format"""
    try:
        validate_email_format(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

def extract_domain(url_or_domain: str) -> Optional[str]:
    """Extract domain from URL or return domain if already provided"""
    if not url_or_domain:
        return None
    
    # Remove protocol
    domain = url_or_domain.replace("https://", "").replace("http://", "").replace("www.", "")
    
    # Remove path
    domain = domain.split("/")[0]
    
    # Remove port
    domain = domain.split(":")[0]
    
    # Remove query params
    domain = domain.split("?")[0]
    
    return domain.lower().strip()

def parse_name(full_name: str) -> tuple:
    """Parse full name into first and last name"""
    parts = full_name.strip().split()
    if len(parts) == 0:
        return ("", "")
    elif len(parts) == 1:
        return (parts[0], "")
    else:
        return (parts[0], " ".join(parts[1:]))
