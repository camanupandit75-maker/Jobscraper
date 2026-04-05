"""
Load search profiles from Supabase for the worker (replaces config when non-empty).
"""
import httpx
from config import SUPABASE_URL, SUPABASE_KEY
from utils.logger import get_logger
from utils.profile_locations import infer_indeed_base_from_locations

logger = get_logger(__name__)

REST_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def _db_row_to_worker_profile(row: dict) -> dict:
    loc_raw = (row.get("location") or "").strip()
    locations = [p.strip() for p in loc_raw.split(",") if p.strip()] if loc_raw else []
    if not locations:
        locations = [""]

    sites = [str(s) for s in (row.get("sites") or []) if s]
    keywords = [str(k) for k in (row.get("keywords") or []) if k]
    profile = {
        "name": (row.get("name") or "").strip() or "unnamed",
        "keywords": keywords,
        "locations": locations,
        "location": locations[0] if locations and locations[0] else "",
        "sites": sites,
        "remote": any((x or "").lower() == "remote" for x in locations),
        "job_type": "full-time",
    }
    # Single region → stable default host; multiple → omit so Indeed infers per location
    if len(locations) == 1:
        profile["indeed_base_url"] = infer_indeed_base_from_locations(locations)
    elif len(locations) > 1:
        pass  # Indeed scraper uses infer_indeed_base_for_location per query
    else:
        profile["indeed_base_url"] = "https://www.indeed.com"
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
