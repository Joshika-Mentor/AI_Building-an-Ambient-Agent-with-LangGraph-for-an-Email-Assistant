"""Gmail API service for fetching and sending emails."""
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    token_file = 'token.json'
    credentials_file = 'credentials.json'

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"{credentials_file} not found. Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def fetch_unread_emails(service, max_results=10):
    """Fetch unread emails from inbox."""
    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX', 'UNREAD'],
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])
    emails = []

    for msg in messages:
        msg_detail = service.users().messages().get(
            userId='me', id=msg['id'], format='full'
        ).execute()

        headers = msg_detail['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

        body = extract_body(msg_detail['payload'])

        emails.append({
            'id': msg['id'],
            'subject': subject,
            'from': sender,
            'date': date,
            'body': body,
            'threadId': msg_detail.get('threadId', '')
        })

    return emails


def extract_body(payload):
    """Extract email body from payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            elif part['mimeType'] == 'text/html':
                data = part['body'].get('data', '')
                if data:
                    import re
                    html = base64.urlsafe_b64decode(data).decode('utf-8')
                    return re.sub('<[^<]+?>', '', html)
    else:
        data = payload['body'].get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')
    return ''


def send_email(service, to, subject, body, thread_id=None):
    """Send an email reply."""
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    body_dict = {'raw': raw}

    if thread_id:
        body_dict['threadId'] = thread_id

    sent = service.users().messages().send(userId='me', body=body_dict).execute()
    return sent


def mark_as_read(service, message_id):
    """Mark email as read."""
    service.users().messages().modify(
        userId='me',
        id=message_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()
