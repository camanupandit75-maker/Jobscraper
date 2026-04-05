"""
Load search profiles from Supabase for the worker (replaces config when non-empty).
"""
import httpx
from config import SUPABASE_URL, SUPABASE_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

REST_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def _db_row_to_worker_profile(row: dict) -> dict:
    loc = (row.get("location") or "").strip()
    sites = [str(s) for s in (row.get("sites") or []) if s]
    keywords = [str(k) for k in (row.get("keywords") or []) if k]
    profile = {
        "name": (row.get("name") or "").strip() or "unnamed",
        "keywords": keywords,
        "location": loc,
        "sites": sites,
        "remote": loc.lower() == "remote",
        "job_type": "full-time",
    }
    ll = loc.lower()
    if "india" in ll or ll == "india":
        profile["indeed_base_url"] = "https://in.indeed.com"
    elif any(
        x in ll
        for x in (
            "uae",
            "emirates",
            "dubai",
            "abu dhabi",
            "middle east",
            "gulf",
            "ksa",
            "saudi",
            "qatar",
            "kuwait",
            "bahrain",
            "oman",
        )
    ):
        profile["indeed_base_url"] = "https://gulf.indeed.com"
    return profile


def fetch_active_search_profiles() -> list:
    """
    Active rows from search_profiles, converted to worker profile dicts.
    Returns [] if env missing, request fails, or no rows.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    url = (
        f"{SUPABASE_URL.rstrip('/')}/rest/v1/search_profiles"
        "?is_active=eq.true&select=*&order=created_at.asc"
    )
    try:
        resp = httpx.get(url, headers=REST_HEADERS, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
    except Exception as e:
        logger.error(f"Failed to load search_profiles from Supabase: {e}")
        return []
    if not rows:
        return []
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            out.append(_db_row_to_worker_profile(row))
        except Exception as e:
            logger.warning(f"Skipping bad search_profile row: {e}")
    return out
