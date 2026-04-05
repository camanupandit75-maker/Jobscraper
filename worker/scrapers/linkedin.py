"""
LinkedIn scraper using Playwright.
Scrapes public job listings only — no login required.
"""
import time
from urllib.parse import quote_plus
from .base import BaseScraper
from utils.logger import get_logger

logger = get_logger(__name__)

class LinkedInScraper(BaseScraper):
    source_name = "linkedin"

    def scrape(self, profile: dict) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not installed. Skipping LinkedIn.")
            return []

        all_jobs = []
        keywords = profile.get("keywords", [])
        location = profile.get("location", "")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(user_agent=self.get_headers()["User-Agent"])
            page = context.new_page()

            for keyword in keywords[:2]:
                try:
                    q = quote_plus(keyword)
                    l = quote_plus(location)
                    url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={l}&f_TPR=r86400&sortBy=DD"
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(3)
                    # Scroll to load more
                    for _ in range(3):
                        page.keyboard.press("End")
                        time.sleep(1.5)
                    cards = page.query_selector_all(".job-search-card")
                    for card in cards[:30]:
                        try:
                            title = card.query_selector("h3.base-search-card__title")
                            company = card.query_selector("h4.base-search-card__subtitle")
                            location_el = card.query_selector("span.job-search-card__location")
                            link = card.query_selector("a.base-card__full-link")
                            if title and link:
                                job = self.normalize({
                                    "title": title.inner_text().strip(),
                                    "company": company.inner_text().strip() if company else "",
                                    "location": location_el.inner_text().strip() if location_el else "",
                                    "url": link.get_attribute("href") or "",
                                })
                                job["hash"] = self.make_hash(job)
                                all_jobs.append(job)
                        except Exception:
                            continue
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"LinkedIn error for '{keyword}': {e}")
            browser.close()

        logger.info(f"LinkedIn: found {len(all_jobs)} jobs")
        return all_jobs
