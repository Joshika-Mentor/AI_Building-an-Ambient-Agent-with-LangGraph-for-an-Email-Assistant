# Email Assistant Agent

**Internship Project** - An ambient AI agent built with LangGraph that automatically monitors and responds to Gmail messages using a local LLM (no API keys needed!).

## Features

- Monitors Gmail inbox for unread emails
- Uses **local LLM (Ollama)** - no OpenAI API key required
- Auto-sends replies to routine requests
- Flags complex emails for human review
- Marks processed emails as read
- Runs entirely on your machine - private & free

## Architecture Flow

```
                         ┌─────────────┐
                         │    Start    │
                         └──────┬──────┘
                                │
                                ▼
                         ┌─────────────┐
     ┌───────────────────┤    Fetch    ├───────────────────┐
     │                   │   Emails    │                   │
     │                   └──────┬──────┘                   │
     │                          │                          │
     │                          ▼                          │
     │                   ┌─────────────┐                     │
     │                   │  next_email │                     │
     │                   └──────┬──────┘                     │
     │                          │                          │
     │                          ▼                          │
     │            ┌─────────────────────────┐                │
     │            │ More emails to process? │                │
     │            └────────────┬────────────┘                │
     │                       │    │                        │
     │                   Yes │    │ No                     │
     │                       ▼    ▼                        │
     │            ┌─────────────┐  ┌────────┐               │
     │            │   Process   │  │  End   │               │
     │            │  (analyze)  │  └────────┘               │
     │            └──────┬──────┘                          │
     │                   │                                  │
     │     ┌─────────────┼─────────────┐                    │
     │     ▼             ▼             ▼                    │
     │┌─────────┐ ┌──────────┐ ┌──────────┐                │
     ││  Send   │ │  Flag    │ │  Mark    │                │
     ││Response │ │ for Human│ │ as Read  │                │
     │└────┬────┘ │ Review   │ └────┬─────┘                │
     │     │      └──────────┘      │                      │
     │     └──────────┬─────────────┘                      │
     │                │                                    │
     └────────────────┴────────────────────────────────────┘
```

## State Flow

1. **fetch** - Retrieve unread emails from Gmail
2. **next_email** - Get next email from queue
3. **should_continue** - Check if more emails remain
4. **process** (analyze_and_respond) - Local LLM decides action:
   - **Auto-send**: Clear requests → send reply + mark read
   - **Flag**: Complex/sensitive → skip + mark read
5. **Loop** - Return to next_email until queue empty

## Project Structure

```
sb/
├── src/                      # Source code
│   ├── agent/
│   │   └── email_agent.py    # LangGraph workflow
│   ├── services/
│   │   └── gmail_service.py  # Gmail API wrapper
│   └── utils/
├── scripts/                  # Entry points
│   ├── setup_gmail.py        # Gmail authentication
│   └── run_agent.py          # Main runner
├── config/                   # Configuration
│   ├── .env.example
│   ├── settings.py
│   └── credentials.example.json
├── tests/                    # Unit tests
│   └── test_agent.py
├── OLLAMA_SETUP.md           # Local LLM setup guide
├── GMAIL_SETUP_GUIDE.md      # Gmail API setup guide
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## Quick Start

### Prerequisites

1. **Install Ollama** (local LLM) - see [OLLAMA_SETUP.md](OLLAMA_SETUP.md)
2. **Setup Gmail API** - see [GMAIL_SETUP_GUIDE.md](GMAIL_SETUP_GUIDE.md)

### Install & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Ollama and pull a model
curl -fsSL https://ollama.com/install.sh | sh  # macOS/Linux
ollama pull llama3.2

# 3. Configure environment
cp config/.env.example config/.env
# Edit config/.env if needed (defaults work for most setups)

# 4. Setup Gmail API (one-time)
# See GMAIL_SETUP_GUIDE.md for detailed steps
python scripts/setup_gmail.py

# 5. Run the agent
python scripts/run_agent.py
```

## Configuration

Edit `config/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | http://localhost:11434 |
| `OLLAMA_MODEL` | Local model name | llama3.2 |
| `MAX_EMAILS` | Max emails to process | 5 |
| `TEMPERATURE` | Response creativity (0-1) | 0.3 |

**Recommended models:**
- `llama3.2` (default) - Fast, good quality, 3B params
- `phi3` - Microsoft, very fast, 3.8B params
- `mistral` - High quality, 7B params
- `llama3` - Best quality, 8B params (slower)

## Components

### src/agent/email_agent.py

LangGraph workflow with nodes:
- `fetch_emails`: Fetch from Gmail API
- `get_next_email`: Pop next from queue
- `analyze_and_respond`: Local LLM analysis & response

### src/services/gmail_service.py

Gmail API wrapper:
- `get_gmail_service`: OAuth authentication
- `fetch_unread_emails`: Get unread messages
- `send_email`: Send replies
- `mark_as_read`: Remove UNREAD label

## Tech Stack

- **LangGraph** - Agent workflow orchestration
- **Ollama** - Local LLM runner (no API costs!)
- **LangChain** - LLM framework
- **Gmail API** - Email integration
- **Python 3.10+**

## Why Local LLM?

- **Privacy** - Your emails never leave your machine
- **Free** - No API costs
- **Offline** - Works without internet (after setup)
- **Customizable** - Use any model you want

---

*Built as an internship project demonstrating LangGraph, local LLMs, and API automation.*
