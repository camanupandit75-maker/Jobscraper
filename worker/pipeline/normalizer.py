from datetime import datetime

def normalize_job_type(raw: str) -> str:
    raw = raw.lower()
    if "remote" in raw:
        return "remote"
    if "part" in raw:
        return "part-time"
    if "contract" in raw or "freelance" in raw:
        return "contract"
    return "full-time"

def normalize_posted_at(raw) -> str:
    if not raw:
        return datetime.utcnow().isoformat()
    if isinstance(raw, datetime):
        return raw.isoformat()
    return str(raw)

def normalize_jobs(jobs: list[dict]) -> list[dict]:
    normalized = []
    for job in jobs:
        job["job_type"] = normalize_job_type(job.get("job_type", ""))
        job["posted_at"] = normalize_posted_at(job.get("posted_at"))
        job["title"] = job.get("title", "").strip()
        job["company"] = job.get("company", "").strip()
        job["location"] = job.get("location", "").strip()
        if job["title"]:  # Skip empty titles
            normalized.append(job)
    return normalized
