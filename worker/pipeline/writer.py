from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx
from config import SUPABASE_URL, SUPABASE_KEY
from utils.logger import get_logger

logger = get_logger(__name__)


def _deleted_count_from_response(resp: httpx.Response) -> int:
    if not resp.content:
        return 0
    try:
        data = resp.json()
        return len(data) if isinstance(data, list) else 0
    except Exception:
        return 0


HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=ignore-duplicates",
}

def get_existing_hashes() -> set:
    """Fetch all existing job hashes from Supabase."""
    try:
        resp = httpx.get(
            f"{SUPABASE_URL}/rest/v1/jobs?select=hash",
            headers=HEADERS,
            timeout=30
        )
        resp.raise_for_status()
        return {row["hash"] for row in resp.json()}
    except Exception as e:
        logger.error(f"Failed to fetch existing hashes: {e}")
        return set()

def upsert_jobs(jobs: list[dict]) -> int:
    """Upsert jobs to Supabase. Returns number of jobs inserted."""
    if not jobs:
        return 0
    try:
        resp = httpx.post(
            f"{SUPABASE_URL}/rest/v1/jobs?on_conflict=hash",
            headers={**HEADERS, "Prefer": "resolution=ignore-duplicates,return=minimal"},
            json=jobs,
            timeout=60
        )
        resp.raise_for_status()
        logger.info(f"Upserted {len(jobs)} jobs to Supabase")
        return len(jobs)
    except Exception as e:
        logger.error(f"Supabase upsert error: {e}")
        return 0

def log_scrape_run(source: str, jobs_added: int, jobs_found: int,
                   started_at: str, ended_at: str, error: str = None):
    try:
        httpx.post(
            f"{SUPABASE_URL}/rest/v1/scrape_runs",
            headers=HEADERS,
            json={
                "source": source,
                "jobs_added": jobs_added,
                "jobs_found": jobs_found,
                "started_at": started_at,
                "ended_at": ended_at,
                "status": "error" if error else "success",
                "error_msg": error,
            },
            timeout=10
        )
    except Exception as e:
        logger.error(f"Failed to log scrape run: {e}")


def cleanup_old_jobs() -> int:
    """
    Remove stale jobs. Never deletes bookmarked or applied rows.

    - Hidden rows older than 7 days (not bookmarked, not applied).
    - Non-bookmarked, non-applied rows older than 30 days (any visibility).
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return 0

    base = f"{SUPABASE_URL.rstrip('/')}/rest/v1/jobs"
    now = datetime.now(timezone.utc)
    ts_7d = quote((now - timedelta(days=7)).isoformat(), safe="")
    ts_30d = quote((now - timedelta(days=30)).isoformat(), safe="")

    del_headers = {**HEADERS, "Prefer": "return=representation"}
    total = 0

    try:
        q1 = (
            f"?is_hidden=eq.true&scraped_at=lt.{ts_7d}"
            "&is_bookmarked=eq.false&status=neq.applied"
        )
        r1 = httpx.delete(base + q1, headers=del_headers, timeout=120)
        r1.raise_for_status()
        n1 = _deleted_count_from_response(r1)
        total += n1
        logger.info(f"cleanup_old_jobs: deleted {n1} hidden job(s) older than 7 days")
    except Exception as e:
        logger.error(f"cleanup_old_jobs (hidden): {e}")

    try:
        q2 = (
            f"?is_bookmarked=eq.false&status=neq.applied&scraped_at=lt.{ts_30d}"
        )
        r2 = httpx.delete(base + q2, headers=del_headers, timeout=120)
        r2.raise_for_status()
        n2 = _deleted_count_from_response(r2)
        total += n2
        logger.info(
            f"cleanup_old_jobs: deleted {n2} non-bookmarked non-applied job(s) older than 30 days"
        )
    except Exception as e:
        logger.error(f"cleanup_old_jobs (stale): {e}")

    logger.info(f"cleanup_old_jobs: total deleted {total}")
    return total
