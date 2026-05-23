#!/usr/bin/env python3
"""CLI entry point for the Closira-style support workflow."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow running as `python -m src.main` or `python src/main.py`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import LLMError  # noqa: E402
from src.workflow import SupportWorkflow  # noqa: E402


def run_interactive(*, mock: bool) -> None:
    load_dotenv(ROOT / ".env")
    workflow = SupportWorkflow(mock=mock)
    print("\n" + "=" * 60)
    print("Bloom Aesthetics — AI Support Workflow (Closira assignment)")
    print("Commands: /end  /qualify  /quit")
    print("=" * 60 + "\n")
    print(f"Assistant: {workflow.greeting()}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nEnding session...")
            try:
                print(workflow.end_session())
            except LLMError as exc:
                print(f"[API error] {exc}")
            break

        if user_input.lower() in ("/quit", "quit", "exit"):
            try:
                print(f"\nAssistant: {workflow.end_session()}\n")
            except LLMError as exc:
                print(f"\n[API error] {exc}\n")
            break

        try:
            reply = workflow.handle_user_message(user_input)
        except LLMError as exc:
            print(f"\n[API error] {exc}\n")
            print("Tip: use --mock, wait and retry, or set GEMINI_MODEL=gemini-2.5-flash in .env\n")
            continue
        print(f"\nAssistant: {reply}\n")

        if workflow.state.ended:
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="AI customer support workflow CLI")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run without Gemini API (deterministic demo responses)",
    )
    args = parser.parse_args()
    run_interactive(mock=args.mock)


if __name__ == "__main__":
    main()
