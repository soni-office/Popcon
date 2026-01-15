import time
import requests
from typing import Optional
from config import Config
from models.prospect import Prospect
from utils.logger import setup_logger
from utils.validators import validate_email, extract_domain

logger = setup_logger(__name__)

class HunterAgent:
    """Agent for finding email addresses using Hunter.io API"""
    
    def __init__(self):
        self.api_key = Config.HUNTER_API_KEY
        self.base_url = "https://api.hunter.io/v2"
        self.last_request_time = 0
        self.min_request_interval = 1.0 / Config.HUNTER_RATE_LIMIT
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def find_email(self, prospect: Prospect, retries: int = 3) -> Optional[str]:
        """
        Find email address for a prospect using Hunter.io
        Returns email if found, None otherwise
        """
        if not prospect.company_domain:
            # Try to get domain from company name
            domain = self._guess_domain(prospect.company_name)
            if not domain:
                logger.warning(f"No domain available for {prospect.company_name}")
                return None
            prospect.company_domain = domain
        
        logger.info(f"Finding email for {prospect.full_name()} at {prospect.company_domain}")
        
        for attempt in range(retries):
            try:
                self._rate_limit()
                
                # Use email finder API
                url = f"{self.base_url}/email-finder"
                params = {
                    "api_key": self.api_key,
                    "domain": prospect.company_domain,
                    "first_name": prospect.first_name,
                    "last_name": prospect.last_name
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("data") and data["data"].get("email"):
                    email = data["data"]["email"]
                    score = data["data"].get("score", 0)
                    
                    if validate_email(email) and score >= 50:  # Minimum confidence score
                        logger.info(f"Found email for {prospect.full_name()}: {email} (score: {score})")
                        return email
                    else:
                        logger.warning(f"Email found but low confidence: {email} (score: {score})")
                
                # Try domain search as fallback
                return self._domain_search(prospect)
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {prospect.full_name()}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(Config.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"Failed to find email for {prospect.full_name()} after {retries} attempts")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error finding email: {str(e)}")
                return None
        
        return None
    
    def _domain_search(self, prospect: Prospect) -> Optional[str]:
        """Search for email using domain search"""
        try:
            self._rate_limit()
            url = f"{self.base_url}/domain-search"
            params = {
                "api_key": self.api_key,
                "domain": prospect.company_domain,
                "seniority": "senior",
                "limit": 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            emails = data.get("data", {}).get("emails", [])
            
            # Try to match by name
            for email_data in emails:
                if (email_data.get("first_name", "").lower() == prospect.first_name.lower() and
                    email_data.get("last_name", "").lower() == prospect.last_name.lower()):
                    email = email_data.get("value")
                    if validate_email(email):
                        logger.info(f"Found email via domain search: {email}")
                        return email
            
            return None
            
        except Exception as e:
            logger.debug(f"Domain search failed: {str(e)}")
            return None
    
    def _guess_domain(self, company_name: str) -> Optional[str]:
        """Guess company domain from company name"""
        # Simple heuristic: convert company name to domain
        # In production, you might want to use a domain lookup service
        domain = company_name.lower().replace(" ", "").replace("&", "and")
        domain = domain.replace(",", "").replace(".", "")
        # This is a simplified approach - in production, use a proper domain lookup
        return f"{domain}.com"  # This is just a placeholder
