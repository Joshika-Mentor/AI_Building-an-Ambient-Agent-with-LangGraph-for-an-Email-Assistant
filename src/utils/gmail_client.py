import os
import pickle
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.message import EmailMessage

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """Authenticates using credentials.json and returns the Gmail service."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Missing credentials.json for Gmail API. Returning mock service.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Failed to build Gmail service: {e}")
        return None

def fetch_recent_emails(max_results=5):
    """Fetches recent unread emails from the inbox."""
    service = get_gmail_service()
    if not service:
        # Mock behavior if no Gmail API configured
        return [
            {"message_id": "mock1", "sender": "bob@acme.com", "subject": "Can we meet Tuesday at 3pm?", "body": "Hi, I'd like to schedule a 30-minute sync to discuss the Q4 roadmap. Are you free Tuesday afternoon?"},
            {"message_id": "mock2", "sender": "deals@shopify.com", "subject": "Flash sale — 50% off everything!", "body": "Don't miss our biggest sale! Shop now."}
        ]

    try:
        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        email_data = []
        for msg in messages:
            msg_id = msg['id']
            msg_full = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            headers = msg_full.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown Sender")
            snippet = msg_full.get('snippet', '')
            
            email_data.append({
                "message_id": msg_id,
                "sender": sender,
                "subject": subject,
                "body": snippet
            })
            
        return email_data
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []

def send_email(to, subject, body):
    """Sends an email using the Gmail API."""
    service = get_gmail_service()
    if not service:
        print(f"MOCK: Sent email to {to} | Subject: {subject} | Body: {body}")
        return {"id": "mock_sent_id", "status": "MOCK_SUCCESS"}

    try:
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['From'] = 'me'
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f'Sent email to {to}. Message ID: {send_message["id"]}')
        return send_message
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"error": str(e)}
