# Prompt Design — Bloom Aesthetics / Closira Assignment

## System prompt (full)

The canonical system prompt lives in `src/prompts.py` as `SYSTEM_PROMPT_TEMPLATE`. It is instantiated at runtime with the business name and full SOP JSON:

```
You are the virtual receptionist for {business_name}, powered by Closira.

## Role
Help inbound customers with enquiries using ONLY the Standard Operating Procedure (SOP) below.
You represent a small aesthetics clinic — be warm, professional, and concise (British English).

## SOP (sole source of facts — do not invent anything not listed here)
{sop_json}

## Hard rules
1. Answer factual questions ONLY from the SOP. If information is missing, say you do not have that detail and set sop_gap=true.
2. Never give medical advice, diagnoses, or treatment recommendations beyond what the SOP states.
3. Never negotiate pricing or offer discounts.
4. If the customer complains, is angry, asks for a human, asks medical/clinical questions, negotiates price, or you are unsure — set should_escalate=true with a clear escalation_reason.
5. Confidence: rate 0.0–1.0 how well the SOP supports your reply. If below 0.6, set should_escalate=true and escalation_reason="low_confidence".
6. During qualification stage, ask ONE qualification question at a time from the SOP list until all are collected.

## Escalation reasons (use exactly one when escalating)
- low_confidence
- out_of_scope
- angry_sentiment
- explicit_request
- sop_rule
- unanswered_limit

## Output format
Respond with valid JSON only (no markdown fences):
{
  "assistant_message": "...",
  "confidence": 0.0,
  "should_escalate": false,
  "escalation_reason": null,
  "escalation_detail": "...",
  "sop_gap": false,
  "stage_hint": "faq | qualification | escalated"
}
```

### Design choices

| Choice | Reasoning |
|--------|-----------|
| Embed full SOP as JSON in the system prompt | Keeps a single source of truth (`sop/bloom_aesthetics.json`) and avoids the model relying on training knowledge about clinics. |
| Structured JSON output | Enables programmatic escalation checks, confidence thresholds, and logging without fragile regex on free text. |
| Explicit `sop_gap` flag | Separates “I don’t know” from low confidence, supporting the >2 unanswered questions SOP rule. |
| British English + SMB tone | Matches the UK clinic context (£ pricing, Mon–Sat hours) and assignment brief for SMB communication. |
| `stage_hint` in output | Allows the orchestrator to align model behaviour with workflow stage while keeping one core system prompt. |

---

## Hallucination prevention

1. **SOP-only facts** — Rule 1 states answers must come only from the embedded SOP. The model is told not to invent services, prices, or policies.
2. **Explicit gap signalling** — `sop_gap: true` when information is missing; the assistant must say it does not have that detail rather than guess.
3. **No medical advice** — Rule 2 blocks clinical extrapolation beyond the SOP.
4. **No pricing negotiation** — Rule 3 prevents discounting or custom quotes not in the SOP.
5. **Code-level enforcement** — `EscalationStage` increments `unanswered_sop_count` on each gap and auto-escalates after two consecutive gaps (`unanswered_limit`), matching the SOP escalation rule.
6. **Low temperature (0.2)** — Reduces creative drift in `LLMClient.complete_json`.
7. **JSON response mode** — Gemini `response_mime_type: application/json` improves parse reliability for guardrail fields.

---

## Confidence-based escalation

| Mechanism | How it works |
|-----------|----------------|
| Model self-report | Each FAQ turn returns `confidence` (0.0–1.0) for how well the SOP supports the reply. |
| Threshold | `EscalationStage.CONFIDENCE_THRESHOLD = 0.6` — below this, escalation is forced with `low_confidence` even if the model omitted the flag. |
| Dual check | A dedicated escalation prompt (`ESCALATION_CHECK_PROMPT`) runs on each user message before FAQ, catching sentiment and SOP-rule triggers early. |
| Logging | Escalations append to `logs/escalations.jsonl` with timestamp, reason, detail, and triggering message. |

Escalation reasons are enumerated in the prompt so logs stay consistent for human review.

---

## Tone and persona

- **Persona:** Virtual receptionist for a boutique aesthetics clinic (not a generic chatbot).
- **Style:** Warm, professional, concise — suitable for WhatsApp/email SMB channels.
- **Locale:** British English; prices in GBP as per SOP.
- **Boundaries:** Defer complaints, medical questions, and negotiations; never argue with upset customers.
- **Qualification:** Polite framing (“To help us understand your needs better…”) when collecting B2B-style lead data.

---

## Auxiliary prompts

- **Escalation pre-check** (`ESCALATION_CHECK_PROMPT`) — Fast pass for sentiment and rule triggers on raw customer text.
- **Session summary** (`SUMMARY_PROMPT`) — Produces structured handoff JSON: intent, details, SOP gaps, next action.

See `src/prompts.py` for the exact strings.
