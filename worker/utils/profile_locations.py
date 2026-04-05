"""
Normalize profile location(s) from Supabase/config (string or list).
"""
from typing import List


def normalize_profile_locations(profile: dict) -> List[str]:
    """
    Prefer profile['locations'] (list); else split profile['location'] on commas.
    Returns [""] when nothing is set (single empty search).
    """
    raw = profile.get("locations")
    if isinstance(raw, list) and len(raw) > 0:
        out = [str(x).strip() for x in raw if str(x).strip()]
        return out if out else [""]
    s = profile.get("location")
    if s is None:
        return [""]
    s = str(s).strip()
    if not s:
        return [""]
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return parts if parts else [""]


def infer_indeed_base_for_location(loc: str) -> str:
    """Pick regional Indeed host from one location string."""
    ll = (loc or "").lower()
    if "india" in ll or ll == "india":
        return "https://in.indeed.com"
    if any(
        x in ll
        for x in (
            "uae",
            "emirates",
            "dubai",
            "abu dhabi",
            "middle east",
            "gulf",
            "ksa",
            "saudi",
            "qatar",
            "kuwait",
            "bahrain",
            "oman",
        )
    ):
        return "https://gulf.indeed.com"
    return "https://www.indeed.com"


def infer_indeed_base_from_locations(locations: List[str]) -> str:
    """Heuristic when a profile has one effective region string (legacy / single loc)."""
    if not locations:
        return "https://www.indeed.com"
    joined = " ".join(locations).lower()
    if "india" in joined or joined.strip() == "india":
        return "https://in.indeed.com"
    if any(
        x in joined
        for x in (
            "uae",
            "emirates",
            "dubai",
            "abu dhabi",
            "middle east",
            "gulf",
            "ksa",
            "saudi",
            "qatar",
            "kuwait",
            "bahrain",
            "oman",
        )
    ):
        return "https://gulf.indeed.com"
    return "https://www.indeed.com"
