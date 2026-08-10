import httpx
import urllib.parse
import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("factguard.services.url_scraper")

BLOCKED_IP_PATTERNS = [
    r'^127\.', r'^10\.', r'^172\.(1[6-9]|2[0-9]|3[0-1])\.', r'^192\.168\.',
    r'^localhost$', r'^0\.0\.0\.0$'
]

class URLScraperService:
    """Safely extracts headline and article body text from target URLs with SSRF protection."""

    async def fetch_url_content(self, url: str) -> tuple[str, str]:
        # SSRF Protection Check
        if not self._is_safe_url(url):
            raise ValueError("Target URL is invalid or targets an internal restricted IP address.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            
            html_content = resp.text
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style tags
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.extract()

            title = soup.title.string.strip() if soup.title and soup.title.string else "Web Article"
            
            # Extract main article paragraphs
            paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 30]
            body_text = "\n\n".join(paragraphs[:10])

            if not body_text:
                body_text = soup.get_text()[:2000]

            return title, f"Article Headline: {title}\n\n{body_text}"

    def _is_safe_url(self, url: str) -> bool:
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False
            
            hostname = parsed.hostname.lower() if parsed.hostname else ""
            for pattern in BLOCKED_IP_PATTERNS:
                if re.search(pattern, hostname):
                    return False
            return True
        except Exception:
            return False

url_scraper_service = URLScraperService()
