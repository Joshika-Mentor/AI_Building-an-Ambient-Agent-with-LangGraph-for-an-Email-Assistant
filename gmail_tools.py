import os.path
import base64
from email.message import EmailMessage
from typing import List, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("WARNING: Please download your credentials.json from Google Cloud Console and place it in the project root.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def fetch_unread_emails(service, max_results=5) -> List[Dict]:
    """Fetch unread emails from the inbox."""
    try:
        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        email_data = []
        if not messages:
            return email_data
            
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
            sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')
            
            # Extract body
            body = "No text content"
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
                
            email_data.append({
                'id': message['id'],
                'threadId': message['threadId'],
                'subject': subject,
                'sender': sender,
                'body': body
            })
            
        return email_data
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

def mark_as_read(service, msg_id):
    """Remove UNREAD label from a message."""
    try:
        service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
    except HttpError as error:
        print(f'An error occurred: {error}')

def create_draft_reply(service, msg_id, thread_id, to, original_subject, draft_content):
    """Create a draft reply."""
    try:
        message = EmailMessage()
        message.set_content(draft_content)
        message['To'] = to
        message['From'] = 'me'
        
        if not original_subject.startswith('Re:'):
            message['Subject'] = f'Re: {original_subject}'
        else:
            message['Subject'] = original_subject
            
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {
            'message': {
                'raw': encoded_message,
                'threadId': thread_id
            }
        }
        draft = service.users().drafts().create(userId='me', body=create_message).execute()
        return draft
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def send_draft(service, draft_id):
    """Send an existing draft."""
    try:
        sent_message = service.users().drafts().send(userId='me', body={'id': draft_id}).execute()
        return sent_message
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None
