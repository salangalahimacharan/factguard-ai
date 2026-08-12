import asyncio
import time
import logging
import httpx
import urllib.parse
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from app.schemas.fact_check import ClaimExtractionItem, SourceMetadata, CredibilityRating
from app.config import settings

logger = logging.getLogger("factguard.agents.researcher")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class ResearchAgent:
    """Agent 2: Multi-engine web researcher using live DuckDuckGo, Wikipedia, Google News, and Tavily APIs."""

    async def run(self, claim: ClaimExtractionItem) -> List[SourceMetadata]:
        start_time = time.time()
        logger.info(f"Agent 2 [Researcher] researching claim {claim.claim_id}: '{claim.claim_text}'")

        # Generate targeted search query strategies
        queries = self._generate_search_queries(claim)
        
        # Execute search queries concurrently in parallel!
        search_tasks = [self._execute_search(q, qt) for qt, q in queries.items()]
        query_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        raw_results: List[Dict[str, Any]] = []
        for res_list in query_results:
            if isinstance(res_list, list):
                raw_results.extend(res_list)

        # Deduplicate results by normalized URL
        seen_urls = set()
        sources: List[SourceMetadata] = []
        
        for idx, res in enumerate(raw_results):
            url = res.get("url", "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            # Determine publisher & source type from URL
            domain = self._extract_domain(url)
            publisher = res.get("publisher") or domain
            source_type = self._determine_source_type(domain)

            sources.append(SourceMetadata(
                source_id=f"SRC-{claim.claim_id}-{len(sources)+1:02d}",
                claim_id=claim.claim_id,
                title=res.get("title", f"Information regarding {domain}"),
                url=url,
                publisher=publisher,
                publication_date=res.get("date"),
                excerpt=res.get("snippet", claim.claim_text)[:500],
                source_type=source_type,
                credibility_score=50.0, # Refined by Source Credibility Agent
                credibility_rating=CredibilityRating.MEDIUM,
                reliability_indicators=[f"Type: {source_type}", f"Domain: {domain}"]
            ))

        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Agent 2 [Researcher] found {len(sources)} unique sources for claim {claim.claim_id} in {elapsed}ms.")
        return sources

    def _generate_search_queries(self, claim: ClaimExtractionItem) -> Dict[str, str]:
        claim_text = claim.claim_text
        if claim_text.startswith("http://") or claim_text.startswith("https://") or "URL:" in claim_text or "http" in claim_text:
            url_match = re.search(r'https?://[^\s]+', claim_text)
            if url_match:
                parsed = urllib.parse.urlparse(url_match.group(0))
                domain_parts = [p for p in parsed.netloc.split('.') if p not in ['www', 'com', 'org', 'gov', 'net', 'edu', 'int', 'io', 'ai']]
                claim_text = " ".join(domain_parts) if domain_parts else parsed.netloc
            else:
                claim_text = re.sub(r'https?://[^\s]+', '', claim_text).strip()
        
        # Clean search terms without quotes
        clean_text = re.sub(r'[^\w\s]', ' ', claim_text)
        words = [w for w in clean_text.split() if len(w) > 2]
        keywords = " ".join(words[:8]) or "general claim verification"

        # Multi-query strategy for reliable evidence retrieval
        queries = {
            "direct_claim": f"{keywords}".strip(),
            "fact_check": f"{keywords} fact check evidence".strip()
        }
        return queries

    async def _execute_search(self, query: str, query_type: str) -> List[Dict[str, Any]]:
        # Run search engines concurrently in parallel!
        tasks = [
            self._search_duckduckgo_html(query),
            self._search_wikipedia(query),
            self._search_google_news_rss(query)
        ]
        engine_results = await asyncio.gather(*tasks, return_exceptions=True)
        results = []
        for r in engine_results:
            if isinstance(r, list):
                results.extend(r)
        return results

    async def _search_duckduckgo_html(self, query: str) -> List[Dict[str, Any]]:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        data = {"q": query}

        try:
            timeout_cfg = httpx.Timeout(3.5, connect=2.5, read=3.5)
            async with httpx.AsyncClient(timeout=timeout_cfg, follow_redirects=True) as client:
                resp = await asyncio.wait_for(client.post(url, data=data, headers=headers), timeout=3.5)
                if resp.status_code != 200:
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                results = []

                for result in soup.select(".result"):
                    title_elem = result.select_one(".result__title a")
                    snippet_elem = result.select_one(".result__snippet")

                    if not title_elem:
                        continue

                    raw_href = title_elem.get("href", "")
                    actual_url = self._clean_ddg_url(raw_href)

                    if actual_url and actual_url.startswith("http"):
                        results.append({
                            "title": title_elem.get_text(strip=True),
                            "url": actual_url,
                            "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                            "publisher": self._extract_domain(actual_url)
                        })

                    if len(results) >= 4:
                        break

                return results
        except Exception as e:
            logger.debug(f"DuckDuckGo search error: {e}")
            return []

    async def _search_wikipedia(self, query: str) -> List[Dict[str, Any]]:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "utf8": 1,
            "srlimit": 3
        }
        headers = {"User-Agent": "FactGuardAI/1.0 (academic; project@factguard.ai)"}

        try:
            timeout_cfg = httpx.Timeout(3.5, connect=2.5, read=3.5)
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                resp = await asyncio.wait_for(client.get(url, params=params, headers=headers), timeout=3.5)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                search_items = data.get("query", {}).get("search", [])
                results = []

                for item in search_items:
                    title = item.get("title", "")
                    snippet_raw = item.get("snippet", "")
                    clean_snippet = BeautifulSoup(snippet_raw, "html.parser").get_text(strip=True)

                    wiki_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    results.append({
                        "title": f"Wikipedia: {title}",
                        "url": wiki_url,
                        "snippet": clean_snippet,
                        "publisher": "Wikipedia Encyclopedia"
                    })
                return results
        except Exception as e:
            logger.debug(f"Wikipedia search error: {e}")
            return []

    async def _search_google_news_rss(self, query: str) -> List[Dict[str, Any]]:
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        headers = {"User-Agent": USER_AGENT}

        try:
            timeout_cfg = httpx.Timeout(3.5, connect=2.5, read=3.5)
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                resp = await asyncio.wait_for(client.get(rss_url, headers=headers), timeout=3.5)
                if resp.status_code != 200:
                    return []

                soup = BeautifulSoup(resp.text, "xml")
                results = []

                for item in soup.find_all("item")[:3]:
                    title = item.find("title").get_text(strip=True) if item.find("title") else ""
                    link = item.find("link").get_text(strip=True) if item.find("link") else ""
                    pub_date = item.find("pubDate").get_text(strip=True) if item.find("pubDate") else None

                    if link:
                        results.append({
                            "title": title,
                            "url": link,
                            "snippet": title,
                            "publisher": self._extract_domain(link),
                            "date": pub_date
                        })
                return results
        except Exception as e:
            logger.debug(f"Google News RSS error: {e}")
            return []

    def _clean_ddg_url(self, raw_url: str) -> str:
        if "uddg=" in raw_url:
            match = re.search(r'uddg=([^&]+)', raw_url)
            if match:
                return urllib.parse.unquote(match.group(1))
        return raw_url

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc or parsed.path.split('/')[0]
            netloc = re.sub(r'^www\.', '', netloc)
            return netloc
        except Exception:
            return "Web Source"

    def _determine_source_type(self, domain: str) -> str:
        domain_lower = domain.lower()
        if any(gov in domain_lower for gov in [".gov", ".edu", "who.int", "nasa.gov", "cdc.gov", "nih.gov"]):
            return "official"
        elif any(news in domain_lower for news in ["reuters", "apnews", "bbc", "nytimes", "bloomberg", "theguardian"]):
            return "news"
        elif "wikipedia" in domain_lower:
            return "academic"
        else:
            return "news"

research_agent = ResearchAgent()
