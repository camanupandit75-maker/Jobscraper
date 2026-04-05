"""
Stable job hash for deduplication: lowercase title/company with punctuation removed + normalized URL.
"""
import hashlib
from urllib.parse import urlparse, urlunparse


def normalize_text_for_hash(s: str) -> str:
    """Lowercase; keep only alphanumeric (Unicode) so punctuation variants collapse."""
    return "".join(c for c in (s or "").lower() if c.isalnum())


def normalize_url_for_hash(url: str) -> str:
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


def compute_job_hash(job: dict) -> str:
    """MD5 of normalized title + company + URL (same logic as scraper dedupe)."""
    t = normalize_text_for_hash(job.get("title", "") or "")
    c = normalize_text_for_hash(job.get("company", "") or "")
    url_norm = normalize_url_for_hash(job.get("url", "") or "")
    key = f"{t}{c}{url_norm}"
    return hashlib.md5(key.encode()).hexdigest()
