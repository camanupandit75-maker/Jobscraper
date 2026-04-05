"""
Drop US/UK/Canada/Australia-listed jobs when the profile targets India, Gulf, MENA, or Remote only.

See filter_jobs_by_western_exclusion() — used by Indeed and LinkedIn after cards are collected.
"""
from __future__ import annotations

import re
from typing import List

from utils.logger import get_logger

logger = get_logger(__name__)

# Job listing location must not match these when the geo filter applies (case-insensitive).
_JOB_WESTERN_PHRASES = (
    "united states",
    "united kingdom",
)
_JOB_WESTERN_WORD_RE = (
    re.compile(r"\busa\b", re.I),
    re.compile(r"\bu\.s\.a\.?\b", re.I),
    re.compile(r"\bu\.s\.?\b", re.I),
    re.compile(r"\buk\b", re.I),
    re.compile(r"\bu\.k\.?\b", re.I),
    re.compile(r"\bengland\b", re.I),
    re.compile(r"\bcanada\b", re.I),
    re.compile(r"\baustralia\b", re.I),
)


def _job_location_matches_western_exclusion(job_location: str) -> bool:
    s = (job_location or "").lower()
    for ph in _JOB_WESTERN_PHRASES:
        if ph in s:
            return True
    for rx in _JOB_WESTERN_WORD_RE:
        if rx.search(job_location or ""):
            return True
    return False


# If any profile location matches, we do not apply the western-job filter.
_PROFILE_WESTERN_PHRASES = (
    "united states",
    "united kingdom",
)
_PROFILE_WESTERN_RES = (
    re.compile(r"\busa\b", re.I),
    re.compile(r"\bu\.s\.a\.?\b", re.I),
    re.compile(r"\bu\.s\.?\b", re.I),
    re.compile(r"\buk\b", re.I),
    re.compile(r"\bu\.k\.?\b", re.I),
    re.compile(r"\bengland\b", re.I),
    re.compile(r"\bcanada\b", re.I),
    re.compile(r"\baustralia\b", re.I),
)


def _profile_explicitly_includes_western_countries(locations: List[str]) -> bool:
    for raw in locations:
        loc = (raw or "").strip()
        if not loc:
            continue
        lo = loc.lower()
        for ph in _PROFILE_WESTERN_PHRASES:
            if ph in lo:
                return True
        for rx in _PROFILE_WESTERN_RES:
            if rx.search(loc):
                return True
    return False


# Profile location is treated as India / UAE / Saudi / Remote / MENA only if it matches one of these.
_PROFILE_TARGET_RES = (
    re.compile(r"\bremote\b", re.I),
    re.compile(r"\bwfh\b", re.I),
    re.compile(r"\bwork from home\b", re.I),
    re.compile(r"\bindia\b", re.I),
    re.compile(r"\bindian\b", re.I),
    re.compile(r"\bbangalore\b", re.I),
    re.compile(r"\bbengaluru\b", re.I),
    re.compile(r"\bmumbai\b", re.I),
    re.compile(r"\bdelhi\b", re.I),
    re.compile(r"\bhyderabad\b", re.I),
    re.compile(r"\bchennai\b", re.I),
    re.compile(r"\bpune\b", re.I),
    re.compile(r"\bkolkata\b", re.I),
    re.compile(r"\bahmedabad\b", re.I),
    re.compile(r"\bgurgaon\b", re.I),
    re.compile(r"\bgurugram\b", re.I),
    re.compile(r"\bnoida\b", re.I),
    re.compile(r"\buae\b", re.I),
    re.compile(r"\bdubai\b", re.I),
    re.compile(r"\babu dhabi\b", re.I),
    re.compile(r"\bsharjah\b", re.I),
    re.compile(r"\bemirates\b", re.I),
    re.compile(r"\bsaudi\b", re.I),
    re.compile(r"\briyadh\b", re.I),
    re.compile(r"\bjeddah\b", re.I),
    re.compile(r"\bdammam\b", re.I),
    re.compile(r"\bksa\b", re.I),
    re.compile(r"\bqatar\b", re.I),
    re.compile(r"\bdoha\b", re.I),
    re.compile(r"\bkuwait\b", re.I),
    re.compile(r"\bbahrain\b", re.I),
    re.compile(r"\bmanama\b", re.I),
    re.compile(r"\boman\b", re.I),
    re.compile(r"\bmuscat\b", re.I),
    re.compile(r"\begypt\b", re.I),
    re.compile(r"\bcairo\b", re.I),
    re.compile(r"\balexandria\b", re.I),
    re.compile(r"\bjordan\b", re.I),
    re.compile(r"\bamman\b", re.I),
    re.compile(r"\blebanon\b", re.I),
    re.compile(r"\bbeirut\b", re.I),
    re.compile(r"\biraq\b", re.I),
    re.compile(r"\bbaghdad\b", re.I),
    re.compile(r"\bmorocco\b", re.I),
    re.compile(r"\bcasablanca\b", re.I),
    re.compile(r"\balgeria\b", re.I),
    re.compile(r"\balgiers\b", re.I),
    re.compile(r"\btunisia\b", re.I),
    re.compile(r"\btunis\b", re.I),
    re.compile(r"\bmena\b", re.I),
    re.compile(r"\bgcc\b", re.I),
    re.compile(r"\bgulf\b", re.I),
    re.compile(r"middle[\s-]east", re.I),
    re.compile(r"\byemen\b", re.I),
    re.compile(r"\blibya\b", re.I),
    re.compile(r"\bsyria\b", re.I),
    re.compile(r"\bpalestine\b", re.I),
    re.compile(r"\bisrael\b", re.I),
    re.compile(r"\btel aviv\b", re.I),
    re.compile(r"\biran\b", re.I),
    re.compile(r"\btehran\b", re.I),
)


def _profile_location_is_india_uae_sa_remote_mena(loc: str) -> bool:
    s = (loc or "").strip()
    if not s:
        return False
    for rx in _PROFILE_TARGET_RES:
        if rx.search(s):
            return True
    return False


def should_apply_western_job_location_filter(locations: List[str]) -> bool:
    """
    True when every non-empty profile location is India/UAE/SA/Remote/MENA-class
    and the profile does not explicitly name US/UK/Canada/Australia.
    """
    non_empty = [x.strip() for x in locations if (x or "").strip()]
    if not non_empty:
        return False
    if _profile_explicitly_includes_western_countries(non_empty):
        return False
    return all(_profile_location_is_india_uae_sa_remote_mena(x) for x in non_empty)


def filter_jobs_by_western_exclusion(jobs: list, profile_locations: List[str]) -> list:
    if not should_apply_western_job_location_filter(profile_locations):
        return jobs
    kept = []
    dropped = 0
    for j in jobs:
        loc = j.get("location") or ""
        if _job_location_matches_western_exclusion(loc):
            dropped += 1
            continue
        kept.append(j)
    if dropped:
        logger.info(
            "Western-location filter: removed %s job(s) (profile targets India/Gulf/MENA/Remote only)",
            dropped,
        )
    return kept
