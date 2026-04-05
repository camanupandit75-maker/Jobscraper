"""
Glassdoor scraper using Playwright (best effort — heavy anti-bot).
"""
import time
from urllib.parse import quote_plus
from .base import BaseScraper
from utils.logger import get_logger
from utils.profile_locations import normalize_profile_locations

logger = get_logger(__name__)

class GlassdoorScraper(BaseScraper):
    source_name = "glassdoor"

    def scrape(self, profile: dict) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not installed. Skipping Glassdoor.")
            return []

        all_jobs = []
        keywords = profile.get("keywords", [])
        locs = normalize_profile_locations(profile)
        location = locs[0] if locs else ""

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(user_agent=self.get_headers()["User-Agent"])
            page = context.new_page()
            for keyword in keywords[:1]:
                try:
                    q = quote_plus(keyword)
                    url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={q}&locT=N&locId=115&sortBy=date_desc"
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(4)
                    cards = page.query_selector_all("li.react-job-listing")
                    for card in cards[:20]:
                        try:
                            title_el = card.query_selector("[data-test='job-title']")
                            company_el = card.query_selector("[data-test='employer-name']")
                            loc_el = card.query_selector("[data-test='emp-location']")
                            link_el = card.query_selector("a.jobLink")
                            if title_el and link_el:
                                href = link_el.get_attribute("href") or ""
                                job = self.normalize({
                                    "title": title_el.inner_text().strip(),
                                    "company": company_el.inner_text().strip() if company_el else "",
                                    "location": loc_el.inner_text().strip() if loc_el else location,
                                    "url": f"https://www.glassdoor.com{href}" if href.startswith("/") else href,
                                })
                                job["hash"] = self.make_hash(job)
                                all_jobs.append(job)
                        except Exception:
                            continue
                except Exception as e:
                    logger.error(f"Glassdoor error: {e}")
            browser.close()

        logger.info(f"Glassdoor: found {len(all_jobs)} jobs")
        return all_jobs
