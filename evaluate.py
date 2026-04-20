import os
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate
from backend.agent import process_email

load_dotenv()

# Ensure you have LANGSMITH_API_KEY set in .env
client = Client()

def create_dataset():
    """Create a sample golden dataset for evaluation."""
    dataset_name = "Email_Agent_Eval"
    try:
        # Check if dataset exists to avoid recreating
        return client.read_dataset(dataset_name=dataset_name)
    except:
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Golden dataset for email agent triage and response."
        )
        
        examples = [
            ("Can we meet tomorrow at 10am to discuss the Q3 report?", "Work", "respond/act"),
            ("Your invoice #1234 is overdue for payment.", "Finance", "respond/act"),
            ("Are you coming to the party this weekend?", "Personal", "notify_human"),
            ("New login detected on your account.", "Other", "notify_human")
        ]
        
        for email, expected_cat, expected_triage in examples:
            client.create_example(
                inputs={"email_content": email},
                outputs={"category": expected_cat, "triage_result": expected_triage},
                dataset_id=dataset.id
            )
        return dataset

def exact_match_evaluator(run, example):
    """Simple evaluator checking if the expected category matches the agent's output."""
    expected_category = example.outputs.get("category")
    actual_category = run.outputs.get("category")
    
    score = 1 if expected_category == actual_category else 0
    return {"key": "category_accuracy", "score": score}

def run_evaluation():
    dataset = create_dataset()
    print(f"Dataset ready. Running evaluations...")
    
    def target_function(inputs):
        result = process_email(inputs["email_content"])
        return result
        
    evaluate(
        target_function,
        data=dataset.name,
        evaluators=[exact_match_evaluator],
        experiment_prefix="Triage-Accuracy-Eval"
    )
    print("Evaluation complete! View results in LangSmith.")

if __name__ == "__main__":
    run_evaluation()
