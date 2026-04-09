import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    # Context
    email: dict  # Contains subject, sender, body, message_id
    user_preferences: dict

    # Triage Phase
    triage_result: Optional[str]      # e.g., "ignore", "respond", "notify_human"
    triage_reasoning: Optional[str]

    # ReAct Phase
    messages: Annotated[list[AnyMessage], operator.add]
    
    # HITL Phase
    pending_action: Optional[dict]    # Action the agent wants to take (tool call)
    human_decision: Optional[str]     # "approve", "deny", "edit"
    human_edit_content: Optional[str] # Edited content if user selected "edit"
    
    # Final Outcome
    status: str                       # e.g., "in_progress", "done", "paused"
    final_output: Optional[str]
