import time
import random
from typing import Optional, List
from openai import OpenAI
from config import Config
from models.prospect import Prospect
from utils.logger import setup_logger
from utils.validators import validate_email
from utils.gmail_oauth import GmailOAuthService

logger = setup_logger(__name__)

class EmailAgent:
    """Agent for generating and sending emails using Gmail OAuth2"""
    
    def __init__(self, user_email: str = None):
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.user_email = user_email
        self.gmail_oauth = GmailOAuthService()
        self.delay_min = 5  # Minimum delay between emails (seconds)
        self.delay_max = 15  # Maximum delay between emails (seconds)
        self._gmail_service = None
    
    def get_gmail_service(self, user_email: str = None) -> object:
        """Get or create Gmail service for user"""
        email = user_email or self.user_email
        if not email:
            raise ValueError("User email is required for Gmail OAuth")
        
        if not self._gmail_service:
            self._gmail_service = self.gmail_oauth.get_gmail_service(email)
        return self._gmail_service
    
    def generate_email(self, prospect: Prospect, template_path: Optional[str] = None, 
                       user_info: Optional[dict] = None) -> str:
        """
        Generate personalized email using GPT
        Returns the email content in a simple, professional format
        """
        logger.info(f"Generating email for {prospect.full_name()}")
        
        try:
            # Load template if provided
            template = ""
            if template_path:
                try:
                    with open(template_path, 'r') as f:
                        template = f.read()
                except FileNotFoundError:
                    logger.warning(f"Template file not found: {template_path}, using default")
            
            # Get user info for personalization
            user_name = user_info.get('name', 'Job Seeker') if user_info else 'Job Seeker'
            user_skills = user_info.get('skills', '') if user_info else ''
            user_goal = user_info.get('goal', '') if user_info else ''
            
            # Create prompt for GPT with user information
            user_context = ""
            if user_skills:
                user_context += f"\n- Mention your skills: {user_skills}"
            if user_goal:
                user_context += f"\n- Reference your goal: {user_goal}"
            
            prompt = f"""Generate a concise, professional email to {prospect.full_name()} at {prospect.company_name}.

The email should:
- Be brief and friendly (2-3 short paragraphs)
- Mention that you were researching {prospect.company_name}
- Express interest in opportunities or collaboration{user_context}
- Request a brief conversation
- Use a casual but professional tone
- Be signed by {user_name}

{"Use this template as a guide:" + template if template else ""}

Generate the email body only (no subject line). Start with "Hi {prospect.first_name}," and end with "Best,\n{user_name}":"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional email writer who creates brief, friendly, and effective outreach emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            email_body = response.choices[0].message.content.strip()
            logger.info(f"Generated email for {prospect.full_name()}")
            return email_body
            
        except Exception as e:
            logger.error(f"Error generating email: {str(e)}")
            raise
    
    def send_email(self, prospect: Prospect, subject: str, body: str, 
                  dry_run: bool = False, user_email: str = None) -> bool:
        """
        Send email via Gmail API using OAuth2
        Returns True if successful, False otherwise
        """
        if not validate_email(prospect.email):
            logger.error(f"Invalid email address: {prospect.email}")
            return False
        
        if dry_run:
            logger.info(f"[DRY RUN] Would send email to {prospect.email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body:\n{body}")
            return True
        
        try:
            # Get Gmail service
            service = self.get_gmail_service(user_email)
            
            # Send email via Gmail API
            self.gmail_oauth.send_message(
                service=service,
                recipient=prospect.email,
                subject=subject,
                body=body
            )
            
            logger.info(f"✅ Sent to: {prospect.full_name()} ({prospect.email})")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {prospect.email}: {str(e)}")
            return False
    
    def generate_and_send(self, prospect: Prospect, template_path: Optional[str] = None, 
                         subject: Optional[str] = None, dry_run: bool = False,
                         user_info: Optional[dict] = None, user_email: str = None) -> bool:
        """
        Generate and send email in one step
        Returns True if successful
        """
        try:
            # Generate email body
            body = self.generate_email(prospect, template_path, user_info=user_info)
            
            # Generate subject if not provided
            if not subject:
                subject = f"Quick question regarding {prospect.company_name}"
            
            # Send email
            return self.send_email(prospect, subject, body, dry_run, user_email=user_email)
            
        except Exception as e:
            logger.error(f"Error in generate_and_send: {str(e)}")
            return False
    
    def send_bulk_emails(self, prospects: List[Prospect], template_path: Optional[str] = None,
                         subject: Optional[str] = None, dry_run: bool = False,
                         user_info: Optional[dict] = None, user_email: str = None) -> dict:
        """
        Send emails to multiple prospects with human-like delays between sends
        Returns a dictionary with success/failure counts
        """
        results = {
            'total': len(prospects),
            'sent': 0,
            'failed': 0
        }
        
        if dry_run:
            logger.info(f"[DRY RUN] Would send {len(prospects)} emails")
            for prospect in prospects:
                self.generate_and_send(prospect, template_path, subject, dry_run=True, 
                                     user_info=user_info, user_email=user_email)
            results['sent'] = len(prospects)
            return results
        
        # Get Gmail service once
        try:
            service = self.get_gmail_service(user_email)
            logger.info("🚀 Connected to Gmail API successfully.")
            
            for idx, prospect in enumerate(prospects, 1):
                logger.info(f"Processing {idx}/{len(prospects)}: {prospect.full_name()}")
                
                try:
                    # Generate email
                    body = self.generate_email(prospect, template_path, user_info=user_info)
                    if not subject:
                        email_subject = f"Quick question regarding {prospect.company_name}"
                    else:
                        email_subject = subject
                    
                    # Send email via Gmail API
                    self.gmail_oauth.send_message(
                        service=service,
                        recipient=prospect.email,
                        subject=email_subject,
                        body=body
                    )
                    
                    logger.info(f"✅ Sent to: {prospect.full_name()} ({prospect.email})")
                    results['sent'] += 1
                    
                    # Anti-spam: Wait 5 to 15 seconds between emails (except for last one)
                    if idx < len(prospects):
                        wait_time = random.randint(self.delay_min, self.delay_max)
                        logger.info(f"⏳ Waiting {wait_time}s to simulate human behavior...")
                        time.sleep(wait_time)
                    
                except Exception as e:
                    logger.error(f"❌ Error sending to {prospect.email}: {str(e)}")
                    results['failed'] += 1
                    continue
            
        except Exception as e:
            logger.error(f"❌ Gmail API error: {str(e)}")
            results['failed'] = len(prospects) - results['sent']
        
        logger.info(f"📊 Bulk send complete: {results['sent']} sent, {results['failed']} failed")
        return results
