"""Entry point to run the Email Assistant Agent."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.email_agent import create_agent


def main():
    """Run the email agent."""
    print("=" * 50)
    print("  Email Assistant Agent - Internship Project")
    print("=" * 50)
    print()

    agent = create_agent()
    result = agent.invoke({})

    print(f"\n{'=' * 50}")
    print(f"  SUMMARY: Processed {len(result['responses'])} emails")
    print(f"{'=' * 50}")

    for i, r in enumerate(result['responses'], 1):
        status = "Sent" if r['sent'] else "Needs Review"
        subject = r['email']['subject'][:35]
        print(f"  {i}. {subject}... [{status}]")


if __name__ == "__main__":
    main()
