from __future__ import annotations

from typing import Any

from ..llm import LLMClient
from ..models import ConversationState, TurnResult, WorkflowStage
from ..prompts import build_system_prompt
from ..sop_loader import sop_to_prompt_block


class FAQStage:
    """Stage 1: Answer customer questions strictly from the SOP."""

    def __init__(self, llm: LLMClient, sop: dict[str, Any]) -> None:
        self.llm = llm
        self.sop = sop
        self.system = build_system_prompt(
            sop.get("business_name", "the clinic"),
            sop_to_prompt_block(sop),
        )

    def respond(self, state: ConversationState, customer_message: str) -> TurnResult:
        transcript = "\n".join(state.transcript_lines())
        user = (
            f"Current workflow stage: {state.stage.value}\n"
            f"Unanswered SOP gaps so far: {state.unanswered_sop_count}\n"
            f"Transcript:\n{transcript}\n\n"
            f"Latest customer message:\n{customer_message}\n\n"
            "Reply to the customer following all rules. Workflow stage is FAQ — do not ask lead qualification questions; suggest /qualify instead. Always set stage_hint to 'faq'."
        )
        data = self.llm.complete_json(self.system, user)
        return TurnResult(
            assistant_message=data.get("assistant_message", "How can I help you today?"),
            confidence=float(data.get("confidence", 0.5)),
            should_escalate=bool(data.get("should_escalate", False)),
            escalation_reason=data.get("escalation_reason"),
            escalation_detail=data.get("escalation_detail"),
            sop_gap=bool(data.get("sop_gap", False)),
            stage=WorkflowStage.FAQ,
            raw=data,
        )
