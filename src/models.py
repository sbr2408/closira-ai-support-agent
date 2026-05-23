from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowStage(str, Enum):
    FAQ = "faq"
    QUALIFICATION = "qualification"
    ESCALATED = "escalated"
    SUMMARY = "summary"


class EscalationReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    OUT_OF_SCOPE = "out_of_scope"
    ANGRY_SENTIMENT = "angry_sentiment"
    EXPLICIT_REQUEST = "explicit_request"
    SOP_RULE = "sop_rule"
    UNANSWERED_LIMIT = "unanswered_limit"


@dataclass
class Message:
    role: str
    content: str


@dataclass
class QualificationAnswer:
    question: str
    answer: str


@dataclass
class EscalationEvent:
    reason: str
    detail: str
    customer_message: str


@dataclass
class TurnResult:
    assistant_message: str
    confidence: float
    should_escalate: bool
    escalation_reason: str | None
    escalation_detail: str | None
    sop_gap: bool
    stage: WorkflowStage
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationState:
    messages: list[Message] = field(default_factory=list)
    stage: WorkflowStage = WorkflowStage.FAQ
    qualification_answers: list[QualificationAnswer] = field(default_factory=list)
    qualification_index: int = 0
    unanswered_sop_count: int = 0
    escalations: list[EscalationEvent] = field(default_factory=list)
    sop_gaps: list[str] = field(default_factory=list)
    escalated: bool = False
    ended: bool = False

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def transcript_lines(self) -> list[str]:
        lines: list[str] = []
        for m in self.messages:
            label = "Customer" if m.role == "user" else "Assistant"
            lines.append(f"{label}: {m.content}")
        return lines


@dataclass
class SessionSummary:
    customer_intent: str
    key_details: list[str]
    qualification_summary: str | None
    sop_gaps: list[str]
    escalation_events: list[str]
    recommended_next_action: str
    raw_text: str
