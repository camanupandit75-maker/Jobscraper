import os
from dotenv import load_dotenv

load_dotenv()

# ── Supabase ──────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ── Scrape schedule ───────────────────────────────────────
SCRAPE_INTERVAL_HOURS = 4
MAX_JOBS_PER_SITE_PER_RUN = 50

# ── Your search profiles ──────────────────────────────────
# Edit keywords and locations to match what you're looking for
SEARCH_PROFILES = [
    {
        "name": "CFO India",
        "keywords": ["CFO", "Chief Financial Officer", "Finance Director", "VP Finance"],
        "location": "India",
        "indeed_base_url": "https://in.indeed.com",
        "remote": True,
        "job_type": "full-time",
        "sites": ["remoteok", "indeed", "naukri", "linkedin", "internshala", "wellfound"]
    },
    {
        "name": "CA MENA",
        "keywords": [
            "Chartered Accountant",
            "CA",
            "Financial Controller",
            "Finance Manager",
            "Chief Accountant",
            "Senior Accountant",
            "Group CFO",
            "VP Finance",
        ],
        "location": "UAE",
        "indeed_base_url": "https://gulf.indeed.com",
        "remote": False,
        "job_type": "full-time",
        "sites": ["indeed", "linkedin", "glassdoor"]
    },
    {
        "name": "CA India",
        "keywords": [
            "Chartered Accountant",
            "CA",
            "ICAI",
            "Financial Controller",
            "Finance Manager",
            "Group CFO",
        ],
        "location": "India",
        "indeed_base_url": "https://in.indeed.com",
        "remote": False,
        "job_type": "full-time",
        "sites": ["indeed", "linkedin"]
    },
    {
        "name": "CA Remote Global",
        "keywords": [
            "Chartered Accountant",
            "CA",
            "Remote CFO",
            "Fractional CFO",
            "Virtual CFO",
        ],
        "location": "Remote",
        "remote": True,
        "job_type": "full-time",
        "sites": ["remoteok", "linkedin"]
    },
    {
        "name": "CA Middle East",
        "keywords": [
            "Chartered Accountant",
            "CA",
            "ACCA",
            "CPA",
            "Financial Controller",
            "Chief Accountant",
            "Group Finance Manager",
        ],
        "location": "UAE",
        "indeed_base_url": "https://gulf.indeed.com",
        "remote": False,
        "job_type": "full-time",
        "sites": ["indeed", "linkedin"]
    },
    {
        "name": "CFO Remote Global",
        "keywords": ["CFO", "Chief Financial Officer", "Fractional CFO"],
        "location": "Remote",
        "remote": True,
        "job_type": "full-time",
        "sites": ["remoteok", "wellfound"]
    },
    {
        "name": "ai",
        "keywords": [
            "AI engineer",
            "machine learning",
            "ML engineer",
            "artificial intelligence",
            "LLM",
        ],
        "location": "india, uae, remote",
        "remote": True,
        "job_type": "full-time",
        "sites": ["indeed", "linkedin", "remoteok"],
    },
]

# ── Request settings ──────────────────────────────────────
REQUEST_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 2   # Polite delay between requests
MAX_RETRIES = 3

# ── Webhook (optional) ────────────────────────────────────
# POST to this URL after each scrape run (can leave blank)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
