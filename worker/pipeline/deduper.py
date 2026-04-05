def dedupe_jobs(jobs: list[dict], existing_hashes: set) -> list[dict]:
    """Remove jobs already in Supabase and internal duplicates."""
    seen = set()
    unique = []
    for job in jobs:
        h = job.get("hash", "")
        if h and h not in existing_hashes and h not in seen:
            seen.add(h)
            unique.append(job)
    return unique
