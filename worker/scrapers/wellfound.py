"""
Wellfound (formerly AngelList) scraper using Playwright.
"""
import time
from typing import List
from urllib.parse import quote_plus
from .base import BaseScraper
from utils.logger import get_logger

logger = get_logger(__name__)

class WellfoundScraper(BaseScraper):
    source_name = "wellfound"

    def scrape(self, profile: dict) -> List[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not installed. Skipping Wellfound.")
            return []

        all_jobs: List[dict] = []
        keywords = profile.get("keywords", [])

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(user_agent=self.get_headers()["User-Agent"])
            page = context.new_page()
            for keyword in keywords[:2]:
                try:
                    q = quote_plus(keyword)
                    url = f"https://wellfound.com/jobs?q={q}"
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5)
                    try:
                        page.wait_for_selector("a[data-test='job-link']", timeout=10000)
                    except Exception:
                        pass
                    cards = page.query_selector_all("[data-test='StartupResult']")
                    if not cards:
                        cards = page.query_selector_all(".styles_component__Ey28k")
                    for card in cards[:30]:
                        try:
                            title_el = card.query_selector("a[data-test='job-link']")
                            company_el = card.query_selector("a[data-test='startup-link']")
                            loc_el = card.query_selector("[data-test='location']")
                            if title_el:
                                href = title_el.get_attribute("href") or ""
                                job = self.normalize({
                                    "title": title_el.inner_text().strip(),
                                    "company": company_el.inner_text().strip() if company_el else "",
                                    "location": loc_el.inner_text().strip() if loc_el else "Remote",
                                    "url": f"https://wellfound.com{href}" if href.startswith("/") else href,
                                })
                                job["hash"] = self.make_hash(job)
                                all_jobs.append(job)
                        except Exception:
                            continue
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Wellfound error for '{keyword}': {e}")
            browser.close()

        logger.info(f"Wellfound: found {len(all_jobs)} jobs")
        return all_jobs
