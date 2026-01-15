from dataclasses import dataclass
from typing import Optional

@dataclass
class Company:
    """Represents a company"""
    name: str
    domain: Optional[str] = None
    
    def __hash__(self):
        return hash(self.name.lower())
    
    def __eq__(self, other):
        if isinstance(other, Company):
            return self.name.lower() == other.name.lower()
        return False

@dataclass
class Prospect:
    """Represents a hiring prospect"""
    first_name: str
    last_name: str
    company_name: str
    company_domain: Optional[str] = None
    linkedin_profile: Optional[str] = None
    email: Optional[str] = None
    job_title: Optional[str] = None
    
    def __hash__(self):
        return hash((self.first_name.lower(), self.last_name.lower(), self.company_name.lower()))
    
    def __eq__(self, other):
        if isinstance(other, Prospect):
            return (self.first_name.lower() == other.first_name.lower() and
                   self.last_name.lower() == other.last_name.lower() and
                   self.company_name.lower() == other.company_name.lower())
        return False
    
    def full_name(self) -> str:
        """Return full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for export"""
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name(),
            'company_name': self.company_name,
            'company_domain': self.company_domain,
            'linkedin_profile': self.linkedin_profile,
            'email': self.email,
            'job_title': self.job_title
        }
