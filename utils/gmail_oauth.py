"""
Gmail OAuth2 Authentication and Service Management
Handles OAuth flow and Gmail API service creation
"""

import os
import json
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Gmail API scopes - only need send permission
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailOAuthService:
    """Manages Gmail OAuth2 authentication and service"""
    
    def __init__(self, credentials_file: str = None, token_dir: str = 'tokens'):
        """
        Initialize Gmail OAuth service
        
        Args:
            credentials_file: Path to Google OAuth2 credentials JSON file
            token_dir: Directory to store user tokens
        """
        self.credentials_file = credentials_file or os.getenv(
            'GOOGLE_CREDENTIALS_FILE',
            'credentials.json'
        )
        self.token_dir = token_dir
        os.makedirs(token_dir, exist_ok=True)
        self._service_cache = {}
    
    def get_token_path(self, email: str) -> str:
        """Get token file path for a specific email"""
        # Sanitize email for filename
        safe_email = email.replace('@', '_at_').replace('.', '_')
        return os.path.join(self.token_dir, f'token_{safe_email}.json')
    
    def get_authorization_url(self, email: str, redirect_uri: str = None) -> str:
        """
        Generate authorization URL for OAuth flow (for web apps)
        
        Args:
            email: User's email address
            redirect_uri: OAuth redirect URI (optional)
        
        Returns:
            Authorization URL
        """
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_file}\n"
                "Please download OAuth2 credentials from Google Cloud Console"
            )
        
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_file,
            SCOPES
        )
        
        # For web apps, we need to get the authorization URL
        flow.redirect_uri = redirect_uri or 'http://localhost:8000/oauth/callback'
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url
    
    def get_gmail_service(self, email: str, port: int = 0, authorization_code: str = None) -> object:
        """
        Authenticate user and return Gmail service
        
        Args:
            email: User's email address
            port: Port for OAuth callback (0 = auto-assign, for desktop apps)
            authorization_code: OAuth authorization code (for web apps)
        
        Returns:
            Gmail API service object
        """
        # Check cache first
        if email in self._service_cache:
            try:
                service = self._service_cache[email]
                # Test if service is still valid
                service.users().getProfile(userId='me').execute()
                return service
            except:
                # Service expired, remove from cache
                del self._service_cache[email]
        
        creds = None
        token_path = self.get_token_path(email)
        
        # Load existing token if available
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                logger.warning(f"Error loading token for {email}: {str(e)}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Try to refresh
                try:
                    creds.refresh(Request())
                    logger.info(f"Refreshed token for {email}")
                except Exception as e:
                    logger.warning(f"Failed to refresh token for {email}: {str(e)}")
                    creds = None
            
            if not creds:
                # Need new authorization
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Please download OAuth2 credentials from Google Cloud Console.\n"
                        f"Expected location: {os.path.abspath(self.credentials_file)}"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, 
                    SCOPES
                )
                
                if authorization_code:
                    # Web app flow - exchange code for token
                    flow.fetch_token(code=authorization_code)
                    creds = flow.credentials
                else:
                    # Desktop app flow - opens browser
                    try:
                        creds = flow.run_local_server(port=port, open_browser=True)
                    except Exception as e:
                        logger.error(f"OAuth flow error: {str(e)}")
                        raise Exception(
                            f"OAuth authentication failed: {str(e)}\n"
                            "Make sure credentials.json exists and is valid."
                        )
                
                logger.info(f"New authorization completed for {email}")
            
            # Save credentials
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"Saved token for {email}")
        
        # Build and cache service
        service = build('gmail', 'v1', credentials=creds)
        self._service_cache[email] = service
        
        return service
    
    def send_message(self, service: object, recipient: str, subject: str, body: str, 
                    from_email: str = None) -> dict:
        """
        Send email via Gmail API
        
        Args:
            service: Gmail API service object
            recipient: Recipient email address
            subject: Email subject
            body: Email body
            from_email: Sender email (optional, uses authenticated user)
        
        Returns:
            Message ID if successful
        """
        try:
            message = EmailMessage()
            message.set_content(body)
            message['To'] = recipient
            message['Subject'] = subject
            # Gmail API uses 'me' to represent authenticated user
            # The actual from address is determined by the authenticated account
            
            # Encode message
            encoded_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()
            
            create_message = {'raw': encoded_message}
            
            # Send message
            send_result = service.users().messages().send(
                userId='me',
                body=create_message
            ).execute()
            
            logger.info(f"Email sent successfully. Message ID: {send_result['id']}")
            return send_result
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise
    
    def revoke_token(self, email: str) -> bool:
        """Revoke token for a user"""
        try:
            token_path = self.get_token_path(email)
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                if creds:
                    creds.revoke(Request())
                os.remove(token_path)
                if email in self._service_cache:
                    del self._service_cache[email]
                logger.info(f"Revoked token for {email}")
                return True
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
        return False
    
    def is_authenticated(self, email: str) -> bool:
        """Check if user is authenticated"""
        token_path = self.get_token_path(email)
        if not os.path.exists(token_path):
            return False
        
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            if creds and creds.valid:
                return True
            elif creds and creds.expired and creds.refresh_token:
                # Can refresh, so still authenticated
                return True
        except:
            pass
        
        return False
