"""Tests for Email Assistant Agent."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.email_agent import should_continue, EmailState


class TestEmailAgent(unittest.TestCase):
    """Test cases for the email agent."""

    def test_should_continue_with_emails(self):
        """Test should_continue returns 'process_email' when emails remain."""
        state = EmailState(
            emails=[{"id": "1"}, {"id": "2"}],
            current_email={},
            responses=[],
            processed_count=0
        )
        result = should_continue(state)
        self.assertEqual(result, "process_email")

    def test_should_continue_no_emails(self):
        """Test should_continue returns 'end' when no emails remain."""
        state = EmailState(
            emails=[{"id": "1"}],
            current_email={},
            responses=[],
            processed_count=1
        )
        result = should_continue(state)
        self.assertEqual(result, "end")


class TestGmailService(unittest.TestCase):
    """Test cases for Gmail service."""

    @patch('src.services.gmail_service.build')
    @patch('src.services.gmail_service.Credentials')
    def test_fetch_unread_emails(self, mock_creds, mock_build):
        """Test fetching unread emails."""
        from src.services.gmail_service import fetch_unread_emails

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': '123', 'threadId': 'thread123'}]
        }

        mock_service.users().messages().get().execute.return_value = {
            'id': '123',
            'threadId': 'thread123',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'Date', 'value': '2024-01-01'}
                ],
                'body': {'data': 'SGVsbG8gV29ybGQ='}  # "Hello World" base64
            }
        }

        emails = fetch_unread_emails(mock_service, max_results=1)

        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]['subject'], 'Test Subject')
        self.assertEqual(emails[0]['from'], 'test@example.com')


if __name__ == '__main__':
    unittest.main()
