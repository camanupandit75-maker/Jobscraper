from utils.job_hash import compute_job_hash


def dedupe_jobs(jobs: list[dict], existing_hashes: set) -> list[dict]:
    """Remove jobs already in Supabase and internal duplicates using normalized hash."""
    seen = set()
    unique = []
    for job in jobs:
        h = compute_job_hash(job)
        job["hash"] = h
        if h and h not in existing_hashes and h not in seen:
            seen.add(h)
            unique.append(job)
    return unique
