"""Preference record storage and export for Human-in-the-Loop RL."""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any

PROMPTS_DATASET_PATH = Path(__file__).resolve().parent / "prompts_dataset.json"


def load_prompts_dataset() -> dict[str, Any]:
    """Load the prompt dataset JSON. Returns dict with 'category', 'description', 'prompts'."""
    with open(PROMPTS_DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_random_prompt_from_dataset() -> str:
    """Return a random prompt from the curated dataset (ambiguous ethical / tradeoffs)."""
    data = load_prompts_dataset()
    prompts = data.get("prompts", [])
    if not prompts:
        return ""
    return random.choice(prompts).strip()


def create_record(
    prompt: str,
    response_a: str,
    response_b: str,
    preference: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build a single preference record."""
    return {
        "prompt": prompt,
        "response_a": response_a,
        "response_b": response_b,
        "preference": preference,
        "metadata": metadata,
    }


def append_record(
    records: list[dict],
    prompt: str,
    response_a: str,
    response_b: str,
    preference: str,
    metadata: dict[str, Any],
    jsonl_path: str | Path | None = None,
) -> None:
    """Append a record to the list and optionally to a JSONL file."""
    record = create_record(
        prompt, response_a, response_b, preference, metadata
    )
    records.append(record)
    if jsonl_path is not None:
        path = Path(jsonl_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def export_training_jsonl(records: list[dict]) -> str:
    """
    Produce JSONL string for downstream training: only non-tie rows
    as {prompt, chosen, rejected}.
    """
    lines = []
    for r in records:
        pref = r.get("preference")
        if pref not in ("a", "b"):
            continue
        chosen = r["response_a"] if pref == "a" else r["response_b"]
        rejected = r["response_b"] if pref == "a" else r["response_a"]
        lines.append(
            json.dumps(
                {"prompt": r["prompt"], "chosen": chosen, "rejected": rejected},
                ensure_ascii=False,
            )
        )
    return "\n".join(lines) + ("\n" if lines else "")


def export_full_jsonl(records: list[dict]) -> str:
    """Produce JSONL string with all fields and metadata (including ties)."""
    return "\n".join(
        json.dumps(r, ensure_ascii=False) for r in records
    ) + ("\n" if records else "")
