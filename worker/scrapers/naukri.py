import os
import time
import traceback
from typing import List, Optional

from .base import BaseScraper
from config import REQUEST_DELAY_SECONDS
from utils.logger import get_logger

logger = get_logger(__name__)

NAUKRI_LIST_URLS = [
    "https://www.naukri.com/cfo-jobs",
    "https://www.naukri.com/finance-director-jobs",
]


class NaukriScraper(BaseScraper):
    source_name = "naukri"

    def _collect_cards(self, page):
        selectors = [
            "article.jobTuple",
            'div[class*="jobTuple"]',
            'div[class*="srp-jobtuple"]',
        ]
        for sel in selectors:
            cards = page.query_selector_all(sel)
            if cards:
                return cards
        return []

    def _abs_url(self, href: Optional[str]) -> str:
        if not href:
            return ""
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return f"https://www.naukri.com{href}"
        return f"https://www.naukri.com/{href.lstrip('/')}"

    def _extract_job_from_card(self, card) -> Optional[dict]:
        try:
            title_el = card.query_selector("a.title")
            if not title_el:
                title_el = card.query_selector('a[class*="title"]')
            if not title_el:
                return None

            title = title_el.inner_text().strip()
            href = title_el.get_attribute("href")
            url_val = self._abs_url(href)
            if not title or not url_val:
                return None

            company_el = card.query_selector("a.subTitle")
            if not company_el:
                company_el = card.query_selector('a[class*="comp-name"]')
            company = company_el.inner_text().strip() if company_el else ""

            loc_el = card.query_selector('span[class*="location"]')
            location_text = loc_el.inner_text().strip() if loc_el else ""

            job = self.normalize({
                "title": title,
                "company": company,
                "location": location_text,
                "url": url_val,
            })
            job["hash"] = self.make_hash(job)
            return job
        except Exception:
            return None

    def scrape(self, profile: dict) -> List[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not installed. Skipping Naukri.")
            return []

        all_jobs: List[dict] = []
        browser = None

        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                except Exception:
                    logger.error(
                        "Naukri: Playwright failed to launch Chromium. "
                        "Install browsers with: playwright install chromium"
                    )
                    traceback.print_exc()
                    logger.info("Naukri: found 0 jobs")
                    return []

                try:
                    context = browser.new_context(user_agent=self.get_headers()["User-Agent"])
                    page = context.new_page()

                    for url in NAUKRI_LIST_URLS:
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=45000)
                            time.sleep(3)

                            if os.environ.get("NAUKRI_DEBUG", "").lower() in ("1", "true", "yes"):
                                with open("naukri_debug.html", "w", encoding="utf-8") as f:
                                    f.write(page.content())
                                logger.info("NAUKRI_DEBUG: wrote naukri_debug.html (cwd)")

                            cards = self._collect_cards(page)
                            for card in cards[:50]:
                                job = self._extract_job_from_card(card)
                                if job:
                                    all_jobs.append(job)

                            time.sleep(REQUEST_DELAY_SECONDS)
                        except Exception as e:
                            logger.error(f"Naukri scrape error for '{url}': {e}")
                            traceback.print_exc()

                finally:
                    if browser is not None:
                        try:
                            browser.close()
                        except Exception:
                            traceback.print_exc()

        except Exception:
            logger.error("Naukri: Playwright error (outside browser session)")
            traceback.print_exc()

        logger.info(f"Naukri: found {len(all_jobs)} jobs")
        return all_jobs
