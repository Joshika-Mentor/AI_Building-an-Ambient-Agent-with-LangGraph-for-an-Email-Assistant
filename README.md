# Ambient Agent for Email Assistant (LangGraph)

This project demonstrates how to build an **Ambient Agent** that monitors a Gmail inbox, automatically triages incoming emails, and drafts intelligent responses using **LangGraph** and **LangChain**. The agent runs in the background and uses a human-in-the-loop (HITL) approach, asking for approval before sending out draft responses.

## Features
- **Gmail Integration:** Fetches unread emails from your Inbox.
- **Triage Logic:** Uses an LLM to decide whether an email needs a response or should be ignored (e.g., newsletters, promotions).
- **Automated Drafting:** Drafts polite and context-aware replies for emails needing attention.
- **Human-in-the-Loop:** Pauses the LangGraph execution to allow a human to review, approve, or discard the draft directly via the terminal.
- **State Management:** LangGraph's `MemorySaver` tracks the state of the conversation and workflow.

## Prerequisites
- Python 3.9+
- A Google Cloud Platform account with the **Gmail API** enabled.
- An **OpenAI API Key** (or another LLM provider supported by LangChain).

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/sreedharleo/Building-an-Ambient-Agent-with-LangGraph-for-an-Email-Assistant.git
cd Building-an-Ambient-Agent-with-LangGraph-for-an-Email-Assistant
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Rename the `.env.example` file to `.env` and add your OpenAI API Key:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Gmail API Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and enable the **Gmail API**.
3. Navigate to **APIs & Services > Credentials**.
4. Click **Create Credentials** > **OAuth client ID**.
5. Choose **Desktop app** as the application type.
6. Download the generated JSON file, rename it to `credentials.json`, and place it in the root directory of this project.

## Usage

Run the main agent script:
```bash
python main.py
```

- **First Run:** The script will open a browser window asking you to authenticate with your Google Account. Once authenticated, a `token.json` file will be created to store your access tokens for future use.
- The agent will continuously poll your inbox (every 30 seconds) for new `UNREAD` emails.
- If it finds an email, it will analyze it. If it decides to draft a response, it will pause and prompt you:
  ```
  Approve this draft and send? (y/n):
  ```
- Press `y` to approve and send, or `n` to discard the draft.
- The email will then be marked as read.

## Architecture Structure
- `main.py`: The entry point that polls for emails and manages the CLI interface.
- `agent.py`: Defines the LangGraph state, nodes (`triage`, `draft`, `human_review`), and conditional routing logic.
- `gmail_tools.py`: Helper functions utilizing the `google-api-python-client` to interact with the Gmail API.
