import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from utils.user_agents import get_random_user_agent
from utils.logger import get_logger

logger = get_logger(__name__)

class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    source_name: str = "unknown"

    def get_headers(self) -> dict:
        return {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    @abstractmethod
    def scrape(self, profile: dict) -> list[dict]:
        """
        Scrape jobs for a given search profile.
        Returns a list of normalized job dicts.
        """
        pass

    def normalize(self, raw: dict) -> dict:
        """Normalize raw scraped data to standard schema."""
        return {
            "title": raw.get("title", "").strip(),
            "company": raw.get("company", "").strip(),
            "location": raw.get("location", "").strip(),
            "job_type": raw.get("job_type", "full-time"),
            "salary": raw.get("salary", ""),
            "url": raw.get("url", "").strip(),
            "description": raw.get("description", "")[:2000],  # cap at 2000 chars
            "source": self.source_name,
            "posted_at": raw.get("posted_at") or datetime.utcnow().isoformat(),
        }

    def _normalize_url_for_hash(self, url: str) -> str:
        """Strip query, fragment, and trailing slashes so the same job URL hashes consistently."""
        u = (url or "").strip()
        if not u:
            return ""
        parsed = urlparse(u)
        path = parsed.path.rstrip("/") or "/"
        netloc = parsed.netloc.lower()
        scheme = (parsed.scheme or "https").lower()
        normalized = urlunparse((scheme, netloc, path, "", "", ""))
        return normalized.lower()

    def make_hash(self, job: dict) -> str:
        """Create a unique hash for deduplication."""
        url_norm = self._normalize_url_for_hash(job.get("url", "") or "")
        key = f"{job.get('title', '').lower()}{job.get('company', '').lower()}{url_norm}"
        return hashlib.md5(key.encode()).hexdigest()
