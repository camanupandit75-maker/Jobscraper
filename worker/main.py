#!/usr/bin/env python3
"""
Main entry point for the job scraper worker.
Runs on Railway 24/7. Scrapes all configured sites every N hours.
"""
import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from config import (
    SEARCH_PROFILES, SCRAPE_INTERVAL_HOURS,
    SUPABASE_URL, SUPABASE_KEY,
)
from pipeline.profiles_loader import fetch_active_search_profiles
from scrapers.remoteok import RemoteOKScraper
from scrapers.indeed import IndeedScraper
from scrapers.naukri import NaukriScraper
from scrapers.internshala import IntershalaScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.wellfound import WellfoundScraper
from scrapers.glassdoor import GlassdoorScraper
from pipeline.normalizer import normalize_jobs
from pipeline.deduper import dedupe_jobs
from pipeline.writer import (
    cleanup_old_jobs,
    get_existing_hashes,
    log_scrape_run,
    upsert_jobs,
)
from utils.logger import get_logger

logger = get_logger("main")


def resolve_search_profiles() -> list:
    """DB-backed profiles when any active rows exist; else config.SEARCH_PROFILES."""
    db_profiles = fetch_active_search_profiles()
    if db_profiles:
        logger.info(f"Using {len(db_profiles)} active profile(s) from Supabase search_profiles")
        return db_profiles
    logger.info("No active search_profiles in Supabase — using config.SEARCH_PROFILES")
    return list(SEARCH_PROFILES)


SCRAPER_MAP = {
    "remoteok":    RemoteOKScraper(),
    "indeed":      IndeedScraper(),
    "naukri":      NaukriScraper(),
    "internshala": IntershalaScraper(),
    "linkedin":    LinkedInScraper(),
    "wellfound":   WellfoundScraper(),
    "glassdoor":   GlassdoorScraper(),
}

CSV_FIELDS = [
    "title", "company", "location", "job_type", "salary", "url", "source", "posted_at",
]


def run_local():
    logger.info("=" * 60)
    logger.info("Local mode: writing to jobs_output.csv (jobs not upserted to Supabase)")
    logger.info("=" * 60)

    all_rows: list[dict] = []
    per_site: dict[str, int] = {}

    for profile in resolve_search_profiles():
        sites = profile.get("sites", [])
        profile_name = profile.get("name", "unknown")
        logger.info(f"\nProfile: {profile_name} | Sites: {sites}")

        for site_name in sites:
            scraper = SCRAPER_MAP.get(site_name)
            if not scraper:
                logger.warning(f"Unknown scraper: {site_name}")
                continue

            try:
                raw_jobs = scraper.scrape(profile)
                normalized = normalize_jobs(raw_jobs)
                for job in normalized:
                    all_rows.append({k: job.get(k, "") or "" for k in CSV_FIELDS})
                per_site[site_name] = per_site.get(site_name, 0) + len(normalized)
            except Exception as e:
                logger.error(f"Error running {site_name} scraper: {e}")

    out_path = Path(__file__).resolve().parent / "jobs_output.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(f"\nWrote {len(all_rows)} rows to {out_path}")
    logger.info("Jobs found per site:")
    for site in sorted(per_site.keys()):
        logger.info(f"  {site}: {per_site[site]}")


def run_scrape():
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
        return

    logger.info("=" * 60)
    logger.info(f"Starting scrape run at {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 60)

    cleanup_old_jobs()

    existing_hashes = get_existing_hashes()
    logger.info(f"Found {len(existing_hashes)} existing jobs in database")

    total_added = 0

    for profile in resolve_search_profiles():
        sites = profile.get("sites", [])
        profile_name = profile.get("name", "unknown")
        logger.info(f"\nProfile: {profile_name} | Sites: {sites}")

        for site_name in sites:
            scraper = SCRAPER_MAP.get(site_name)
            if not scraper:
                logger.warning(f"Unknown scraper: {site_name}")
                continue

            started_at = datetime.now(timezone.utc).isoformat()
            error_msg = None
            jobs_found = 0
            jobs_added = 0

            try:
                raw_jobs = scraper.scrape(profile)
                jobs_found = len(raw_jobs)
                normalized = normalize_jobs(raw_jobs)
                unique = dedupe_jobs(normalized, existing_hashes)
                jobs_added = upsert_jobs(unique)
                # Add new hashes to our local set to avoid re-inserting in same run
                for job in unique:
                    existing_hashes.add(job.get("hash", ""))
                total_added += jobs_added
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error running {site_name} scraper: {e}")

            ended_at = datetime.now(timezone.utc).isoformat()
            log_scrape_run(
                source=site_name,
                jobs_added=jobs_added,
                jobs_found=jobs_found,
                started_at=started_at,
                ended_at=ended_at,
                error=error_msg
            )

    logger.info(f"\nScrape run complete. Total new jobs added: {total_added}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job scraper worker")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Scrape to jobs_output.csv only; no Supabase or scheduler.",
    )
    args = parser.parse_args()

    if args.local:
        run_local()
        sys.exit(0)

    # Run once immediately on startup
    run_scrape()

    # Then schedule recurring runs
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_scrape,
        "interval",
        hours=SCRAPE_INTERVAL_HOURS,
        id="scrape_job",
        max_instances=1
    )
    logger.info(f"Scheduler started. Next run in {SCRAPE_INTERVAL_HOURS} hours.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
