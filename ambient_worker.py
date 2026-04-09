import time
import os
import sqlite3
from dotenv import load_dotenv
from src.agent.graph import build_graph
from src.utils.gmail_client import fetch_recent_emails

load_dotenv()

def run_ambient_loop(interval_sec=10):
    print("Starting Ambient Email Agent Worker...")
    db_path = "memory.db"
    graph = build_graph(db_path)
    
    while True:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Polling for new emails...")
        emails = fetch_recent_emails(max_results=5)
        
        # connect to db to see what we've processed
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        for email in emails:
            thread_id = email['message_id']
            # Check if this thread exists
            try:
                cur.execute("SELECT thread_id FROM checkpoints WHERE thread_id = ?", (thread_id,))
                exists = cur.fetchone()
            except sqlite3.OperationalError:
                # Table might not exist yet if no graph runs have happened
                exists = None
                
            if exists:
                continue
                
            print(f"Processing NEW email: {email['subject']} from {email['sender']}")
            config = {"configurable": {"thread_id": thread_id}}
            initial_state = {
                "email": email,
                "messages": [],
                "triage_result": None,
                "triage_reasoning": None,
                "status": "starting"
            }
            try:
                graph.invoke(initial_state, config=config)
                # Check if interrupted for HITL
                state_sn = graph.get_state(config)
                if state_sn.next:
                    print(f"🛑 Thread {thread_id} interrupted! Awaiting Human Approval.")
                else:
                    print(f"✅ Thread {thread_id} completed.")
            except Exception as e:
                print(f"Error invoking graph: {e}")
                
        conn.close()
        time.sleep(interval_sec)

if __name__ == "__main__":
    run_ambient_loop()
