# AI Customer Support Workflow — Closira Assignment

Python workflow demonstrating a four-stage AI support agent for **Bloom Aesthetics Clinic**, grounded in a JSON SOP with explicit escalation and session summaries.

## Features (assignment stages)

| # | Stage | Module |
|---|--------|--------|
| 1 | FAQ answering (SOP-only) | `src/stages/faq.py` |
| 2 | Lead qualification (2–3 questions) | `src/stages/qualification.py` |
| 3 | Escalation detection & logging | `src/stages/escalation.py` |
| 4 | Conversation summary | `src/stages/summary.py` |

Orchestration: `src/workflow.py` · CLI: `src/main.py`

## Setup

```bash
cd aiagentdev
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your Gemini API key to .env (https://aistudio.google.com/apikey)
```

## Run

**Interactive CLI (live Gemini API):**

```bash
python -m src.main
```

**Interactive CLI (offline mock — no API key):**

```bash
python -m src.main --mock
```

**Replay a scripted scenario:**

```bash
python scripts/run_scenario.py in_sop --mock
python scripts/run_scenario.py out_of_scope --live   # requires GEMINI_API_KEY in .env
```

### CLI commands

| Command | Action |
|---------|--------|
| `/end` | End session and print structured summary |
| `/qualify` | Start lead qualification questions |
| `/quit` | Exit and generate summary |

Escalation events are appended to `logs/escalations.jsonl`.

## SOP data

The agent operates only on `sop/bloom_aesthetics.json` (Bloom Aesthetics Clinic — hours, services, booking, escalation rules). See `prompt_design.md` for how this is injected into prompts.

## Project layout

```
aiagentdev/
├── sop/bloom_aesthetics.json
├── src/
│   ├── main.py              # CLI entry
│   ├── workflow.py          # Orchestrator
│   ├── prompts.py           # System & auxiliary prompts
│   ├── llm.py               # Gemini client + mock mode
│   └── stages/              # FAQ, qualification, escalation, summary
├── scripts/run_scenario.py  # Scripted replays
├── test_transcripts/        # Sample conversations per behaviour
├── prompt_design.md
├── logs/                    # Runtime escalation/summary logs (gitignored)
└── requirements.txt
```

## Deliverables checklist

- [x] Python workflow with four stages
- [x] `prompt_design.md`
- [x] `test_transcripts/` (5 scenarios)
- [x] `README.md`
- [ ] 2–5 min video walkthrough (record locally and upload to GitHub/Loom)

## Trade-offs & limitations

- **No UI** — CLI only, per assignment brief.
- **Single SOP file** — Multi-tenant routing is out of scope.
- **Qualification** is rule-triggered (`/qualify` or B2B keywords); a production system might use intent classification.
- **Dual LLM calls per turn** (escalation pre-check + FAQ) improve safety at higher latency/cost.
- **Mock mode** uses keyword heuristics for demos without an API key; use the live Gemini API for evaluation.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Required unless `--mock`. Get one at [Google AI Studio](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `LLM_ESCALATION_CHECK` | `false` | Set `true` for an extra LLM escalation pass (uses more quota) |

### Quota / 429 errors

If you see `RESOURCE_EXHAUSTED` or `limit: 0` for a model:

1. Change model in `.env`: `GEMINI_MODEL=gemini-2.5-flash` (or `gemini-2.5-flash-lite`)
2. Wait ~1 minute and retry, or check usage at [ai.dev/rate-limit](https://ai.dev/rate-limit)
3. Use offline mode: `python -m src.main --mock`
4. Enable billing on your Google AI project if the free tier is exhausted

Escalation uses **rule-based checks first** (no API call). Only FAQ/summary call Gemini by default.

## License

Submission prototype for Closira AI Engineering Intern assignment.
