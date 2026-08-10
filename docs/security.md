# FactGuard AI Security & AI Safety Documentation

## Security & Defense Architecture

### 1. Untrusted Input Boundary & Prompt Injection Defenses
Social media content submitted for verification is treated strictly as **untrusted user data**.
- All prompt templates wrap input text inside strict block quotes and explicit isolation instructions.
- RegEx sanitization filters out injection patterns like `SYSTEM INSTRUCTION:`, `Assistant:`, and `Ignore previous instructions`.
- System prompts enforce that instruction-like content in posts must be evaluated as text, never executed.

### 2. SSRF Protection for URL Scraper
- The URL scraper validates target hostnames against blocked private IP ranges (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`, `localhost`).
- Non-HTTP/HTTPS protocols are rejected.

### 3. API Key & CORS Security
- API keys are managed purely server-side via `.env` and Pydantic Settings.
- Frontend code never exposes API keys.
- CORS restricted to allowed origin domains.
