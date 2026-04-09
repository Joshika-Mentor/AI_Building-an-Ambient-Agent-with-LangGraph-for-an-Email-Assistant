"""Email Assistant Agent built with LangGraph."""
import os
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

from src.services.gmail_service import get_gmail_service, fetch_unread_emails, send_email, mark_as_read

load_dotenv()

# Initialize local LLM via Ollama
llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "llama3.2"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    temperature=float(os.getenv("TEMPERATURE", "0.3"))
)


class EmailState(TypedDict):
    """State for the email agent."""
    emails: List[dict]
    current_email: dict
    responses: Annotated[List[dict], lambda x, y: x + y]
    processed_count: int


def should_continue(state: EmailState):
    """Determine if there are more emails to process."""
    if state["processed_count"] < len(state["emails"]):
        return "process_email"
    return "end"


def fetch_emails(state: EmailState):
    """Fetch unread emails from Gmail."""
    service = get_gmail_service()
    max_emails = int(os.getenv("MAX_EMAILS", "5"))
    emails = fetch_unread_emails(service, max_results=max_emails)
    print(f"Fetched {len(emails)} unread emails")
    return {"emails": emails, "processed_count": 0, "responses": []}


def get_next_email(state: EmailState):
    """Get the next email to process."""
    idx = state["processed_count"]
    if idx < len(state["emails"]):
        return {"current_email": state["emails"][idx]}
    return {"current_email": None}


def analyze_and_respond(state: EmailState):
    """Analyze email and generate response."""
    email = state["current_email"]
    service = get_gmail_service()

    print(f"\n--- Processing Email ---")
    print(f"From: {email['from']}")
    print(f"Subject: {email['subject']}")
    print(f"Body: {email['body'][:200]}...")

    prompt = f"""You are a helpful email assistant. Analyze this email and draft a concise, professional response.

From: {email['from']}
Subject: {email['subject']}
Body: {email['body']}

Draft a brief, helpful response (2-4 sentences max). If the email needs human attention (sensitive, complex, unclear, or you cannot provide a good response), respond with "[NEEDS_HUMAN_REVIEW]".

Response:"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()
    except Exception as e:
        print(f"⚠ LLM Error: {e}")
        response_text = "[NEEDS_HUMAN_REVIEW]"

    result = {
        "email": email,
        "response": response_text,
        "sent": False
    }

    if "[NEEDS_HUMAN_REVIEW]" not in response_text:
        try:
            reply_subject = f"Re: {email['subject']}" if not email['subject'].startswith('Re:') else email['subject']
            send_email(service, email['from'], reply_subject, response_text, email.get('threadId'))
            mark_as_read(service, email['id'])
            result["sent"] = True
            print(f"✓ Response sent and marked as read")
        except Exception as e:
            print(f"✗ Error sending: {e}")
    else:
        print("⚠ Flagged for human review")

    return {
        "responses": [result],
        "processed_count": state["processed_count"] + 1
    }


def create_agent():
    """Create the LangGraph agent."""
    workflow = StateGraph(EmailState)

    workflow.add_node("fetch", fetch_emails)
    workflow.add_node("next_email", get_next_email)
    workflow.add_node("process", analyze_and_respond)

    workflow.set_entry_point("fetch")
    workflow.add_edge("fetch", "next_email")

    workflow.add_conditional_edges(
        "next_email",
        should_continue,
        {"process_email": "process", "end": END}
    )

    workflow.add_edge("process", "next_email")

    return workflow.compile()


if __name__ == "__main__":
    agent = create_agent()
    result = agent.invoke({})

    print(f"\n=== Summary ===")
    print(f"Processed: {len(result['responses'])} emails")
    for r in result['responses']:
        status = "Sent" if r['sent'] else "Needs Review"
        print(f"  - {r['email']['subject'][:40]}... [{status}]")
