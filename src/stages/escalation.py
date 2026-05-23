from __future__ import annotations

import json
import os
import re
from typing import Any

from ..llm import LLMClient
from ..models import ConversationState, EscalationEvent
from ..prompts import ESCALATION_CHECK_PROMPT

# Fast local checks before any API call (saves quota; assignment escalation rules).
_RULE_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"\b(complaint|refund|terrible|awful|angry|furious|unacceptable|disgusting)\b",
        "angry_sentiment",
        "Customer complaint or strong negative sentiment",
    ),
    (
        r"\b(speak to (a )?human|real person|talk to (a )?manager|human agent)\b",
        "explicit_request",
        "Customer requested a human agent",
    ),
    (
        r"\b(side effect|allergic|pregnant|medical advice|is it safe|clinical)\b",
        "sop_rule",
        "Medical or clinical question — escalate per SOP",
    ),
    (
        r"\b(discount|cheaper|negotiate|price match|best price)\b",
        "sop_rule",
        "Pricing negotiation — escalate per SOP",
    ),
]


class EscalationStage:
    """Stage 3: Detect when to hand off to a human and log the reason."""

    CONFIDENCE_THRESHOLD = 0.6
    MAX_UNANSWERED = 2

    def __init__(self, llm: LLMClient, sop: dict[str, Any]) -> None:
        self.llm = llm
        self.sop = sop
        self.rules = sop.get("escalation_rules", [])
        self._use_llm_check = os.getenv("LLM_ESCALATION_CHECK", "false").lower() in (
            "1",
            "true",
            "yes",
        )

    def check_message_rules(self, customer_message: str) -> EscalationEvent | None:
        lower = customer_message.lower()
        for pattern, reason, detail in _RULE_PATTERNS:
            if re.search(pattern, lower):
                return EscalationEvent(
                    reason=reason,
                    detail=detail,
                    customer_message=customer_message,
                )
        return None

    def check_message(self, state: ConversationState, customer_message: str) -> EscalationEvent | None:
        ruled = self.check_message_rules(customer_message)
        if ruled:
            return ruled

        if self.llm.mock or not self._use_llm_check:
            return None

        prompt = ESCALATION_CHECK_PROMPT.format(escalation_rules=json.dumps(self.rules))
        context = "\n".join(state.transcript_lines()[-8:])
        user = f"Recent transcript:\n{context}\n\nLatest customer message:\n{customer_message}"
        data = self.llm.complete_json(prompt, user)
        if data.get("should_escalate"):
            return EscalationEvent(
                reason=data.get("escalation_reason") or "sop_rule",
                detail=data.get("escalation_detail") or "Escalation trigger detected",
                customer_message=customer_message,
            )
        return None

    def apply_turn_flags(
        self,
        state: ConversationState,
        customer_message: str,
        *,
        confidence: float,
        should_escalate: bool,
        escalation_reason: str | None,
        escalation_detail: str | None,
        sop_gap: bool,
    ) -> EscalationEvent | None:
        if sop_gap:
            state.unanswered_sop_count += 1
            state.sop_gaps.append(customer_message)

        if state.unanswered_sop_count > self.MAX_UNANSWERED:
            return EscalationEvent(
                reason="unanswered_limit",
                detail=f"More than {self.MAX_UNANSWERED} SOP gaps in this session",
                customer_message=customer_message,
            )

        if confidence < self.CONFIDENCE_THRESHOLD and not should_escalate:
            should_escalate = True
            escalation_reason = escalation_reason or "low_confidence"
            escalation_detail = escalation_detail or f"Confidence {confidence:.2f} below threshold"

        if should_escalate:
            return EscalationEvent(
                reason=escalation_reason or "sop_rule",
                detail=escalation_detail or "Model flagged escalation",
                customer_message=customer_message,
            )
        return None

    def record(self, state: ConversationState, event: EscalationEvent) -> None:
        state.escalations.append(event)
        state.escalated = True
        from ..models import WorkflowStage

        state.stage = WorkflowStage.ESCALATED
