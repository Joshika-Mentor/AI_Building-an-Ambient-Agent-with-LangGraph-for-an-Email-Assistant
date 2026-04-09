import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from src.agent.graph import build_graph
from src.utils.gmail_client import fetch_recent_emails

load_dotenv()

st.set_page_config(page_title="Ambient Email Triage", page_icon="📬", layout="wide")

st.sidebar.title("🔑 Configuration")
st.sidebar.markdown("This agent requires a Gemini API Key to reason about emails.")
user_api_key = st.sidebar.text_input("Gemini API Key (AIza...)", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))
if user_api_key and user_api_key != "your_gemini_api_key_here":
    os.environ["GOOGLE_API_KEY"] = user_api_key
else:
    st.sidebar.warning("API Key not set! The agent will fail to triage emails.")

# Premium Theme Styling (Stitch-inspired dark mode)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    .stApp { background: linear-gradient(135deg, #09090b 0%, #17172b 100%); color: #e2e8f0; }
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white; border: none; border-radius: 8px; font-weight: 600; transition: all 0.3s ease; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stButton>button:hover {
        transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(139, 92, 246, 0.4); border-color: rgba(255, 255, 255, 0.3);
    }
    h1 { background: -webkit-linear-gradient(45deg, #60a5fa, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; letter-spacing: -0.5px; }
    h2, h3 { color: #f1f5f9; font-weight: 600; }
    .hitl-box { background: rgba(244,63,94,0.1); border-left: 4px solid #f43f5e; padding: 15px; border-radius: 8px; margin: 15px 0;}
    .success-box { background: rgba(16,185,129,0.1); border-left: 4px solid #10b981; padding: 15px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("📬 Ambient Email Agent (Full Project)")
st.markdown("**LangGraph** + **Gemini** + **SQLite Checkpointing** + **Gmail API**")

@st.cache_resource
def init_graph():
    return build_graph()

graph = init_graph()

tab1, tab2, tab3 = st.tabs(["📥 Live Inbox Analysis", "🛑 HITL Checkpoint", "⚙️ Settings"])

with tab1:
    st.subheader("Live Inbox Agent Activity")
    st.markdown("The **Ambient Agent** is continuously polling in the background. Here is the processed email history.")
    
    if st.button("🔄 Refresh Dashboard", type="primary"):
        pass # Streamlit natively reruns on button click
        
    try:
        import sqlite3
        conn = sqlite3.connect("memory.db")
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT thread_id FROM checkpoints")
        threads = cur.fetchall()
        
        if not threads:
            st.info("No emails processed yet by the agent. Ensure `ambient_worker.py` is running.")
        
        for (thread_id,) in reversed(threads):
            config = {"configurable": {"thread_id": thread_id}}
            state_sn = graph.get_state(config)
            
            email = state_sn.values.get("email", {})
            t_cat = state_sn.values.get("triage_result", "unknown")
            if not t_cat: t_cat = "unknown"
            reasoning = state_sn.values.get("triage_reasoning", "No reasoning available.")
            
            badge_color = "#3b82f6"
            if t_cat == "respond": badge_color = "#10b981"
            elif t_cat == "ignore": badge_color = "#64748b"
            elif t_cat == "notify_human": badge_color = "#f43f5e"
            
            st.markdown("---")
            st.markdown(f"**From:** {email.get('sender')} | **Subject:** {email.get('subject')}")
            st.markdown(f'''
            <div style="background: rgba(255,255,255,0.05); border-left: 4px solid {badge_color}; padding: 10px; border-radius: 8px;">
                <p style="margin:0;"><strong>Triage Decision:</strong> {t_cat.upper()} <br> <em>{reasoning}</em></p>
            </div>
            ''', unsafe_allow_html=True)
            
            if state_sn.next:
                st.error(f"⏳ Action Paused (Message ID: `{thread_id}`). See HITL tab.")
                
        conn.close()
    except Exception as e:
        st.warning(f"Could not load state: {e}")


with tab2:
    st.subheader("Awaiting Human Approval")
    try:
        import sqlite3
        conn = sqlite3.connect("memory.db")
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT thread_id FROM checkpoints")
        threads = cur.fetchall()
        
        pending_found = False
        for (thread_id,) in threads:
            config = {"configurable": {"thread_id": thread_id}}
            state_sn = graph.get_state(config)
            
            if state_sn.next:
                pending_found = True
                st.markdown(f"<div class='hitl-box'><strong>Action Required (Thread `{thread_id}`):</strong> The agent wants to execute a dangerous tool: <code>{state_sn.next[0]}</code></div>", unsafe_allow_html=True)
                
                try:
                    last_msg = state_sn.values.get("messages", [])[-1]
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        args = last_msg.tool_calls[0].get('args', {})
                        
                        st.write(f"**To:** {args.get('to_email', 'unknown')}")
                        st.write(f"**Subject:** {args.get('subject', 'unknown')}")
                        
                        edited_draft = st.text_area("Review & Edit Draft", value=args.get("body", ""), height=150, key=f"draft_{thread_id}")
                        
                        col_a, col_b, col_c = st.columns(3)
                        if col_a.button("✅ Approve + Send", key=f"app_{thread_id}"):
                            graph.update_state(config, {"human_decision": "approve", "human_edit_content": edited_draft})
                            with st.spinner("Executing and finalizing..."):
                                graph.invoke(None, config=config)
                            st.success("Sent successfully!")
                            st.rerun()
                            
                        if col_b.button("❌ Deny Action", key=f"den_{thread_id}"):
                            graph.update_state(config, {"human_decision": "deny"})
                            with st.spinner("Updating state..."):
                                graph.invoke(None, config=config)
                            st.warning("Action denied and logged.")
                            st.rerun()
                except Exception as e:
                    st.write(f"Could not parse tool call: {e}")
                    
        if not pending_found:
            st.success("No pending actions. The inbox is clear!")
        conn.close()
    except Exception as e:
        st.warning(f"Could not query pending actions: {e}")

with tab3:
    st.subheader("Configuration")
    st.markdown("Ensure your API Keys are active in your local `.env`")
    col1, col2 = st.columns(2)
    has_google = "GOOGLE_API_KEY" in os.environ
    col1.metric("Local Gemini Key", "Found" if has_google else "Missing")
    has_creds = os.path.exists("credentials.json")
    col2.metric("Gmail OAuth credentials.json", "Found" if has_creds else "Missing (Mock Mode Enabled)")
    if not has_creds:
        st.info("Since credentials.json isn't present, the Gmail API is operating in MOCK mode to protect crashes. To go live, pull OAuth creds from Google Cloud Console.")
