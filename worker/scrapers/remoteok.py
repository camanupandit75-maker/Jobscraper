import re
import httpx
from datetime import datetime
from .base import BaseScraper
from utils.logger import get_logger

logger = get_logger(__name__)

# Always consider these terms (in addition to words derived from profile keywords)
FALLBACK_KEYWORD_WORDS = frozenset({"finance", "financial", "accounting"})


def _tokenize_keywords(profile_keywords: list) -> set[str]:
    """Lowercase words (alphanumeric runs) from profile keyword strings."""
    words: set[str] = set()
    for kw in profile_keywords:
        if not kw or not str(kw).strip():
            continue
        for part in re.findall(r"[a-z0-9]+", str(kw).lower()):
            if len(part) >= 2:
                words.add(part)
    words.update(FALLBACK_KEYWORD_WORDS)
    return words


def _tags_blob(item: dict) -> str:
    raw = item.get("tags")
    if raw is None:
        return ""
    if isinstance(raw, list):
        return " ".join(str(t).lower() for t in raw)
    return str(raw).lower()


def _job_matches(words: set[str], title: str, tags_blob: str) -> bool:
    if not words:
        return False
    title_l = (title or "").lower()
    haystack = f"{title_l} {tags_blob}"
    return any(w in haystack for w in words)


class RemoteOKScraper(BaseScraper):
    source_name = "remoteok"
    API_URL = "https://remoteok.com/api"

    def scrape(self, profile: dict) -> list[dict]:
        words = _tokenize_keywords(profile.get("keywords", []))
        jobs = []
        try:
            headers = self.get_headers()
            headers["Accept"] = "application/json"
            headers["Accept-Encoding"] = "identity"
            resp = httpx.get(self.API_URL, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            # First item is metadata, skip it
            listings = [item for item in data if isinstance(item, dict) and "position" in item]
            for item in listings:
                position = item.get("position", "") or ""
                tags_blob = _tags_blob(item)
                if not _job_matches(words, position, tags_blob):
                    continue
                job = self.normalize({
                    "title": position,
                    "company": item.get("company", ""),
                    "location": item.get("location", "Remote"),
                    "job_type": "remote",
                    "salary": item.get("salary", ""),
                    "url": f"https://remoteok.com/remote-jobs/{item.get('id','')}",
                    "description": item.get("description", ""),
                    "posted_at": datetime.utcfromtimestamp(
                        int(item.get("epoch", 0))
                    ).isoformat() if item.get("epoch") else None,
                })
                job["hash"] = self.make_hash(job)
                jobs.append(job)
                if len(jobs) >= 50:
                    break
        except Exception as e:
            logger.error(f"RemoteOK scrape error: {e}")
        logger.info(f"RemoteOK: found {len(jobs)} matching jobs")
        return jobs
