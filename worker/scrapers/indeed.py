import time
from typing import Optional
from urllib.parse import quote_plus, urlparse, parse_qs
from .base import BaseScraper
from config import REQUEST_DELAY_SECONDS
from utils.logger import get_logger

logger = get_logger(__name__)


class IndeedScraper(BaseScraper):
    source_name = "indeed"

    def _indeed_base(self) -> str:
        return getattr(self, "_indeed_base_url", "https://www.indeed.com").rstrip("/")

    def _build_url(self, keyword: str, location: str) -> str:
        q = quote_plus(keyword)
        loc = quote_plus(location)
        base = self._indeed_base()
        return f"{base}/jobs?q={q}&l={loc}&sort=date"

    def _jk_from_href(self, href: Optional[str]) -> Optional[str]:
        if not href:
            return None
        if "jk=" in href:
            return href.split("jk=")[1].split("&")[0].split("#")[0]
        try:
            qs = parse_qs(urlparse(href).query)
            if "jk" in qs and qs["jk"]:
                return qs["jk"][0]
        except Exception:
            pass
        return None

    def _listing_scope(self, link):
        """Nearest job row/card for querying company/location (link may be <a data-jk>)."""
        try:
            h = link.evaluate_handle(
                """n => n.closest('div.job_seen_beacon, li.resultContent, td.resultContent, tr')"""
            )
            if h is not None:
                el = h.as_element()
                if el is not None:
                    return el
        except Exception:
            pass
        return link

    def _extract_job_from_card(self, card) -> Optional[dict]:
        try:
            link = card
            if card.get_attribute("data-jk") is None:
                link = card.query_selector("a[data-jk]")
            if not link:
                link = card.query_selector("a.jcs-JobTitle")
            if not link:
                link = card.query_selector('h2 a[href*="viewjob"], h2 a[href*="jobs/view"]')
            if not link:
                return None

            jk = link.get_attribute("data-jk")
            href = link.get_attribute("href")
            if not jk:
                jk = self._jk_from_href(href)

            title = link.inner_text().strip()
            if not title:
                t2 = card.query_selector("h2.jobTitle span[title]")
                if t2:
                    title = (t2.get_attribute("title") or t2.inner_text() or "").strip()
            if not title:
                t3 = card.query_selector("h2.jobTitle, h2 a span")
                if t3:
                    title = t3.inner_text().strip()

            if not title or not jk:
                return None

            scope = self._listing_scope(link)
            company_el = scope.query_selector("[data-testid='company-name']")
            company = company_el.inner_text().strip() if company_el else ""

            location_el = scope.query_selector("[data-testid='text-location']")
            loc = location_el.inner_text().strip() if location_el else ""

            salary_el = scope.query_selector("[data-testid='attribute_snippet_testid']")
            salary = salary_el.inner_text().strip() if salary_el else ""

            url = f"{self._indeed_base()}/viewjob?jk={jk}"
            return self.normalize({
                "title": title,
                "company": company,
                "location": loc,
                "salary": salary,
                "url": url,
            })
        except Exception:
            return None

    def _collect_cards(self, page):
        cards = page.query_selector_all("div.job_seen_beacon")
        if not cards:
            cards = page.query_selector_all("div.slider_container div.job_seen_beacon")
        if not cards:
            cards = page.query_selector_all("li.resultContent")
        if not cards:
            seen = set()
            links = []
            for a in page.query_selector_all("a[data-jk]"):
                jk = a.get_attribute("data-jk")
                if jk and jk not in seen:
                    seen.add(jk)
                    links.append(a)
            cards = links
        return cards

    def scrape(self, profile: dict) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not installed. Skipping Indeed.")
            return []

        all_jobs: list[dict] = []
        keywords = profile.get("keywords", [])
        location = profile.get("location", "")
        self._indeed_base_url = str(
            profile.get("indeed_base_url") or "https://www.indeed.com"
        ).rstrip("/")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(user_agent=self.get_headers()["User-Agent"])
            page = context.new_page()

            for keyword in keywords[:3]:
                try:
                    url = self._build_url(keyword, location)
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(3)

                    cards = self._collect_cards(page)
                    for card in cards[:50]:
                        job = self._extract_job_from_card(card)
                        if job:
                            job["hash"] = self.make_hash(job)
                            all_jobs.append(job)

                    time.sleep(REQUEST_DELAY_SECONDS)
                except Exception as e:
                    logger.error(f"Indeed scrape error for '{keyword}': {e}")

            browser.close()

        logger.info(f"Indeed: found {len(all_jobs)} jobs")
        return all_jobs
