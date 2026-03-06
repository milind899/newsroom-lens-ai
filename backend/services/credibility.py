"""
Source credibility lookup service.

Provides a hardcoded database of known media sources with credibility ratings
modeled after MBFC (Media Bias/Fact Check) style assessments. No external API
calls are made — this is a pure local lookup table.
"""

from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Credibility database
# ---------------------------------------------------------------------------
# Each entry maps a bare domain to:
#   reliability_score  : 0-100 overall trustworthiness
#   bias_rating        : political leaning
#   factual_reporting  : accuracy of factual claims
#   category           : type of outlet
#
# Ratings are based on publicly available MBFC-style assessments and
# cross-referenced with independent media literacy resources.
# ---------------------------------------------------------------------------

_CREDIBILITY_DB: dict[str, dict] = {
    # ── Indian sources ─────────────────────────────────────────────────────
    "ndtv.com": {
        "reliability_score": 72,
        "bias_rating": "center-left",
        "factual_reporting": "high",
        "category": "television / digital news",
    },
    "thewire.in": {
        "reliability_score": 68,
        "bias_rating": "left",
        "factual_reporting": "high",
        "category": "independent digital media",
    },
    "opindia.com": {
        "reliability_score": 30,
        "bias_rating": "right",
        "factual_reporting": "low",
        "category": "digital media / opinion",
    },
    "thehindu.com": {
        "reliability_score": 82,
        "bias_rating": "center-left",
        "factual_reporting": "very high",
        "category": "national newspaper",
    },
    "hindustantimes.com": {
        "reliability_score": 72,
        "bias_rating": "center",
        "factual_reporting": "high",
        "category": "national newspaper",
    },
    "indiatoday.in": {
        "reliability_score": 68,
        "bias_rating": "center",
        "factual_reporting": "high",
        "category": "television / digital news",
    },
    "scroll.in": {
        "reliability_score": 70,
        "bias_rating": "center-left",
        "factual_reporting": "high",
        "category": "independent digital media",
    },
    "swarajyamag.com": {
        "reliability_score": 40,
        "bias_rating": "right",
        "factual_reporting": "mixed",
        "category": "digital magazine",
    },
    "newslaundry.com": {
        "reliability_score": 70,
        "bias_rating": "center-left",
        "factual_reporting": "high",
        "category": "independent digital media / media criticism",
    },
    "theprint.in": {
        "reliability_score": 72,
        "bias_rating": "center",
        "factual_reporting": "high",
        "category": "independent digital media",
    },
    "firstpost.com": {
        "reliability_score": 58,
        "bias_rating": "center-right",
        "factual_reporting": "mixed",
        "category": "digital news",
    },
    "livemint.com": {
        "reliability_score": 78,
        "bias_rating": "center",
        "factual_reporting": "high",
        "category": "financial / business news",
    },
    "republicworld.com": {
        "reliability_score": 32,
        "bias_rating": "right",
        "factual_reporting": "low",
        "category": "television / digital news",
    },
    "zeenews.india.com": {
        "reliability_score": 38,
        "bias_rating": "right",
        "factual_reporting": "mixed",
        "category": "television / digital news",
    },
    "aajtak.in": {
        "reliability_score": 42,
        "bias_rating": "center-right",
        "factual_reporting": "mixed",
        "category": "television / digital news",
    },
    "news18.com": {
        "reliability_score": 50,
        "bias_rating": "center-right",
        "factual_reporting": "mixed",
        "category": "television / digital news",
    },
    "deccanherald.com": {
        "reliability_score": 76,
        "bias_rating": "center",
        "factual_reporting": "high",
        "category": "regional newspaper",
    },
    "indianexpress.com": {
        "reliability_score": 78,
        "bias_rating": "center",
        "factual_reporting": "high",
        "category": "national newspaper",
    },
    "tribuneindia.com": {
        "reliability_score": 74,
        "bias_rating": "center",
        "factual_reporting": "high",
        "category": "regional newspaper",
    },
    "outlookindia.com": {
        "reliability_score": 66,
        "bias_rating": "center-left",
        "factual_reporting": "high",
        "category": "news magazine",
    },

    # ── International sources ──────────────────────────────────────────────
    "bbc.com": {
        "reliability_score": 82,
        "bias_rating": "center-left",
        "factual_reporting": "high",
        "category": "public broadcaster",
    },
    "aljazeera.com": {
        "reliability_score": 65,
        "bias_rating": "center-left",
        "factual_reporting": "mixed",
        "category": "state-funded broadcaster",
    },
    "reuters.com": {
        "reliability_score": 92,
        "bias_rating": "center",
        "factual_reporting": "very high",
        "category": "wire service / news agency",
    },
    "apnews.com": {
        "reliability_score": 92,
        "bias_rating": "center",
        "factual_reporting": "very high",
        "category": "wire service / news agency",
    },
    "cnn.com": {
        "reliability_score": 62,
        "bias_rating": "left",
        "factual_reporting": "mixed",
        "category": "television / digital news",
    },
    "foxnews.com": {
        "reliability_score": 38,
        "bias_rating": "right",
        "factual_reporting": "mixed",
        "category": "television / digital news",
    },
    "nytimes.com": {
        "reliability_score": 82,
        "bias_rating": "center-left",
        "factual_reporting": "high",
        "category": "national newspaper",
    },
    "washingtonpost.com": {
        "reliability_score": 80,
        "bias_rating": "center-left",
        "factual_reporting": "high",
        "category": "national newspaper",
    },
    "theguardian.com": {
        "reliability_score": 76,
        "bias_rating": "center-left",
        "factual_reporting": "high",
        "category": "national newspaper",
    },
    "rt.com": {
        "reliability_score": 20,
        "bias_rating": "right",
        "factual_reporting": "very low",
        "category": "state-controlled media",
    },
    "breitbart.com": {
        "reliability_score": 22,
        "bias_rating": "right",
        "factual_reporting": "low",
        "category": "digital media / opinion",
    },
    "huffpost.com": {
        "reliability_score": 56,
        "bias_rating": "left",
        "factual_reporting": "mixed",
        "category": "digital media / opinion",
    },
}

