from urllib.parse import urlparse
from app.models import SourceTier


# Major established publications mapping to MEDIUM tier.
# Can be expanded as needed.
MEDIUM_TIER_DOMAINS = {
    "reuters.com",
    "bbc.com",
    "bbc.co.uk",
    "apnews.com",
    "nytimes.com",
    "washingtonpost.com",
    "theguardian.com",
    "wsj.com",
    "npr.org",
    "bloomberg.com",
    "ft.com",
}

# Organizations mapped to HIGH tier alongside standard top-level domains.
HIGH_TIER_DOMAINS = {
    "who.int",
    "un.org",
    "worldbank.org",
    "imf.org",
    "wto.org",
    "cdc.gov",
    "nih.gov",
    "nasa.gov",
}


def rank_source(url: str) -> SourceTier:
    """
    Rank a source URL into a SourceTier based on its domain.
    """
    if not url:
        return SourceTier.LOW
        
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if not domain:
            # Maybe the URL is just a domain string without scheme
            domain = url.lower()
            
        # Strip common subdomains for easier matching
        if domain.startswith("www."):
            domain = domain[4:]
            
        # Check explicit high tier domains
        if domain in HIGH_TIER_DOMAINS:
            return SourceTier.HIGH
            
        # Check standard high tier TLDs
        if domain.endswith(".gov") or domain.endswith(".edu") or domain.endswith(".int"):
            return SourceTier.HIGH
            
        # Special case for .org. The prompt says ".org (international organizations) -> HIGH".
        # We explicitly handled some in HIGH_TIER_DOMAINS, but standard .org might be MEDIUM or LOW.
        # Given "LOW: Everything else", we'll check MEDIUM domains explicitly.
        if domain in MEDIUM_TIER_DOMAINS:
            return SourceTier.MEDIUM
            
        return SourceTier.LOW
    except Exception:
        return SourceTier.LOW
