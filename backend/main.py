from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .agent import process_email, app as agent_graph, store_preference

app = FastAPI(title="Ambient Email Agent API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailRequest(BaseModel):
    content: str
    thread_id: str = "thread-1"

class DecisionRequest(BaseModel):
    decision: str  # "approve", "deny", or "edit"
    thread_id: str = "thread-1"
    edit_instruction: str = None

@app.post("/classify")
async def classify_email(request: EmailRequest):
    try:
        # Step 1: Run the agent. If it needs to do 'respond/act', it will PAUSE before agent_loop.
        result = process_email(request.content, request.thread_id)
        
        # Check current state using the checkpointer
        config = {"configurable": {"thread_id": request.thread_id}}
        state = agent_graph.get_state(config)
        
        is_paused = len(state.next) > 0 # If true, graph is waiting for approval
        
        return {
            "status": "success",
            "triage": result.get("triage_result", ""),
            "category": result.get("category", ""),
            "action": result.get("agent_action", ""),
            "reasoning": result.get("reasoning", ""),
            "requires_human_approval": is_paused
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/human_decision")
async def handle_decision(request: DecisionRequest):
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        
        if request.decision == "approve":
            # Resume the graph with NO state changes
            result = agent_graph.invoke(None, config=config)
            return {"status": "approved", "final_reasoning": result.get("reasoning", "")}
            
        elif request.decision == "deny":
            # Manually update the state to STOP the workflow
            # We jump out of the paused execution.
            agent_graph.update_state(config, {"reasoning": "Action aborted by Human."})
            return {"status": "denied", "message": "Workflow aborted."}
            
        elif request.decision == "edit" and request.edit_instruction:
            # Store the preference persistently for learning
            store_preference(request.edit_instruction)
            
            # Update the graph state to include the edit and resume
            agent_graph.update_state(config, {"reasoning": f"Human edited: {request.edit_instruction}. Proceeding with edit."})
            result = agent_graph.invoke(None, config=config)
            return {"status": "edited", "final_reasoning": result.get("reasoning", "")}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
