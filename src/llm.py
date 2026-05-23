from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from google import genai
from google.genai import types

try:
    from google.genai.errors import ClientError as GenaiClientError
except ImportError:
    GenaiClientError = Exception  # type: ignore[misc, assignment]


class LLMError(Exception):
    """User-facing API error (quota, auth, network)."""

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        raise


def _friendly_api_error(exc: BaseException) -> LLMError:
    if isinstance(exc, LLMError):
        return exc
    msg = str(exc)
    retry_after: float | None = None
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
        m = re.search(r"retry in ([\d.]+)s", msg, re.I)
        if m:
            retry_after = float(m.group(1))
        return LLMError(
            "Gemini API quota exceeded for this model/plan. "
            "Wait a minute and retry, set GEMINI_MODEL=gemini-2.5-flash in .env, "
            "enable billing at https://aistudio.google.com/, or run with --mock.",
            retry_after=retry_after,
        )
    if "401" in msg or "403" in msg or "API_KEY" in msg.upper():
        return LLMError(
            "Invalid or unauthorized Gemini API key. Check GEMINI_API_KEY in .env "
            "(create one at https://aistudio.google.com/apikey)."
        )
    if "404" in msg and "model" in msg.lower():
        return LLMError(
            f"Model not found: check GEMINI_MODEL in .env. Error: {msg[:200]}"
        )
    return LLMError(f"Gemini API error: {msg[:300]}")


