FIN = (
    "finance",
    "financial",
    "analyst",
    "asset",
    "wealth",
    "equity",
    "portfolio",
    "investment",
    "trading",
    "fp&a",
    "valuation",
    "real estate",
    "acquisitions",
    "underwriting",
    "accounting",
    "bloomberg",
    "quickbooks",
    "oracle",
    "audit",
    "treasury",
)

SWE = (
    "software",
    "engineer",
    "developer",
    "backend",
    "frontend",
    "full stack",
    "python",
    "java",
    "c++",
    "react",
    "kubernetes",
    "docker",
    "ml",
    "ai",
    "data",
)


def extract_tokens(text: str) -> set[str]:
    t = (text or "").lower()
    return {w for w in FIN + SWE if w in t}


def token_score(title: str, desc: str, tokens: set[str]) -> float:
    tt = (title + " " + (desc or "")).lower()
    f = sum(1 for k in FIN if k in tt and k in tokens)
    s = sum(1 for k in SWE if k in tt and k in tokens)
    if any(k in tokens for k in FIN) and not any(k in tokens for k in SWE):
        return 2.0 * f - 1.0 * s
    if any(k in tokens for k in SWE):
        return 2.0 * s - 0.5 * f
    return f + s


def intern_like(t: str) -> bool:
    t = (t or "").lower()
    return ("intern" in t) or ("co-op" in t) or ("summer" in t) or ("new grad" in t)


