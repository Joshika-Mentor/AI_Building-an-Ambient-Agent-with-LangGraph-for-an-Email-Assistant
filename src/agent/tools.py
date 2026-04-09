from langchain_core.tools import tool
from src.utils.gmail_client import send_email

@tool
def read_calendar(date: str) -> str:
    """Mock tool to check calendar availability on a given date. Use this whenever the user asks to schedule a meeting."""
    print(f"[TOOL] Checking calendar for: {date}")
    return f"You are free between 2 PM and 5 PM on {date}."

@tool
def send_email_draft(to_email: str, subject: str, body: str) -> str:
    """Dangerous tool to actually send an email. This must be reviewed by a human before execution."""
    print(f"[TOOL] Preparing to send email to {to_email}")
    # The actual graph will interrupt before this is executed. 
    # If approved, this function will ultimately run real API logic.
    res = send_email(to=to_email, subject=subject, body=body)
    return str(res)

SAFE_TOOLS = [read_calendar]
DANGEROUS_TOOLS = [send_email_draft]
ALL_TOOLS = SAFE_TOOLS + DANGEROUS_TOOLS
