# Gmail API Setup Guide

This guide will walk you through creating a `credentials.json` file to use the Gmail API.

## Step-by-Step Instructions

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click on the project dropdown at the top of the page
4. Click **"New Project"**
5. Enter a project name (e.g., "Email Assistant Agent")
6. Click **"Create"**

### Step 2: Enable Gmail API

1. In your new project, go to the **Navigation Menu** (hamburger icon ☰)
2. Hover over **"APIs & Services"** → Click **"Library"**
3. Search for **"Gmail API"**
4. Click on **"Gmail API"** in the results
5. Click **"Enable"**

### Step 3: Configure OAuth Consent Screen

1. Go to **Navigation Menu** → **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** (for personal use) or **"Internal"** (if you have Google Workspace)
3. Click **"Create"**
4. Fill in the required fields:
   - **App name**: Email Assistant Agent
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click **"Save and Continue"**
6. On the **Scopes** page, click **"Add or Remove Scopes"**
7. Search for **"Gmail API"** and check:
   - `.../auth/gmail.modify` (or `.../auth/gmail.readonly` if you only want to read)
8. Click **"Update"** then **"Save and Continue"**
9. Click **"Save and Continue"** on the **Test users** page
10. Click **"Back to Dashboard"**

### Step 4: Create OAuth 2.0 Credentials

1. Go to **Navigation Menu** → **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** at the top
3. Select **"OAuth client ID"**
4. Configure the OAuth client:
   - **Application type**: Desktop app
   - **Name**: Email Assistant Desktop Client
5. Click **"Create"**
6. A popup will show your **Client ID** and **Client Secret**
7. Click **"Download JSON"**

### Step 5: Place credentials.json in Your Project

1. Rename the downloaded file to `credentials.json`
2. Move it to the **root** of your project folder (same level as `README.md`)

Your folder should look like:
```
sb/
├── credentials.json      ← Place it here
├── src/
├── scripts/
├── config/
├── tests/
└── README.md
```

### Step 6: Run the Setup Script

```bash
python scripts/setup_gmail.py
```

This will:
- Open a browser window
- Ask you to sign in to your Google account
- Request permission to access Gmail
- Save an authentication token to `token.json`

---

## Example credentials.json Structure

Your `credentials.json` should look like this (see `config/credentials.example.json`):

```json
{
  "installed": {
    "client_id": "123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-your-client-secret",
    "redirect_uris": [
      "http://localhost"
    ]
  }
}
```

---

## Troubleshooting

### Error: "Access blocked" or "App not verified"

This is normal for testing. Click **"Advanced"** → **"Go to [App Name] (unsafe)"**.

### Error: "File not found: credentials.json"

Make sure:
1. You renamed the downloaded file to exactly `credentials.json`
2. It's in the **root** project folder (not in `config/` or `src/`)
3. The file has the correct JSON structure

### Token Expired

Delete `token.json` and run `python scripts/setup_gmail.py` again.

### Scope Errors

If you see scope errors, make sure you selected the correct scope in Step 3:
- Use `.../auth/gmail.modify` for sending emails
- Use `.../auth/gmail.readonly` for reading only

---

## Security Notes

⚠️ **Never commit `credentials.json` or `token.json` to Git!**

Both files are already in `.gitignore` but double-check before pushing.

If you accidentally expose these files:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Credentials**
3. Delete the compromised OAuth client
4. Create a new one

---

## Quick Reference

| Step | Action | Link |
|------|--------|------|
| 1 | Create Project | [Cloud Console](https://console.cloud.google.com/) |
| 2 | Enable Gmail API | [API Library](https://console.cloud.google.com/apis/library) |
| 3 | OAuth Consent | [OAuth Screen](https://console.cloud.google.com/apis/credentials/consent) |
| 4 | Create Credentials | [Credentials](https://console.cloud.google.com/apis/credentials) |

---

Need more help? See the official [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python).
