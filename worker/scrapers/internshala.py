"""
Internshala scraper: JSON search API first, Playwright fallback.
"""
import re
import time
from typing import Any, Dict, List, Optional

import httpx

from .base import BaseScraper
from config import REQUEST_DELAY_SECONDS
from utils.logger import get_logger
from utils.profile_locations import normalize_profile_locations

logger = get_logger(__name__)

API_TEMPLATE = "https://internshala.com/jobs/ajax/search/keywords-{keyword}"
JOB_DETAIL_TEMPLATE = "https://internshala.com/job/detail/{readable_id}"
PLAYWRIGHT_JOBS_TEMPLATE = "https://internshala.com/jobs/{keyword}-jobs"
MAX_KEYWORDS_PER_RUN = 3
MAX_JOBS_PER_KEYWORD = 50


def _slug_keyword(keyword: str) -> str:
    s = (keyword or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "internship"


def _meta_records(node: Any) -> List[Dict[str, Any]]:
    if node is None:
        return []
    if isinstance(node, list):
        return [x for x in node if isinstance(x, dict)]
    if isinstance(node, dict):
        return [v for v in node.values() if isinstance(v, dict)]
    return []


def _listings_from_json(data: Any) -> List[Dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    out: List[Dict[str, Any]] = []
    for key in ("internships_meta", "jobs_meta"):
        if key not in data:
            continue
        out.extend(_meta_records(data.get(key)))
    return out


def _pick_str(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, list):
        return ", ".join(str(x).strip() for x in val if x).strip()
    return str(val).strip()


def _readable_id_from_record(rec: Dict[str, Any]) -> Optional[str]:
    rid = rec.get("url_readable_id")
    if rid is not None and str(rid).strip():
        return str(rid).strip()
    alt = rec.get("readable_id") or rec.get("url_meta")
    if alt is not None and str(alt).strip():
        return str(alt).strip()
    return None


def _job_from_api_record(rec: Dict[str, Any]) -> Optional[dict]:
    title = _pick_str(
        rec.get("title")
        or rec.get("internship_title")
        or rec.get("name")
        or rec.get("profile_name")
    )
    company = _pick_str(
        rec.get("company_name")
        or rec.get("company")
        or rec.get("employer_name")
    )
    location = _pick_str(
        rec.get("location")
        or rec.get("location_names")
        or rec.get("city")
        or rec.get("cities")
    )
    rid = _readable_id_from_record(rec)
    if not title or not rid:
        return None
    url = JOB_DETAIL_TEMPLATE.format(readable_id=rid)
    return {
        "title": title,
        "company": company,
        "location": location,
        "url": url,
        "description": "",
    }


class IntershalaScraper(BaseScraper):
    source_name = "internshala"

    def _api_headers(self) -> Dict[str, str]:
        h = dict(self.get_headers())
        h["X-Requested-With"] = "XMLHttpRequest"
        h["Referer"] = "https://internshala.com"
        h["Accept"] = "application/json, text/javascript, */*; q=0.01"
        return h

    def _fetch_jobs_via_api(self, keyword_slug: str) -> List[dict]:
        url = API_TEMPLATE.format(keyword=keyword_slug)
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                resp = client.get(url, headers=self._api_headers())
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning(f"Internshala API failed for '{keyword_slug}': {e}")
            return []

        listings = _listings_from_json(data)
        if not listings:
            logger.info(f"Internshala API: no internships_meta/jobs_meta for '{keyword_slug}'")
            return []

        jobs: List[dict] = []
        for rec in listings[:MAX_JOBS_PER_KEYWORD]:
            raw = _job_from_api_record(rec)
            if not raw:
                continue
            job = self.normalize(raw)
            job["hash"] = self.make_hash(job)
            jobs.append(job)
        logger.info(f"Internshala API: {len(jobs)} jobs for '{keyword_slug}'")
        return jobs

    def _abs_href(self, href: Optional[str]) -> str:
        if not href:
            return ""
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return f"https://internshala.com{href}"
        return f"https://internshala.com/{href.lstrip('/')}"

    def _extract_playwright_card(self, card) -> Optional[dict]:
        try:
            title_el = card.query_selector("h3 a")
            if not title_el:
                title_el = card.query_selector("h3.job-internship-name a")
            if not title_el:
                return None
            title = title_el.inner_text().strip()
            href = title_el.get_attribute("href")
            url_val = self._abs_href(href)
            if not title:
                return None
            if not url_val:
                return None

            company_el = card.query_selector("p.company-name")
            company = company_el.inner_text().strip() if company_el else ""

            loc_el = card.query_selector("div.location_link")
            location = loc_el.inner_text().strip() if loc_el else ""

            job = self.normalize({
                "title": title,
                "company": company,
                "location": location,
                "url": url_val,
            })
            job["hash"] = self.make_hash(job)
            return job
        except Exception:
            return None

    def _fetch_jobs_via_playwright(self, keyword_slug: str) -> List[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not installed. Internshala fallback skipped.")
            return []

        page_url = PLAYWRIGHT_JOBS_TEMPLATE.format(keyword=keyword_slug)
        jobs: List[dict] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                try:
                    context = browser.new_context(user_agent=self.get_headers()["User-Agent"])
                    page = context.new_page()
                    page.goto(page_url, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(3)
                    cards = page.query_selector_all("div.individual_internship")
                    for card in cards[:30]:
                        job = self._extract_playwright_card(card)
                        if job:
                            jobs.append(job)
                finally:
                    browser.close()
        except Exception as e:
            logger.error(f"Internshala Playwright fallback failed for '{keyword_slug}': {e}")

        logger.info(f"Internshala Playwright: {len(jobs)} jobs for '{keyword_slug}'")
        return jobs

    def scrape(self, profile: dict) -> List[dict]:
        _ = normalize_profile_locations(profile)
        all_jobs: List[dict] = []
        keywords = profile.get("keywords") or []
        if not keywords:
            keywords = ["finance"]

        for raw_kw in keywords[:MAX_KEYWORDS_PER_RUN]:
            slug = _slug_keyword(str(raw_kw))
            if not slug:
                continue

            batch = self._fetch_jobs_via_api(slug)
            if not batch:
                batch = self._fetch_jobs_via_playwright(slug)

            all_jobs.extend(batch)
            time.sleep(REQUEST_DELAY_SECONDS)

        logger.info(f"Internshala: found {len(all_jobs)} jobs total")
        return all_jobs
