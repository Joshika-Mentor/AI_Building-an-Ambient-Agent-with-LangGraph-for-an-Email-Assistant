import os
import time
from dotenv import load_dotenv

# Load env variables before importing anything that might need it
load_dotenv()

from gmail_tools import authenticate_gmail, fetch_unread_emails, mark_as_read, create_draft_reply, send_draft
from agent import graph

def run_ambient_agent():
    print("Getting Gmail Service...")
    service = authenticate_gmail()
    if not service:
        print("Failed to authenticate.")
        return
        
    print("Checking for new emails...")
    unread = fetch_unread_emails(service, max_results=3)
    
    if not unread:
        print("No new emails found.")
        return
        
    for email in unread:
        print(f"\n--- Processing Email ---\nSubject: {email['subject']}\nFrom: {email['sender']}")
        
        config = {"configurable": {"thread_id": email['threadId']}}
        state = {"email": email}
        
        # Stream the graph until it interrupts
        for event in graph.stream(state, config, stream_mode="values"):
            pass
            
        current_state = graph.get_state(config)
        
        if current_state.next:
            if "human_review" in current_state.next:
                draft_content = current_state.values.get("draft_content")
                print("\n[AGENT DECISION]: Respond")
                print("\n--- PROPOSED DRAFT ---")
                print(draft_content)
                print("----------------------\n")
                
                action = input("Approve this draft and send? (y/n): ")
                
                if action.lower() == 'y':
                    print("Sending email...")
                    to_email = email['sender']
                    if '<' in to_email and '>' in to_email:
                        to_email = to_email.split('<')[1].split('>')[0]
                        
                    draft = create_draft_reply(
                        service=service, 
                        msg_id=email['id'], 
                        thread_id=email['threadId'], 
                        to=to_email, 
                        original_subject=email['subject'], 
                        draft_content=draft_content
                    )
                    
                    if draft:
                        send_draft(service, draft['id'])
                        print("Draft sent!")
                        
                    graph.update_state(config, {"action": "approve"})
                    for event in graph.stream(None, config, stream_mode="values"):
                        pass
                
                else:
                    print("Draft discarded.")
                    graph.update_state(config, {"action": "discard"})
                    for event in graph.stream(None, config, stream_mode="values"):
                        pass
                
                mark_as_read(service, email['id'])
        else:
            print(f"[AGENT DECISION]: Ignore")
            mark_as_read(service, email['id'])
            
if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY is not set in .env")
        
    if not os.path.exists('credentials.json'):
        print("WARNING: credentials.json is missing.")
        print("Go to Google Cloud Platform Console -> APIs & Services -> Credentials.")
        print("Create OAuth client ID -> Desktop App, and download JSON as 'credentials.json'.\n")
        
    print("Ambient Email Agent started...")
    
    while True:
        try:
            run_ambient_agent()
            print("\nSleeping for 30 seconds... (Press Ctrl+C to exit)")
            time.sleep(30)
        except KeyboardInterrupt:
            print("\nExiting.")
            break
