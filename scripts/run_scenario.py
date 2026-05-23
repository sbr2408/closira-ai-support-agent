#!/usr/bin/env python3
"""Replay a scripted customer conversation (useful for demos and transcript generation)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from src.workflow import SupportWorkflow


def run_script(messages: list[str], *, mock: bool) -> str:
    load_dotenv(ROOT / ".env")
    w = SupportWorkflow(mock=mock)
    lines = [f"Assistant: {w.greeting()}"]
    for msg in messages:
        lines.append(f"Customer: {msg}")
        reply = w.handle_user_message(msg)
        lines.append(f"Assistant: {reply}")
    if not w.state.ended:
        summary = w.end_session()
        lines.append(f"Assistant: {summary}")
    return "\n\n".join(lines)


SCENARIOS = {
    "in_sop": ["What are your Botox prices?", "/end"],
    "out_of_scope": ["Do you have free parking on site?", "/end"],
    "escalation": [
        "I had a terrible experience last time and I want a refund immediately!",
        "/end",
    ],
    "qualification": [
        "/qualify",
        "We run a small salon with 4 staff.",
        "Four people handle enquiries.",
        "We use WhatsApp Business and Gmail.",
        "/end",
    ],
    "summary": [
        "What are your opening hours?",
        "How do I book a consultation?",
        "/end",
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=list(SCENARIOS.keys()))
    parser.add_argument("--mock", action="store_true", default=True)
    parser.add_argument("--live", action="store_true", help="Use real Gemini API")
    args = parser.parse_args()
    mock = not args.live
    transcript = run_script(SCENARIOS[args.scenario], mock=mock)
    print(transcript)


if __name__ == "__main__":
    main()
