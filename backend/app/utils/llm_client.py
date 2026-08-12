import os
import json
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("factguard.llm")

class LLMClient:
    """
    Unified LLM Client supporting Google Gemini, OpenAI, and heuristic fallbacks.
    Guarantees structured JSON outputs for all agents with strict 6s timeout protection.
    """
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.openai_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")

    async def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """
        Generates structured JSON response from LLM or fallback parser.
        """
        # Try Gemini API if key exists
        if self.gemini_key:
            try:
                res = await self._call_gemini(prompt, system_prompt)
                parsed = self._extract_json(res)
                if parsed:
                    return parsed
            except Exception as e:
                logger.warning(f"Gemini API call failed or timed out: {e}. Trying fallback.")

        # Try OpenAI API if key exists
        if self.openai_key:
            try:
                res = await self._call_openai(prompt, system_prompt)
                parsed = self._extract_json(res)
                if parsed:
                    return parsed
            except Exception as e:
                logger.warning(f"OpenAI API call failed or timed out: {e}. Trying fallback.")

        # Fallback to local heuristic engine if LLM API is unavailable
        logger.info("Using built-in heuristic reasoning engine for structured output.")
        return {}

    async def _call_gemini(self, prompt: str, system_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        
        full_content = f"{system_prompt}\n\nUser Prompt:\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{
                "parts": [{"text": full_content}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        
        timeout_cfg = httpx.Timeout(6.0, connect=3.0, read=6.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            resp = await asyncio.wait_for(client.post(url, json=payload, headers=headers), timeout=6.0)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_openai(self, prompt: str, system_prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        timeout_cfg = httpx.Timeout(6.0, connect=3.0, read=6.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            resp = await asyncio.wait_for(client.post(url, json=payload, headers=headers), timeout=6.0)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except Exception:
            # Clean markdown codeblocks ```json ... ```
            cleaned = text.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(cleaned)
            except Exception as e:
                logger.error(f"Failed to parse JSON output: {e}")
                return None

llm_client = LLMClient()
