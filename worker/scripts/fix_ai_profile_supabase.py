#!/usr/bin/env python3
"""
Delete search_profiles row named 'ai' (case-insensitive) and insert the corrected profile.
Loads NEXT_PUBLIC_SUPABASE_URL + SUPABASE_SERVICE_KEY from frontend/.env.local (or worker/.env).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[2]
FRONTEND_ENV = REPO / "frontend" / ".env.local"
WORKER_ENV = REPO / "worker" / ".env"

INSERT_BODY = {
    "name": "ai",
    "keywords": [
        "AI engineer",
        "machine learning",
        "ML engineer",
        "artificial intelligence",
        "LLM",
    ],
    "location": "india, uae, remote",
    "sites": ["indeed", "linkedin", "remoteok"],
    "is_active": True,
}


def _parse_dotenv(path: Path) -> dict:
    out = {}
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        out[k] = v
    return out


def main() -> int:
    env = {**_parse_dotenv(WORKER_ENV), **_parse_dotenv(FRONTEND_ENV)}
    url = (env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL") or "").rstrip("/")
    key = env.get("SUPABASE_SERVICE_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not url or not key:
        print(
            "Missing NEXT_PUBLIC_SUPABASE_URL/SUPABASE_URL or SUPABASE_SERVICE_KEY. "
            "Set them in frontend/.env.local or run supabase/fix_ai_profile.sql manually.",
            file=sys.stderr,
        )
        return 1

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30) as client:
        r = client.get(f"{url}/rest/v1/search_profiles?select=id,name", headers=headers)
        r.raise_for_status()
        rows = r.json()
        deleted = 0
        for row in rows:
            name = (row.get("name") or "").strip().lower()
            if name != "ai":
                continue
            rid = row.get("id")
            if not rid:
                continue
            d = client.delete(
                f"{url}/rest/v1/search_profiles?id=eq.{rid}",
                headers=headers,
            )
            d.raise_for_status()
            deleted += 1

        ins = client.post(
            f"{url}/rest/v1/search_profiles",
            headers={**headers, "Prefer": "return=representation"},
            content=json.dumps(INSERT_BODY),
        )
        ins.raise_for_status()
        data = ins.json()
        row = data[0] if isinstance(data, list) and data else data

    print(f"Removed {deleted} existing 'ai' row(s). Inserted profile id={row.get('id', '?')}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
