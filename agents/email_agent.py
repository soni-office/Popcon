import smtplib
import time
import random
from email.message import EmailMessage
from typing import Optional, List
from openai import OpenAI
from config import Config
from models.prospect import Prospect
from utils.logger import setup_logger
from utils.validators import validate_email

logger = setup_logger(__name__)

class EmailAgent:
    """Agent for generating and sending emails"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        # Use SMTP_SSL on port 465 for Gmail (more reliable)
        self.smtp_host = Config.SMTP_HOST
        self.smtp_port = Config.SMTP_PORT
        self.use_ssl = Config.SMTP_PORT == 465  # Use SSL if port is 465
        self.smtp_username = Config.SMTP_USERNAME
        self.smtp_password = Config.SMTP_PASSWORD
        self.from_email = Config.SMTP_FROM_EMAIL or Config.SMTP_USERNAME
        self.from_name = Config.SMTP_FROM_NAME
        self.delay_min = 5  # Minimum delay between emails (seconds)
        self.delay_max = 15  # Maximum delay between emails (seconds)
    
    def generate_email(self, prospect: Prospect, template_path: Optional[str] = None) -> str:
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
            
            # Create prompt for GPT with simpler format
            prompt = f"""Generate a concise, professional email to {prospect.full_name()} at {prospect.company_name}.

The email should:
- Be brief and friendly (2-3 short paragraphs)
- Mention that you were researching {prospect.company_name}
- Express interest in opportunities or collaboration
- Request a brief conversation
- Use a casual but professional tone

{"Use this template as a guide:" + template if template else ""}

Generate the email body only (no subject line, no signature). Start with "Hi {prospect.first_name},":"""
            
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
    
    def send_email(self, prospect: Prospect, subject: str, body: str, dry_run: bool = False) -> bool:
        """
        Send email via SMTP using EmailMessage (simpler format)
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
            # Create message using EmailMessage (simpler)
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = prospect.email
            msg.set_content(body)
            
            # Send email using SMTP_SSL for port 465 or SMTP with STARTTLS for port 587
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as smtp:
                    smtp.login(self.smtp_username, self.smtp_password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                    smtp.starttls()
                    smtp.login(self.smtp_username, self.smtp_password)
                    smtp.send_message(msg)
            
            logger.info(f"✅ Sent to: {prospect.full_name()} ({prospect.email})")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {prospect.email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return False
    
    def generate_and_send(self, prospect: Prospect, template_path: Optional[str] = None, 
                         subject: Optional[str] = None, dry_run: bool = False) -> bool:
        """
        Generate and send email in one step
        Returns True if successful
        """
        try:
            # Generate email body
            body = self.generate_email(prospect, template_path)
            
            # Generate subject if not provided (using your format)
            if not subject:
                subject = f"Quick question regarding {prospect.company_name}"
            
            # Send email
            return self.send_email(prospect, subject, body, dry_run)
            
        except Exception as e:
            logger.error(f"Error in generate_and_send: {str(e)}")
            return False
    
    def send_bulk_emails(self, prospects: List[Prospect], template_path: Optional[str] = None,
                         subject: Optional[str] = None, dry_run: bool = False) -> dict:
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
                self.generate_and_send(prospect, template_path, subject, dry_run=True)
            results['sent'] = len(prospects)
            return results
        
        # Establish a single connection for efficiency
        try:
            if self.use_ssl:
                smtp_connection = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                smtp_connection = smtplib.SMTP(self.smtp_host, self.smtp_port)
                smtp_connection.starttls()
            
            smtp_connection.login(self.smtp_username, self.smtp_password)
            logger.info("🚀 Connected to SMTP server successfully.")
            
            for idx, prospect in enumerate(prospects, 1):
                logger.info(f"Processing {idx}/{len(prospects)}: {prospect.full_name()}")
                
                try:
                    # Generate email
                    body = self.generate_email(prospect, template_path)
                    if not subject:
                        email_subject = f"Quick question regarding {prospect.company_name}"
                    else:
                        email_subject = subject
                    
                    # Create message
                    msg = EmailMessage()
                    msg['Subject'] = email_subject
                    msg['From'] = self.from_email
                    msg['To'] = prospect.email
                    msg.set_content(body)
                    
                    # Send email
                    smtp_connection.send_message(msg)
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
            
            smtp_connection.quit()
            
        except Exception as e:
            logger.error(f"❌ Connection error: {str(e)}")
            results['failed'] = len(prospects) - results['sent']
        
        logger.info(f"📊 Bulk send complete: {results['sent']} sent, {results['failed']} failed")
        return results