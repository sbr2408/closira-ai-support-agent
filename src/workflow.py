from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .llm import LLMClient
from .models import ConversationState, WorkflowStage
from .sop_loader import load_sop
from .stages import EscalationStage, FAQStage, QualificationStage, SummaryStage


class SupportWorkflow:
    """Orchestrates the four assignment stages in a single conversation session."""

    def __init__(self, sop: dict[str, Any] | None = None, *, mock: bool = False) -> None:
        self.sop = sop or load_sop()
        self.llm = LLMClient(mock=mock)
        self.faq = FAQStage(self.llm, self.sop)
        self.qualification = QualificationStage(self.sop)
        self.escalation = EscalationStage(self.llm, self.sop)
        self.summary = SummaryStage(self.llm, self.sop)
        self.state = ConversationState()
        self.log_dir = Path(__file__).resolve().parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

    def greeting(self) -> str:
        name = self.sop.get("business_name", "our clinic")
        msg = (
            f"Hello! You have reached {name}. I can help with our services, hours, and booking. "
            "How can I assist you today? (Type /end to finish, /qualify to start lead questions)"
        )
        self.state.add("assistant", msg)
        return msg

    def handle_user_message(self, text: str) -> str:
        text = text.strip()
        if not text:
            return "Please send a message or type /end to finish."

        if text.lower() in ("/end", "/quit", "/summary"):
            return self.end_session()

        if text.lower() == "/qualify":
            reply = self.qualification.start(self.state)
            self.state.add("user", text)
            self.state.add("assistant", reply)
            return reply

        self.state.add("user", text)

        if self.state.escalated:
            reply = (
                "Your conversation has been escalated to our team. "
                "A human agent will follow up shortly. Type /end for a session summary."
            )
            self.state.add("assistant", reply)
            return reply

        # Stage 3: pre-check escalation on raw message
        pre = self.escalation.check_message(self.state, text)
        if pre:
            self._escalate(pre)
            reply = (
                "I am connecting you with a member of our team who can help further. "
                f"(Reason: {pre.reason} — {pre.detail})"
            )
            self.state.add("assistant", reply)
            return reply

        # Stage 2: qualification flow (code-driven — not the FAQ model)
        if self.qualification.is_complete(self.state):
            if self.qualification.is_active(self.state):
                reply = (
                    "Qualification is complete. Type /end for a summary, "
                    "or ask a question about our services."
                )
                self.state.stage = WorkflowStage.FAQ
                self.state.add("assistant", reply)
                return reply
        elif self.qualification.awaiting_answer(self.state) or self.qualification.resume_if_pending(
            self.state
        ):
            reply = self.qualification.record_answer(self.state, text)
            self.state.add("assistant", reply)
            return reply

        if self.qualification.should_start(self.state, text):
            reply = self.qualification.start(self.state)
            self.state.add("assistant", reply)
            return reply

        # Stage 1: FAQ
        turn = self.faq.respond(self.state, text)
        event = self.escalation.apply_turn_flags(
            self.state,
            text,
            confidence=turn.confidence,
            should_escalate=turn.should_escalate,
            escalation_reason=turn.escalation_reason,
            escalation_detail=turn.escalation_detail,
            sop_gap=turn.sop_gap,
        )
        if event:
            self._escalate(event)
            reply = turn.assistant_message
            if "connect" not in reply.lower() and "team" not in reply.lower():
                reply += " I am flagging this for a team member to follow up."
        else:
            reply = turn.assistant_message

        self.state.add("assistant", reply)
        return reply

    def end_session(self) -> str:
        self.state.ended = True
        self.state.stage = WorkflowStage.SUMMARY
        summary = self.summary.generate(self.state)
        self._write_summary_log(summary.raw_text)
        self.state.add("assistant", summary.raw_text)
        return summary.raw_text

    def _escalate(self, event: Any) -> None:
        self.escalation.record(self.state, event)
        self._write_escalation_log(event)

    def _write_escalation_log(self, event: Any) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": event.reason,
            "detail": event.detail,
            "customer_message": event.customer_message,
        }
        path = self.log_dir / "escalations.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _write_summary_log(self, text: str) -> None:
        path = self.log_dir / "summaries.txt"
        with path.open("a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.now(timezone.utc).isoformat()} ---\n{text}\n")
