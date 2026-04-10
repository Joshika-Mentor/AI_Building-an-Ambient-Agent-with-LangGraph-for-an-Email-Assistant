import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Email Assistant", layout="wide")

st.title("📧 AI Email Assistant Dashboard")

# Load your final output file
df = pd.read_csv("final_email_assistant.csv")

# Sidebar filter
st.sidebar.header("Filter Emails")

category = st.sidebar.selectbox(
    "Select Category",
    ["All", "Work", "Finance", "Personal", "Other"]
)

if category != "All":
    df = df[df["Category"] == category]

# Show dataset
st.subheader("📨 Email Data")
st.dataframe(df)

# Show agent actions
st.subheader("🤖 Agent Decisions")
st.dataframe(df[["From", "Subject", "Category", "Agent Action"]])

# Pie chart
st.subheader("📊 Action Distribution")

action_counts = df["Agent Action"].value_counts()

fig, ax = plt.subplots()
ax.pie(action_counts, labels=action_counts.index, autopct="%1.1f%%")
ax.axis("equal")

st.pyplot(fig)

# Refresh button
if st.button("🔄 Refresh Data"):
    st.rerun()