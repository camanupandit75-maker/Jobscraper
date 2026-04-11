import time
from typing import List, Optional

import httpx

from .base import BaseScraper
from config import APIFY_TOKEN, REQUEST_DELAY_SECONDS
from utils.logger import get_logger
from utils.profile_locations import normalize_profile_locations

logger = get_logger(__name__)

ACTOR_URL = "https://api.apify.com/v2/acts/unfenced-group~naukri-scraper/runs"
ACTOR_BASE = "https://api.apify.com/v2/acts/unfenced-group~naukri-scraper"


class NaukriApifyScraper(BaseScraper):
    source_name = "naukri"

    def _run_apify_and_fetch_items(
        self, keyword: str, location: str
    ) -> Optional[List[dict]]:
        """
        Start async run, poll until SUCCEEDED or timeout, fetch dataset items.
        Returns None if run FAILED/ABORTED/TIMED-OUT (caller should return [] from scrape).
        Returns [] on poll timeout without success.
        """
        run_resp = httpx.post(
            ACTOR_URL,
            params={"token": APIFY_TOKEN},
            json={
                "keyword": keyword,
                "location": location,
                "maxResults": 50,
            },
            timeout=30,
        )
        run_resp.raise_for_status()
        run_body = run_resp.json()
        run_id = (run_body.get("data") or {}).get("id")
        if not run_id:
            logger.error("Apify run response missing data.id")
            return []

        status: Optional[str] = None
        for _ in range(30):
            time.sleep(10)
            status_resp = httpx.get(
                f"{ACTOR_BASE}/runs/{run_id}",
                params={"token": APIFY_TOKEN},
                timeout=30,
            )
            status_resp.raise_for_status()
            data = status_resp.json().get("data") or {}
            status = data.get("status")
            if status == "SUCCEEDED":
                break
            if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                logger.error(f"Apify run failed with status: {status}")
                return None

        if status != "SUCCEEDED":
            logger.error(
                f"Apify run {run_id} did not finish in time (last status: {status})"
            )
            return []

        items_resp = httpx.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
            params={"token": APIFY_TOKEN},
            timeout=300,
        )
        items_resp.raise_for_status()
        items = items_resp.json()
        if not isinstance(items, list):
            logger.warning(
                f"Unexpected Apify dataset response for '{keyword}' in '{location}'"
            )
            return []
        if items:
            logger.info(f"Sample keys: {list(items[0].keys())}")
            logger.info(f"Sample item: {items[0]}")
        return items

    def scrape(self, profile: dict) -> list:
        if not APIFY_TOKEN:
            logger.warning("APIFY_TOKEN not set. Skipping Naukri scraper.")
            return []

        keywords = profile.get("keywords", [])
        locations = normalize_profile_locations(profile)
        if not locations or locations == [""]:
            locations = [profile.get("location", "India") or "India"]
        all_jobs = []

        for keyword in keywords[:3]:
            for location in locations[:3]:
                try:
                    items = self._run_apify_and_fetch_items(keyword, location)
                    if items is None:
                        return []
                    if not items:
                        continue
                    for item in items:
                        job = self.normalize(
                            {
                                "title": item.get("jobTitle", ""),
                                "company": item.get("companyName", ""),
                                "location": item.get("location", location),
                                "salary": item.get("salary", ""),
                                "url": item.get("jdURL", ""),
                                "description": item.get("jobDescription", ""),
                                "posted_at": item.get("postingDate", ""),
                            }
                        )
                        job["hash"] = self.make_hash(job)
                        all_jobs.append(job)
                    time.sleep(REQUEST_DELAY_SECONDS)
                except Exception as e:
                    logger.error(f"Apify/Naukri error for '{keyword}' in '{location}': {e}")

        logger.info(f"Naukri (Apify): found {len(all_jobs)} jobs")
        return all_jobs
