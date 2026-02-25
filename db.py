"""Supabase persistence for preference records."""

import os
from typing import Any

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

TABLE_NAME = "preferences"


def _get_client():
    """Return Supabase client if configured."""
    url = SUPABASE_URL
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    if not url or not key:
        return None
    from supabase import create_client
    return create_client(url, key)


def is_configured() -> bool:
    """Return True if Supabase URL and key are set."""
    return bool(SUPABASE_URL and (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY))


def _json_safe(obj: Any) -> Any:
    """Return a JSON-serializable version for Supabase JSONB."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return str(obj)


def insert_preference(
    prompt: str,
    response_a: str,
    response_b: str,
    preference: str,
    metadata: dict[str, Any],
) -> None:
    """Insert a single preference record into Supabase."""
    client = _get_client()
    if not client:
        raise RuntimeError("Supabase not configured: set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY)")
    row = {
        "prompt": prompt,
        "response_a": response_a,
        "response_b": response_b,
        "preference": preference,
        "metadata": _json_safe(metadata),
    }
    client.table(TABLE_NAME).insert(row).execute()


def fetch_all_preferences() -> list[dict[str, Any]]:
    """
    Fetch all preference records from Supabase, ordered by created_at.
    Returns list of dicts with keys: prompt, response_a, response_b, preference, metadata.
    (created_at is folded into metadata for compatibility with export functions.)
    """
    client = _get_client()
    if not client:
        return []
    resp = client.table(TABLE_NAME).select("prompt, response_a, response_b, preference, metadata, created_at").order("created_at").execute()
    records = []
    for row in (resp.data or []):
        meta = dict(row.get("metadata") or {})
        if row.get("created_at"):
            meta["created_at"] = row["created_at"]
        records.append({
            "prompt": row.get("prompt", ""),
            "response_a": row.get("response_a", ""),
            "response_b": row.get("response_b", ""),
            "preference": row.get("preference", ""),
            "metadata": meta,
        })
    return records
