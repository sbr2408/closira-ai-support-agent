from __future__ import annotations

import re
from typing import Any

from ..models import ConversationState, QualificationAnswer, WorkflowStage


class QualificationStage:
    """Stage 2: Collect 2–3 structured qualification answers."""

    def __init__(self, sop: dict[str, Any]) -> None:
        self.questions: list[str] = list(sop.get("qualification_questions", []))

    def is_active(self, state: ConversationState) -> bool:
        return state.stage == WorkflowStage.QUALIFICATION

    def awaiting_answer(self, state: ConversationState) -> bool:
        """True when we have asked a question and still need an answer for it."""
        return self.is_active(state) and state.qualification_index < len(self.questions)

    def should_start(self, state: ConversationState, customer_message: str) -> bool:
        if self.is_active(state):
            return False
        triggers = (
            "/qualify",
            "partnership",
            "platform",
            "closira",
            "for my business",
            "for our salon",
            "lead qualification",
            "qualify me",
            "qualify my",
        )
        return _matches_trigger(customer_message, triggers)

    def resume_if_pending(self, state: ConversationState) -> bool:
        """Recover when the FAQ model asked a qual question without switching stage."""
        if self.is_active(state) or self.is_complete(state):
            return False
        last_assistant = _last_assistant_message(state)
        if not last_assistant:
            return False
        pending = self.questions[state.qualification_index]
        if _question_was_asked(pending, last_assistant):
            state.stage = WorkflowStage.QUALIFICATION
            return True
        return False

    def start(self, state: ConversationState) -> str:
        state.stage = WorkflowStage.QUALIFICATION
        return self.next_question(state)

    def next_question(self, state: ConversationState) -> str:
        if state.qualification_index >= len(self.questions):
            return self._completion_message(state)
        q = self.questions[state.qualification_index]
        return f"To help us understand your needs better: {q}"

    def record_answer(self, state: ConversationState, answer: str) -> str:
        if state.qualification_index >= len(self.questions):
            return self._completion_message(state)
        q = self.questions[state.qualification_index]
        state.qualification_answers.append(QualificationAnswer(question=q, answer=answer))
        state.qualification_index += 1
        if state.qualification_index >= len(self.questions):
            return self._completion_message(state)
        return self.next_question(state)

    def is_complete(self, state: ConversationState) -> bool:
        return state.qualification_index >= len(self.questions)

    def summary_text(self, state: ConversationState) -> str:
        if not state.qualification_answers:
            return "No qualification data collected."
        lines = [f"- Q: {a.question}\n  A: {a.answer}" for a in state.qualification_answers]
        return "Lead qualification summary:\n" + "\n".join(lines)

    def _completion_message(self, state: ConversationState) -> str:
        return (
            "Thank you — I have noted your details. "
            + self.summary_text(state).replace("\n", " ")
            + " A team member can follow up if needed. Type /end when you are finished."
        )


def _last_assistant_message(state: ConversationState) -> str | None:
    for m in reversed(state.messages):
        if m.role == "assistant":
            return m.content
    return None


def _question_was_asked(question: str, assistant_text: str) -> bool:
    a = assistant_text.lower()
    # Match distinctive phrase from each SOP question
    markers = [
        "what type of business",
        "how many team members",
        "which tools do you currently use",
    ]
    if any(m in a for m in markers):
        return True
    # Fallback: substantial overlap with the pending question text
    q_words = {w for w in re.findall(r"[a-z]{4,}", question.lower())}
    a_words = set(re.findall(r"[a-z]{4,}", a))
    return len(q_words & a_words) >= 3


def _matches_trigger(message: str, triggers: tuple[str, ...]) -> bool:
    lower = message.lower().strip()
    for t in triggers:
        if t.startswith("/"):
            if lower == t or lower.startswith(t + " "):
                return True
            continue
        if " " in t:
            if t in lower:
                return True
        elif re.search(rf"\b{re.escape(t)}\b", lower):
            return True
    return False
