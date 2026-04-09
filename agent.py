import os
from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Define state properties
class AgentState(TypedDict):
    email: Dict  # Current email being processed
    triage_result: str  # e.g., 'ignore', 'respond'
    draft_content: str  # Optional generated response
    draft_id: str  # Optional generated draft id
    action: str  # what happens next (approve, edit, discard)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def triage_email(state: AgentState) -> AgentState:
    """Determine if email needs a response."""
    email = state["email"]
    
    prompt = f"""You are an intelligent email assistant. Read the following email and decide if it requires a response.
    If it is a newsletter, promotional, automated, or informational email that does not ask a question or require acknowledgment, output 'ignore'.
    If it is from a real person asking a question, requiring action, or needing acknowledgment, output 'respond'.
    
    Email Subject: {email['subject']}
    From: {email['sender']}
    Body:
    {email['body']}
    
    Decision (must be exactly 'ignore' or 'respond'):"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    decision = response.content.strip().lower()
    if decision not in ['ignore', 'respond']:
        decision = 'ignore' # fallback
    
    return {"triage_result": decision}

def draft_response(state: AgentState) -> AgentState:
    """Draft a response if triaged to 'respond'."""
    email = state["email"]
    
    prompt = f"""You are an intelligent email assistant. Draft a polite, concise, and helpful reply to the following email.
    
    Email Subject: {email['subject']}
    From: {email['sender']}
    Body:
    {email['body']}
    
    Draft Response:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    draft_content = response.content.strip()
    
    return {"draft_content": draft_content}

def human_review(state: AgentState) -> AgentState:
    """
    This is an interrupt point for human review.
    """
    return state

# Routing logic
def route_triage(state: AgentState) -> str:
    if state["triage_result"] == "respond":
        return "draft"
    else:
        return "ignore"

def route_review(state: AgentState) -> str:
    action = state.get("action", "approve")
    if action == "approve":
        return "send"
    elif action == "discard":
        return "discard"
    else:
        return "send"

# Build graph
workflow = StateGraph(AgentState)

workflow.add_node("triage", triage_email)
workflow.add_node("draft", draft_response)
workflow.add_node("human_review", human_review)

workflow.add_edge(START, "triage")
workflow.add_conditional_edges("triage", route_triage, {"draft": "draft", "ignore": END})
workflow.add_edge("draft", "human_review")
workflow.add_edge("human_review", END) # Sending handled outside or manually tracked

from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory, interrupt_before=["human_review"])
