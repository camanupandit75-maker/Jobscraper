import time

import httpx

from .base import BaseScraper
from config import APIFY_TOKEN, REQUEST_DELAY_SECONDS
from utils.logger import get_logger
from utils.profile_locations import normalize_profile_locations

logger = get_logger(__name__)


class NaukriApifyScraper(BaseScraper):
    source_name = "naukri"
    ACTOR_URL = (
        "https://api.apify.com/v2/acts/curious_coder~naukri-scraper/run-sync-get-dataset-items"
    )

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
                    resp = httpx.post(
                        self.ACTOR_URL,
                        params={"token": APIFY_TOKEN},
                        json={
                            "keyword": keyword,
                            "location": location,
                            "maxItems": 50,
                        },
                        timeout=120,
                    )
                    resp.raise_for_status()
                    items = resp.json()
                    if not isinstance(items, list):
                        logger.warning(
                            f"Unexpected Apify response for '{keyword}' in '{location}'"
                        )
                        continue
                    for item in items:
                        job = self.normalize(
                            {
                                "title": item.get("title", ""),
                                "company": item.get("companyName", ""),
                                "location": item.get("location", location),
                                "salary": item.get("salary", ""),
                                "url": item.get("jobUrl", ""),
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
