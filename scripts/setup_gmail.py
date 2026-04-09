"""Setup script to authenticate Gmail API."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.gmail_service import get_gmail_service

if __name__ == "__main__":
    print("Setting up Gmail authentication...")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a project and enable Gmail API")
    print("3. Download credentials.json and place it in the root directory")
    print("4. Run this script to authenticate\n")

    try:
        service = get_gmail_service()
        print("✓ Gmail authentication successful!")
        print("Token saved to token.json - you can now run the email agent.")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("\nTo get credentials.json:")
        print("1. Visit https://console.cloud.google.com/apis/credentials")
        print("2. Click 'Create Credentials' → 'OAuth client ID'")
        print("3. Select 'Desktop app' as application type")
        print("4. Download the JSON file and rename to credentials.json")