class LLMClient:
    def __init__(self, mock: bool = False) -> None:
        self.mock = mock
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client: genai.Client | None = None
        if not mock:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Copy .env.example to .env or use --mock for offline demos."
                )
            self._client = genai.Client(api_key=api_key)

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        if self.mock:
            return self._mock_response(user)

        assert self._client is not None
        last_error: BaseException | None = None
        for attempt in range(2):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=user,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        temperature=temperature,
                        response_mime_type="application/json",
                    ),
                )
                content = response.text or "{}"
                return _extract_json(content)
            except GenaiClientError as exc:
                last_error = exc
                err = _friendly_api_error(exc)
                if err.retry_after and attempt == 0:
                    time.sleep(min(err.retry_after, 60))
                    continue
                raise err from exc
            except Exception as exc:
                raise _friendly_api_error(exc) from exc
        raise _friendly_api_error(last_error or RuntimeError("Unknown API error"))

    def _mock_response(self, user: str) -> dict[str, Any]:
        lower = user.lower()
        if "escalation log:" in lower:
            if "botox" in lower and "price" in lower:
                return {
                    "customer_intent": "Pricing enquiry for Botox treatments",
                    "key_details": ["Botox from £200 per SOP", "May want consultation for exact quote"],
                    "qualification_summary": None,
                    "sop_gaps": [],
                    "recommended_next_action": "Offer free consultation booking via WhatsApp",
                }
            if "parking" in lower:
                return {
                    "customer_intent": "Facility question (parking) — out of SOP scope",
                    "key_details": ["Asked about on-site parking", "Escalated to human"],
                    "qualification_summary": None,
                    "sop_gaps": ["Parking availability"],
                    "recommended_next_action": "Human agent to confirm parking options and callback",
                }
            if any(w in lower for w in ("terrible", "refund", "complaint")):
                return {
                    "customer_intent": "Complaint and refund request",
                    "key_details": ["Negative prior experience", "Demanded immediate refund"],
                    "qualification_summary": None,
                    "sop_gaps": [],
                    "recommended_next_action": "Manager callback within 2 hours; do not promise refund via bot",
                }
            if "we run a small salon" in lower or "/qualify" in lower:
                return {
                    "customer_intent": "B2B lead qualification for Closira-style platform",
                    "key_details": [
                        "Small salon, ~4 staff",
                        "Four people handle enquiries",
                        "Uses WhatsApp Business and Gmail",
                    ],
                    "qualification_summary": "Salon; 4 enquiry handlers; WhatsApp Business + Gmail",
                    "sop_gaps": [],
                    "recommended_next_action": "Schedule product demo with decision-maker",
                }
            if "opening hours" in lower or "book a consultation" in lower:
                return {
                    "customer_intent": "Enquiry about clinic hours and booking a free consultation",
                    "key_details": [
                        "Hours: Mon–Sat 9am–7pm",
                        "Booking via WhatsApp or website",
                        "Consultations are free",
                    ],
                    "qualification_summary": None,
                    "sop_gaps": [],
                    "recommended_next_action": "Send WhatsApp booking link and confirm preferred date",
                }
            return {
                "customer_intent": "Pricing enquiry for Botox",
                "key_details": ["Asked about Botox from £200"],
                "qualification_summary": None,
                "sop_gaps": [],
                "recommended_next_action": "Follow up via WhatsApp to confirm appointment",
            }
        if "recent transcript" in lower:
            if any(w in lower for w in ("terrible", "awful", "complaint", "refund", "angry")):
                return {
                    "should_escalate": True,
                    "escalation_reason": "angry_sentiment",
                    "escalation_detail": "Customer complaint and refund demand",
                    "detected_sentiment": "angry",
                    "triggers": ["complaint", "refund"],
                }
            if "parking" in lower:
                return {
                    "should_escalate": True,
                    "escalation_reason": "out_of_scope",
                    "escalation_detail": "Parking not in SOP",
                    "detected_sentiment": "neutral",
                    "triggers": ["out_of_scope"],
                }
            return {
                "should_escalate": False,
                "escalation_reason": None,
                "escalation_detail": None,
                "detected_sentiment": "neutral",
                "triggers": [],
            }
        if "opening hours" in lower or ("hours" in lower and "open" in lower):
            return {
                "assistant_message": "We are open Monday to Saturday, 9am to 7pm. We are closed on Sundays.",
                "confidence": 0.95,
                "should_escalate": False,
                "escalation_reason": None,
                "escalation_detail": None,
                "sop_gap": False,
                "stage_hint": "faq",
            }
        if "book" in lower and "consultation" in lower:
            return {
                "assistant_message": "You can book via WhatsApp or our website. Consultations are free. Please give 24 hours notice if you need to cancel or reschedule.",
                "confidence": 0.95,
                "should_escalate": False,
                "escalation_reason": None,
                "escalation_detail": None,
                "sop_gap": False,
                "stage_hint": "faq",
            }
        if "botox" in lower and "price" in lower:
            return {
                "assistant_message": "Botox treatments start from £200. The exact price depends on the treatment area and is confirmed at consultation.",
                "confidence": 0.95,
                "should_escalate": False,
                "escalation_reason": None,
                "escalation_detail": None,
                "sop_gap": False,
                "stage_hint": "faq",
            }
        if "parking" in lower or "insurance" in lower:
            return {
                "assistant_message": "I do not have parking or insurance information in our records. I will connect you with a team member who can help.",
                "confidence": 0.2,
                "should_escalate": True,
                "escalation_reason": "out_of_scope",
                "escalation_detail": "Question not covered by SOP",
                "sop_gap": True,
                "stage_hint": "escalated",
            }
        if any(w in lower for w in ("terrible", "awful", "complaint", "refund", "angry")):
            return {
                "assistant_message": "I am sorry you have had this experience. I am connecting you with a member of our team who can assist you properly.",
                "confidence": 0.9,
                "should_escalate": True,
                "escalation_reason": "angry_sentiment",
                "escalation_detail": "Customer complaint detected",
                "sop_gap": False,
                "stage_hint": "escalated",
            }
        if "qualification" in lower or "business type" in lower:
            return {
                "assistant_message": "Thank you. What type of business are you enquiring on behalf of (e.g. sole trader, salon, clinic)?",
                "confidence": 0.9,
                "should_escalate": False,
                "escalation_reason": None,
                "escalation_detail": None,
                "sop_gap": False,
                "stage_hint": "qualification",
            }
        return {
            "assistant_message": "Thank you for your message. How can I help you today regarding our services or booking?",
            "confidence": 0.7,
            "should_escalate": False,
            "escalation_reason": None,
            "escalation_detail": None,
            "sop_gap": False,
            "stage_hint": "faq",
        }
