from urllib.parse import urlparse
import httpx
import re

# Canonical ATS hosts only. Keep SmartRecruiters only if fetched via their API.
ALLOWED = {
    "boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.eu.lever.co",
    "jobs.ashbyhq.com",
    "careers.smartrecruiters.com",
}


def host_allowed(url: str) -> bool:
    try:
        return urlparse(url).netloc in ALLOWED
    except Exception:
        return False


_TOMBSTONE = re.compile(
    r"(no longer available|job not found|position closed|no longer posted|no vacancies)",
    re.IGNORECASE,
)


async def link_is_live(url: str) -> bool:
    try:
        timeout = httpx.Timeout(15.0)
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.head(url)
            if resp.status_code in (405, 403):
                resp = await client.get(url)
            if resp.status_code // 100 != 2:
                return False
            text = (resp.text or "")[:4000]
            return _TOMBSTONE.search(text) is None
    except Exception:
        return False


