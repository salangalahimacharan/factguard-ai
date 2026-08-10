import time
import logging
import urllib.parse
from typing import List
from app.schemas.fact_check import SourceMetadata, CredibilityRating

logger = logging.getLogger("factguard.agents.source_credibility")

KNOWN_HIGH_CREDIBILITY_DOMAINS = {
    # Official / International / Government / Academic
    "gov": 95, "edu": 90, "mil": 90,
    "who.int": 95, "cdc.gov": 95, "nasa.gov": 95, "nih.gov": 95, "un.org": 95, "europa.eu": 90,
    "arxiv.org": 90, "nature.com": 95, "sciencedirect.com": 90, "ieee.org": 90, "springer.com": 90,
    "wikipedia.org": 75,
    # Major Tier-1 News Wire & Agencies
    "reuters.com": 92, "apnews.com": 92, "afp.com": 90, "bbc.com": 88, "bbc.co.uk": 88,
    "bloomberg.com": 88, "nytimes.com": 85, "washingtonpost.com": 85, "theguardian.com": 85,
    "ft.com": 88, "wsj.com": 88, "npr.org": 88, "pbs.org": 88, "economist.com": 88
}

KNOWN_LOW_CREDIBILITY_KEYWORDS = [
    "blog", "wordpress", "blogspot", "forum", "gossip", "conspiracy", "clickbait", "tabloid", "satire", "rumor"
]

class SourceCredibilityAgent:
    """Agent 4: Evaluates the credibility, publisher reputation, and domain authority of web sources."""

    async def run(self, sources: List[SourceMetadata]) -> List[SourceMetadata]:
        start_time = time.time()
        logger.info(f"Agent 4 [Source Credibility] evaluating credibility for {len(sources)} sources...")

        evaluated_sources: List[SourceMetadata] = []

        for source in sources:
            score, rating, indicators = self._evaluate_source(source)
            
            # Update source metadata
            source.credibility_score = score
            source.credibility_rating = rating
            source.reliability_indicators = indicators
            evaluated_sources.append(source)

        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Agent 4 [Source Credibility] completed in {elapsed}ms.")
        return evaluated_sources

    def _evaluate_source(self, source: SourceMetadata) -> tuple[float, CredibilityRating, List[str]]:
        domain = self._extract_domain(source.url)
        indicators: List[str] = []
        score = 50.0 # Default baseline

        # Factor 1: Domain check
        matched = False
        for known_domain, domain_score in KNOWN_HIGH_CREDIBILITY_DOMAINS.items():
            if domain == known_domain or domain.endswith("." + known_domain):
                score = float(domain_score)
                indicators.append(f"Recognized authoritative domain: {known_domain}")
                matched = True
                break

        if not matched:
            if any(kw in domain for kw in KNOWN_LOW_CREDIBILITY_KEYWORDS):
                score = 30.0
                indicators.append("Domain associated with user-generated or unverified blog/forum content.")
            else:
                score = 60.0
                indicators.append("Standard public web publisher.")

        # Factor 2: Source Type Boost
        if source.source_type == "official":
            score = min(score + 10.0, 98.0)
            indicators.append("Primary / Official institutional source.")
        elif source.source_type == "academic":
            score = min(score + 10.0, 95.0)
            indicators.append("Peer-reviewed or academic repository.")
        elif source.source_type == "encyclopedia":
            score = min(score, 75.0)
            indicators.append("Crowdsourced encyclopedic reference with citations.")

        # Factor 3: HTTPS & Excerpt Quality
        if source.url.startswith("https://"):
            score = min(score + 2.0, 100.0)
            indicators.append("Secure HTTPS connection.")
        else:
            score = max(score - 10.0, 0.0)
            indicators.append("Insecure HTTP endpoint.")

        if len(source.excerpt) > 100:
            score = min(score + 3.0, 100.0)
            indicators.append("Provides substantial context snippet.")

        score = round(score, 1)

        # Categorize rating
        if score >= 85.0:
            rating = CredibilityRating.VERY_HIGH
        elif score >= 70.0:
            rating = CredibilityRating.HIGH
        elif score >= 50.0:
            rating = CredibilityRating.MEDIUM
        elif score >= 30.0:
            rating = CredibilityRating.LOW
        else:
            rating = CredibilityRating.UNKNOWN

        return score, rating, indicators

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain or "web-source"
        except Exception:
            return "web-source"

source_credibility_agent = SourceCredibilityAgent()
