import os.path
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_google_credentials():
    """Shows basic usage of the Google APIs."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}. Requiring re-login.")
                creds = None
        
        if not creds:
            if not os.path.exists('credentials.json'):
                logger.warning("credentials.json not found! Please download your OAuth 2.0 Client ID from Google Cloud Console.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

def get_calendar_service():
    creds = get_google_credentials()
    if not creds: return None
    return build('calendar', 'v3', credentials=creds)

def get_gmail_service():
    creds = get_google_credentials()
    if not creds: return None
    return build('gmail', 'v1', credentials=creds)