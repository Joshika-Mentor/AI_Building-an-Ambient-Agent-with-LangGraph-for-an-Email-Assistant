# 📬 Ambient Email Agent

Achieving True Email Autonomy with a Next-Generation Ambient Agent using LangGraph, Google Gemini, and Streamlit.

This project implements a fully autonomous, stateful email assistant operating silently in the background (ambient polling). It handles email triage, intelligent reasoning, safe/dangerous tool routing, and Human-in-the-Loop checkpoints using a robust SQLite-backed persistent memory.

---

## 🚀 Setup Complete Guide

Follow these simple steps from scratch to run your ambient agent:

### 1. Environment & Dependencies

First, ensure you are in the project root directory and set up your environment:

```bash
# Set up a new virtual environment
python -m venv venv
# Activate it (Windows)
.\venv\Scripts\activate

# Install all the necessary dependencies
pip install -r requirements.txt
```

### 2. Configuration & API Keys

The agent relies on `.env` for routing large language models and evaluation frameworks. Create or edit your `.env` file in the root folder:

```text
# ── Google Gemini (LLM) ────────────────────────
GOOGLE_API_KEY=your_gemini_api_key_here

# ── LangSmith (observability & eval) ───────────
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ambient-email-agent

# ── Database ───────────────────────────────────
DB_PATH=memory.db
```

### 3. Connect to Gmail API (OAuth)

The project utilizes the real Gmail API to fetch unread emails and send drafted responses:
1. Go to Google Cloud Console (https://console.cloud.google.com).
2. Enable **Gmail API**.
3. Go to Credentials -> Create **OAuth 2.0 Client IDs** (Desktop Setup).
4. Download the `credentials.json` file.
5. Place the `credentials.json` in the root of this project folder (`ambient_email_agent/credentials.json`).

> **Mock Mode Bypass**: If you do not have or skip adding `credentials.json`, the agent will smoothly fallback into a local "Mock Mode", fetching hardcoded test emails (like Shopify deals or Meeting scheduling requests) to preview logic without crashing!

### 4. Run the Ambient Background Worker
Start the heart of the system. This separate terminal process acts as the "ambient" polling queue, fetching new Gmail events every 10 seconds and channeling them flawlessly via LangGraph to save to memory.

```bash
python ambient_worker.py
```
*(Leave this terminal running in the background).*

### 5. Launch the Digital Curator Dashboard
Open a secondary terminal process. We use a premium customized Streamlit app to look beautifully into the active state graph. 

```bash
streamlit run app.py
```
The browser will launch (`http://localhost:8501`). Here, rather than triggering updates, you will see a historical feed (polled directly from `memory.db`), and safely intercept paused "Dangerous Tools" in your **HITL Checkpoint** tab!

### 6. Run the LangSmith Evaluation Script 
Milestone 2 specifies using an LLM-as-a-judge system to test triage logic and response quality formatting correctly against an Enron validation set (`final_email_assistant.csv`). Note: Ensure you uploaded and parsed the data notebook `Ambient_Mail_Agent.ipynb` first.

```bash
python evaluation_script.py
```
View the exact trace performance over at LangSmith dashboards.

---

## 🧠 Architectural Overview
* **Triage Engine (`src/agent/graph.py`)**: Swiftly routes `ignore`, `notify_human`, and `respond` based on system-contextual instructions. 
* **State Saver (`MemorySaver`)**: All state logic caches to `sqlite3`. 
* **Worker Queue (`ambient_worker.py`)**: Seamless workflow that skips "reads" iteratively based on unique `ThreadIds`.
* **HITL Interrupt**: Employs `interrupt_before=['execute_dangerous_tools']` so emails require a physical UI `Approve/Deny` click before calling the real API bounds.
