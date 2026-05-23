from __future__ import annotations

import json
from typing import Any

from ..llm import LLMClient
from ..models import ConversationState, SessionSummary
from ..prompts import SUMMARY_PROMPT
from ..stages.qualification import QualificationStage


class SummaryStage:
    """Stage 4: Structured end-of-session summary for human handoff."""

    def __init__(self, llm: LLMClient, sop: dict[str, Any]) -> None:
        self.llm = llm
        self.qualification = QualificationStage(sop)

    def generate(self, state: ConversationState) -> SessionSummary:
        transcript = "\n".join(state.transcript_lines())
        qual = self.qualification.summary_text(state)
        esc = json.dumps(
            [{"reason": e.reason, "detail": e.detail} for e in state.escalations],
            indent=2,
        )
        prompt = "You produce structured session summaries for SMB support handoffs."
        user = SUMMARY_PROMPT.format(
            transcript=transcript,
            qualification=qual,
            escalations=esc or "None",
        )
        data = self.llm.complete_json(prompt, user)
        raw_text = self._format_summary(data, state)
        return SessionSummary(
            customer_intent=data.get("customer_intent", "Unknown"),
            key_details=list(data.get("key_details", [])),
            qualification_summary=data.get("qualification_summary") or qual,
            sop_gaps=list(data.get("sop_gaps", [])) or list(state.sop_gaps),
            escalation_events=[f"{e.reason}: {e.detail}" for e in state.escalations],
            recommended_next_action=data.get(
                "recommended_next_action",
                "Review transcript and respond to customer",
            ),
            raw_text=raw_text,
        )

    def _format_summary(self, data: dict[str, Any], state: ConversationState) -> str:
        lines = [
            "=" * 50,
            "CONVERSATION SUMMARY",
            "=" * 50,
            f"Customer intent: {data.get('customer_intent', 'N/A')}",
            "",
            "Key details:",
        ]
        for item in data.get("key_details", []):
            lines.append(f"  • {item}")
        lines.extend(["", f"Qualification: {data.get('qualification_summary', 'N/A')}"])
        gaps = data.get("sop_gaps") or state.sop_gaps
        lines.append("\nSOP gaps identified:")
        if gaps:
            for g in gaps:
                lines.append(f"  • {g}")
        else:
            lines.append("  • None")
        lines.append("\nEscalations:")
        if state.escalations:
            for e in state.escalations:
                lines.append(f"  • [{e.reason}] {e.detail}")
        else:
            lines.append("  • None")
        lines.append(f"\nRecommended next action: {data.get('recommended_next_action', 'N/A')}")
        lines.append("=" * 50)
        return "\n".join(lines)
