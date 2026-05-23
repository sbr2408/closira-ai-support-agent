from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_sop(path: Path | None = None) -> dict[str, Any]:
    sop_path = path or Path(__file__).resolve().parent.parent / "sop" / "bloom_aesthetics.json"
    with sop_path.open(encoding="utf-8") as f:
        return json.load(f)


def sop_to_prompt_block(sop: dict[str, Any]) -> str:
    """Serialize SOP for inclusion in prompts — sole source of truth for facts."""
    return json.dumps(sop, indent=2)
