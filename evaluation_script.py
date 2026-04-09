import os
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from src.agent.graph import build_graph

load_dotenv()

# We will test the Triage Node independently as an example of "Agent Quality Score"
def predict_triage(inputs: dict) -> dict:
    """Wrapper for the LangSmith evaluator to test the Triage Node."""
    graph = build_graph("memory_eval.db")
    # Execute just the triage node
    state = {"email": inputs, "messages": []}
    
    # We can invoke the graph but tell it to stop early if needed, or just let it run.
    # For a pure triage eval, it's easier to invoke the graph and get the final state.
    # But for full evaluation, we let it run end-to-end to draft the email.
    config = {"configurable": {"thread_id": inputs.get("message_id")}}
    res = graph.invoke(state, config=config)
    
    # Extract the drafted reply from the last tool call (if any)
    drafted_reply = ""
    if res.get("messages"):
        last_msg = res["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            drafted_reply = last_msg.tool_calls[0].get("args", {}).get("body", "")
            
    return {
        "triage_category": res.get("triage_result"),
        "drafted_reply": drafted_reply
    }

def main():
    if "your_langsmith_api_key_here" in os.environ.get("LANGCHAIN_API_KEY", ""):
        print("Please set your LANGCHAIN_API_KEY in .env to run this evaluation.")
        return

    csv_path = "/content/drive/MyDrive/Colab Notebooks/Project/final_email_assistant.csv"
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Ensure you have run the data notebook.")
        return
        
    df = pd.read_csv(csv_path)
    # We sample 10 from the 100+ dataset to do a quick evaluation run
    sample_df = df.head(10)
    
    dataset_name = "Email Assistant Eval Dataset"
    
    # In a real environment, you'd create the dataset in LangSmith first:
    # client = Client()
    # dataset = client.create_dataset(dataset_name, description="100+ Emails")
    # client.create_examples(inputs=[...], outputs=[...], dataset_id=dataset.id)
    
    # Setup LLM-as-a-judge
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0)
    
    qa_evaluator = LangChainStringEvaluator(
        "qa",
        config={"llm": llm},
        prepare_data=lambda run, example: {
            "prediction": run.outputs["drafted_reply"],
            "reference": example.outputs["ideal_reply"],
            "input": example.inputs["body"]
        }
    )
    
    # For criteria evaluating polite tone:
    criteria_evaluator = LangChainStringEvaluator(
        "criteria",
        config={
            "criteria": {
                "polite": "Is the prediction's tone polite, professional, and helpful?"
            },
            "llm": llm
        },
        prepare_data=lambda run, example: {
            "prediction": run.outputs["drafted_reply"],
            "input": example.inputs["body"]
        }
    )
    
    print("Initiating evaluation run in LangSmith...")
    # evaluate(
    #     predict_triage,
    #     data=dataset_name,
    #     evaluators=[qa_evaluator, criteria_evaluator],
    #     experiment_prefix="ambient-agent-v1"
    # )
    print("Run `langchain evaluation` on your full dataset to see metrics on the LangSmith UI.")

if __name__ == "__main__":
    main()
