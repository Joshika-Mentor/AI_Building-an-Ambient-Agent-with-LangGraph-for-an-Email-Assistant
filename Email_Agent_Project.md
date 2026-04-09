from google.colab import drive
drive.mount('/content/drive')
import zipfile
import os

zip_path = "/content/drive/MyDrive/email_dataset/emails.csv.zip"
extract_path = "/content/drive/MyDrive/email_dataset"

os.makedirs(extract_path, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

print("Dataset extracted to:", extract_path)
import pandas as pd

csv_path = "/content/drive/MyDrive/email_dataset/emails.csv"
df = pd.read_csv(csv_path)

print("Dataset loaded successfully!")
print(df.head())
import re

def parse_email(raw_text):
    headers = {}
    for line in raw_text.split("\n"):
        if line.startswith("Message-ID:"):
            headers["Message-ID"] = line.replace("Message-ID:", "").strip()
        elif line.startswith("From:"):
            headers["From"] = line.replace("From:", "").strip()
        elif line.startswith("Subject:"):
            headers["Subject"] = line.replace("Subject:", "").strip()
    return headers

parsed = df["message"].apply(parse_email)
parsed_df = pd.DataFrame(parsed.tolist())

print(parsed_df.head())
def categorize(subject):
    if subject is None:
        return "Unknown"
    subject = str(subject).lower()
    
    if "meeting" in subject or "schedule" in subject:
        return "Work"
    elif "invoice" in subject or "payment" in subject:
        return "Finance"
    elif "party" in subject or "invitation" in subject:
        return "Personal"
    else:
        return "Other"

parsed_df["Category"] = parsed_df["Subject"].apply(categorize)
parsed_df.to_csv("/content/drive/MyDrive/email_dataset/categorized_emails.csv", index=False)

print("Categorized dataset saved to Drive!")
def agent_action(row):
    if row["Category"] == "Work":
        return "Add to calendar / notify team"
    elif row["Category"] == "Finance":
        return "Forward to accounts department"
    elif row["Category"] == "Personal":
        return "Mark as personal / no action"
    else:
        return "Archive"

parsed_df["Agent_Action"] = parsed_df.apply(agent_action, axis=1)
parsed_df.to_csv("/content/drive/MyDrive/email_dataset/final_email_assistant.csv", index=False)

print("Final assistant dataset saved to Drive!")
import matplotlib.pyplot as plt

# Plotting the top 10 subject distributions
action_counts = parsed_df['Subject'].value_counts().head(10)
explode = [0.05] * len(action_counts)

action_counts.plot(
    kind="pie",
    autopct="%1.1f%%",
    figsize=(7, 7),
    startangle=90,
    explode=explode
)

plt.title("Email Subject Distribution")
plt.ylabel("")
plt.show()
