import os
import sqlite3
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from src.agent.state import AgentState
from src.agent.tools import ALL_TOOLS, SAFE_TOOLS, DANGEROUS_TOOLS

def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0)

def triage_node(state: AgentState):
    """Categorizes the email."""
    llm = get_llm()
    email = state.get("email", {})
    prefs = state.get("user_preferences", {})
    
    prompt = f"""You are an expert email triage assistant.
    Analyze the following email:
    From: {email.get('sender')}
    Subject: {email.get('subject')}
    Body: {email.get('body')}
    
    User Preferences context: {prefs}
    
    Categorize this email into exactly one of three categories:
    1. "ignore": For spam, newsletters, or emails requiring absolutely no attention.
    2. "notify_human": For urgent, sensitive, or critical legal/financial issues requiring immediate human eyes.
    3. "respond": For typical inquiries, scheduling, or operational emails that you can draft a reply for.
    
    Return ONLY a valid JSON object string with two keys: "category" and "reason".
    Example: {{"category": "respond", "reason": "Requires scheduling a meeting."}}
    """
    
    # Simple JSON extraction
    try:
        raw_res = llm.invoke([HumanMessage(content=prompt)]).content
        import json
        import re
        match = re.search(r'\{.*\}', raw_res, re.DOTALL)
        if match:
            res_dict = json.loads(match.group(0))
            return {
                "triage_result": res_dict.get("category", "notify_human"),
                "triage_reasoning": res_dict.get("reason", "Fallback")
            }
        else:
            return {"triage_result": "notify_human", "triage_reasoning": "Parse error."}
    except Exception as e:
        return {"triage_result": "notify_human", "triage_reasoning": str(e)}

def agent_reason_node(state: AgentState):
    """The main reasoning loop that decides which tool to call or if finished."""
    llm = get_llm().bind_tools(ALL_TOOLS)
    
    messages = state.get("messages", [])
    if not messages:
        # Initial message to agent
        email = state.get("email", {})
        sys_prompt = SystemMessage(content="You are a helpful proactive email assistant. Draft responses or use calendar tools to assist.")
        human_msg = HumanMessage(content=f"Please handle this email from {email.get('sender')} with subject '{email.get('subject')}': {email.get('body')}")
        messages = [sys_prompt, human_msg]
        
    response = llm.invoke(messages)
    
    # We might have pending human edits to inject
    human_edit = state.get("human_edit_content")
    if human_edit and state.get("human_decision") == "edit":
        # The human wants to override the tool args for send_email_draft
        pass # In a robust system, we would mutate the tool call args here
        
    return {"messages": [response], "status": "in_progress"}

def execute_safe_tools(state: AgentState):
    """Executes tools that don't need human approval."""
    last_msg = state["messages"][-1]
    results = []
    # Simplified tool execution mapper
    from langchain_core.tools import tool
    tool_map = {t.name: t for t in SAFE_TOOLS}
    
    for tc in last_msg.tool_calls:
        if tc["name"] in tool_map:
            res = tool_map[tc["name"]].invoke(tc["args"])
            results.append(ToolMessage(tool_call_id=tc["id"], name=tc["name"], content=str(res)))
            
    return {"messages": results}

def execute_dangerous_tools(state: AgentState):
    """Executes tools that require human approval."""
    decision = state.get("human_decision", "approve")
    
    if decision == "deny":
        return {"final_output": "Human denied the action.", "status": "done"}
        
    last_msg = state["messages"][-1]
    
    # If the decision was "edit", we want to use the edited content.
    edit_content = state.get("human_edit_content")
    
    results = []
    tool_map = {t.name: t for t in DANGEROUS_TOOLS}
    
    for tc in last_msg.tool_calls:
        if tc["name"] in tool_map:
            args = tc["args"]
            if edit_content and "body" in args:
                args["body"] = edit_content # Inject human edits
                
            res = tool_map[tc["name"]].invoke(args)
            results.append(ToolMessage(tool_call_id=tc["id"], name=tc["name"], content=str(res)))
            
    return {"messages": results, "final_output": "Email sent successfully.", "status": "done"}

def route_triage(state: AgentState) -> Literal["agent_reason", "end"]:
    cat = state.get("triage_result", "")
    if cat == "respond":
        return "agent_reason"
    return "end"

def route_tools(state: AgentState) -> Literal["execute_safe_tools", "execute_dangerous_tools", "end"]:
    messages = state.get("messages", [])
    if not messages:
        return "end"
        
    last_msg = messages[-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        safes = [t.name for t in SAFE_TOOLS]
        dangers = [t.name for t in DANGEROUS_TOOLS]
        
        for tc in last_msg.tool_calls:
            if tc["name"] in dangers:
                return "execute_dangerous_tools"
        return "execute_safe_tools"
    return "end"

def build_graph(db_path="memory.db"):
    workflow = StateGraph(AgentState)
    
    workflow.add_node("triage", triage_node)
    workflow.add_node("agent_reason", agent_reason_node)
    workflow.add_node("execute_safe_tools", execute_safe_tools)
    workflow.add_node("execute_dangerous_tools", execute_dangerous_tools)
    
    workflow.add_edge(START, "triage")
    workflow.add_conditional_edges("triage", route_triage, {"agent_reason": "agent_reason", "end": END})
    workflow.add_conditional_edges("agent_reason", route_tools, {
        "execute_safe_tools": "execute_safe_tools", 
        "execute_dangerous_tools": "execute_dangerous_tools", 
        "end": END
    })
    workflow.add_edge("execute_safe_tools", "agent_reason")
    workflow.add_edge("execute_dangerous_tools", END)
    
    # Setup Persistent Checkpointing
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    # Hitl Checkpoint
    graph = workflow.compile(
        checkpointer=memory,
        interrupt_before=["execute_dangerous_tools"]
    )
    return graph
