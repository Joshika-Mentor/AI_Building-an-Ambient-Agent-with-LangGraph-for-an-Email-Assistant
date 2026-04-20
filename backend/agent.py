import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage

# Load environment variables
load_dotenv()

# Define the state for our agent
class AgentState(TypedDict):
    email_content: str
    triage_result: str
    reasoning: str
    category: str
    agent_action: str

# Initialize the LLM
# Note: You need GOOGLE_API_KEY in your .env
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0)

def triage_node(state: AgentState):
    """
    Classifies the email into: ignore, notify_human, or respond/act.
    Also determines the category and suggested action for the UI.
    """
    content = state["email_content"]
    prefs = get_preferences()
    
    prompt = f"""
    Analyze the following email content and categorize it.
    
    Email: {content}
    
    Current User Preferences for Drafting/Formatting:
    {prefs if prefs else "None"}
    
    Instructions:
    1. Triage the email as one of: 'ignore', 'notify_human', 'respond/act'.
    2. Assign a category: 'Work', 'Finance', 'Personal', or 'Other'.
    3. Suggest an action: 
       - 'Add to calendar / notify team' (for Work)
       - 'Forward to accounts department' (for Finance)
       - 'Mark as personal / no action' (for Personal)
       - 'Archive' (for Other/Ignore)
    4. If the preferences mention specific names or rules, follow them in your reasoning.
    
    Return your response in this EXACT format:
    TRIAGE: [class]
    CATEGORY: [category]
    ACTION: [action]
    REASONING: [reason]
    """
    
    response = llm.invoke(prompt)
    text = response.content
    
    # Simple parsing
    result = {}
    for line in text.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            result[key.strip()] = val.strip()
            
    return {
        "triage_result": result.get("TRIAGE", "notify_human"),
        "category": result.get("CATEGORY", "Other"),
        "agent_action": result.get("ACTION", "Archive"),
        "reasoning": result.get("REASONING", "Processed by agent.")
    }

from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.tools import tool
import sqlite3

# Set up persistent memory (Checkpointer)
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# Simple cross-thread preference memory
def get_preferences(user_id="default"):
    pref_conn = sqlite3.connect("preferences.sqlite", check_same_thread=False)
    pref_conn.execute("CREATE TABLE IF NOT EXISTS prefs (user_id TEXT, preference TEXT)")
    cursor = pref_conn.cursor()
    cursor.execute("SELECT preference FROM prefs WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    return " ".join([r[0] for r in rows if r])

def store_preference(pref: str, user_id="default"):
    pref_conn = sqlite3.connect("preferences.sqlite", check_same_thread=False)
    pref_conn.execute("CREATE TABLE IF NOT EXISTS prefs (user_id TEXT, preference TEXT)")
    pref_conn.execute("INSERT INTO prefs (user_id, preference) VALUES (?, ?)", (user_id, pref))
    pref_conn.commit()

# Define some mock tools for the agent
@tool
def read_calendar(date: str) -> str:
    """Read the calendar for a specific date. Safe tool."""
    return f"Calendar for {date}: 10:00 AM - Team Sync, 2:00 PM - Project Review."

@tool
def send_email(to_email: str, subject: str, body: str) -> str:
    """Send an email. DANGEROUS TOOL - Requires Human Approval."""
    return f"Email sent to {to_email} with subject '{subject}'"

def agent_loop_node(state: AgentState):
    """
    A more advanced reasoning loop.
    In Milestone 2, this is where the agent decides WHICH tool to use based on the triage.
    """
    if state["triage_result"] == "respond/act":
        action_name = state["agent_action"]
        
        # Simulated reasoning based on category
        if "calendar" in action_name.lower():
            # In a full React loop, the LLM would call this tool itself
            tool_output = read_calendar.invoke({"date": "today"})
            new_reasoning = state["reasoning"] + f" [Action: Checked calendar -> {tool_output}] (Waiting for permission to invite)"
            
        elif "accounts" in action_name.lower():
             new_reasoning = state["reasoning"] + " [Action: Prepared forwarding email to Accounts] (PAUSED: Pending Human Approval to send!)"
             
        else:
             new_reasoning = state["reasoning"] + " [Action: Prepared response] (PAUSED: Pending Human Approval to send!)"
             
        return {"reasoning": new_reasoning}
        
    return {}

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("triage", triage_node)
workflow.add_node("agent_loop", agent_loop_node)

# Define edges
workflow.set_entry_point("triage")

def route_after_triage(state: AgentState):
    if state["triage_result"] == "respond/act":
        return "agent_loop"
    return END

workflow.add_conditional_edges("triage", route_after_triage)
workflow.add_edge("agent_loop", END)

# Compile with Checkpointer and HITL interrupt
app = workflow.compile(
    checkpointer=memory,
    # We interrupt BEFORE the agent_loop executes critical actions so a human can approve it
    interrupt_before=["agent_loop"]
)

def process_email(content: str, thread_id: str = "thread-1"):
    """Entry point for the application to process an email using memory."""
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "email_content": content,
        "triage_result": "",
        "reasoning": "",
        "category": "",
        "agent_action": ""
    }
    
    # We call stream/invoke with config for state tracking
    result = app.invoke(initial_state, config=config)
    return result