# Build an alternate-domain lookup so common subdomains also resolve.
# e.g. "www.ndtv.com" → "ndtv.com", "edition.cnn.com" → "cnn.com"
_DOMAIN_ALIASES: dict[str, str] = {}
for _domain in _CREDIBILITY_DB:
    # Map bare domain with www prefix
    _DOMAIN_ALIASES[f"www.{_domain}"] = _domain

# Additional manual aliases for domains whose user-facing hostname
# differs from the canonical key in the database.
_DOMAIN_ALIASES.update({
    "edition.cnn.com": "cnn.com",
    "bbc.co.uk": "bbc.com",
    "www.bbc.co.uk": "bbc.com",
    "m.hindustantimes.com": "hindustantimes.com",
    "m.ndtv.com": "ndtv.com",
    "m.republicworld.com": "republicworld.com",
    "m.timesofindia.com": "timesofindia.com",
    "zeenews.com": "zeenews.india.com",
    "www.zeenews.com": "zeenews.india.com",
})


# ---------------------------------------------------------------------------
# Unknown / default response
# ---------------------------------------------------------------------------
_UNKNOWN_RESPONSE: dict = {
    "known": False,
    "domain": None,
    "reliability_score": None,
    "bias_rating": "unknown",
    "factual_reporting": "unknown",
    "category": "unknown",
    "description": "This source is not in our credibility database. Exercise caution and cross-check claims with established outlets.",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _extract_domain(url: str) -> str:
    """Extract the bare hostname from a URL string.

    Handles inputs like:
      - "https://www.ndtv.com/india-news/some-article"
      - "ndtv.com"
      - "www.ndtv.com"
    """
    url = url.strip()
    # If there is no scheme, urlparse puts everything in `path`.
    if "://" not in url:
        url = f"https://{url}"
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return hostname.lower()


def _resolve_domain(hostname: str) -> str | None:
    """Try to resolve a hostname to a canonical domain key in the database.

    Checks in order:
      1. Exact match in _CREDIBILITY_DB
      2. Exact match in _DOMAIN_ALIASES
      3. Stripped "www." prefix
      4. Two-level suffix match (e.g. "news.bbc.com" -> "bbc.com")
    """
    if hostname in _CREDIBILITY_DB:
        return hostname

    if hostname in _DOMAIN_ALIASES:
        return _DOMAIN_ALIASES[hostname]

    # Strip leading www.
    if hostname.startswith("www."):
        bare = hostname[4:]
        if bare in _CREDIBILITY_DB:
            return bare

    # Try the last two segments (registrable domain approximation)
    parts = hostname.split(".")
    if len(parts) > 2:
        candidate = ".".join(parts[-2:])
        if candidate in _CREDIBILITY_DB:
            return candidate

    return None


def get_source_credibility(url: str) -> dict:
    """Look up credibility data for a news source URL.

    Parameters
    ----------
    url : str
        A full URL (e.g. "https://www.ndtv.com/article/12345") or a bare
        domain (e.g. "ndtv.com").

    Returns
    -------
    dict
        Credibility data with keys:
          - known (bool)
          - domain (str | None)
          - reliability_score (int | None)
          - bias_rating (str)
          - factual_reporting (str)
          - category (str)
          - description (str)
    """
    hostname = _extract_domain(url)
    if not hostname:
        logger.debug("Could not extract domain from URL: %s", url)
        return {**_UNKNOWN_RESPONSE}

    canonical = _resolve_domain(hostname)
    if canonical is None:
        logger.debug("Domain not in credibility DB: %s", hostname)
        resp = {**_UNKNOWN_RESPONSE, "domain": hostname}
        return resp

    entry = _CREDIBILITY_DB[canonical]
    score = entry["reliability_score"]

    # Human-readable summary
    if score >= 80:
        description = "Generally considered a highly credible source with strong editorial standards."
    elif score >= 65:
        description = "Considered a credible source, though some editorial bias may be present."
    elif score >= 50:
        description = "Mixed credibility. Claims should be cross-checked with more reliable outlets."
    elif score >= 35:
        description = "Low credibility. This source has a history of bias and/or questionable reporting."
    else:
        description = "Very low credibility. This source frequently publishes misleading or false information."

    return {
        "known": True,
        "domain": canonical,
        "reliability_score": score,
        "bias_rating": entry["bias_rating"],
        "factual_reporting": entry["factual_reporting"],
        "category": entry["category"],
        "description": description,
    }


def get_all_sources() -> dict[str, dict]:
    """Return the full credibility database (useful for frontend dropdowns or lists)."""
    return {domain: {**data} for domain, data in _CREDIBILITY_DB.items()}
