import re
import time
import logging
from app.schemas.fact_check import BiasAnalysisResult, BiasIndicator
from app.utils.llm_client import llm_client

logger = logging.getLogger("factguard.agents.bias_detector")

SYSTEM_PROMPT = """You are Agent 5: Bias & Manipulation Detection Agent for FactGuard AI.
Your task is to analyze the raw input text for linguistic manipulation, sensationalism, fear-mongering, clickbait, missing context, or absolute claims.

CRITICAL RULE:
- Do NOT label a statement false merely because it uses emotional or sensational language.
- Separate tone/framing analysis from factuality.
- Report specific bias indicators, whether framing is misleading, and evidence excerpts.

Expected JSON output format:
{
  "has_bias": true,
  "sensational_language": true,
  "emotional_manipulation": false,
  "clickbait_framing": true,
  "missing_context": false,
  "bias_score": 65.0,
  "summary": "Text utilizes sensational adjectives and clickbait framing to attract attention.",
  "indicators": [
    {
      "bias_type": "sensationalism",
      "detected": true,
      "description": "Uses hyperbole such as 'SHOCKING SECRET' to provoke emotional response.",
      "evidence_excerpt": "SHOCKING SECRET revealed today"
    }
  ]
}
"""

class BiasDetectorAgent:
    """Agent 5: Detects sensationalism, emotional manipulation, clickbait, and misleading framing."""

    async def run(self, input_text: str) -> BiasAnalysisResult:
        start_time = time.time()
        logger.info("Agent 5 [Bias Detector] analyzing text for manipulation and framing...")

        prompt = f"Analyze the following content for emotional bias and manipulation:\n\n\"\"\"\n{input_text}\n\"\"\""
        llm_res = await llm_client.generate_json(prompt, SYSTEM_PROMPT)

        if llm_res and "bias_score" in llm_res:
            indicators = []
            for item in llm_res.get("indicators", []):
                indicators.append(BiasIndicator(
                    bias_type=item.get("bias_type", "general_bias"),
                    detected=item.get("detected", True),
                    description=item.get("description", "Potential linguistic manipulation detected."),
                    evidence_excerpt=item.get("evidence_excerpt")
                ))

            elapsed = round((time.time() - start_time) * 1000, 2)
            logger.info(f"Agent 5 [Bias Detector] completed in {elapsed}ms. Bias Score={llm_res.get('bias_score')}")
            return BiasAnalysisResult(
                has_bias=llm_res.get("has_bias", False),
                sensational_language=llm_res.get("sensational_language", False),
                emotional_manipulation=llm_res.get("emotional_manipulation", False),
                clickbait_framing=llm_res.get("clickbait_framing", False),
                missing_context=llm_res.get("missing_context", False),
                bias_score=float(llm_res.get("bias_score", 0.0)),
                indicators=indicators,
                summary=llm_res.get("summary", "Analysis completed.")
            )

        # Heuristic fallback analysis
        result = self._heuristic_bias_check(input_text)
        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Agent 5 [Bias Detector] heuristic completed in {elapsed}ms. Bias Score={result.bias_score}")
        return result

    def _heuristic_bias_check(self, text: str) -> BiasAnalysisResult:
        text_lower = text.lower()
        indicators = []
        score = 0.0

        # Check sensationalism / ALL CAPS / exclamation
        sensational_words = ["shocking", "unbelievable", "mind-blowing", "secret", "miracle", "exposed", "devastating"]
        found_sensational = [w for w in sensational_words if w in text_lower]
        has_caps = bool(re.search(r'\b[A-Z]{4,}\b', text))
        has_excl = "!" in text

        if found_sensational or has_caps or has_excl:
            score += 35.0
            indicators.append(BiasIndicator(
                bias_type="sensationalism",
                detected=True,
                description="Contains sensational keywords or dramatic formatting.",
                evidence_excerpt=", ".join(found_sensational[:3]) if found_sensational else "Formatting"
            ))

        # Check clickbait keywords
        clickbait_words = ["you won't believe", "what happened next", "doctors hate this", "must see"]
        found_clickbait = [w for w in clickbait_words if w in text_lower]
        if found_clickbait:
            score += 30.0
            indicators.append(BiasIndicator(
                bias_type="clickbait_framing",
                detected=True,
                description="Uses clickbait phrasing designed to curiosity-gap readers.",
                evidence_excerpt=found_clickbait[0]
            ))

        # Check absolute claims
        absolute_words = ["always", "never", "100%", "proven cure", "guaranteed", "impossible"]
        found_absolute = [w for w in absolute_words if w in text_lower]
        if found_absolute:
            score += 25.0
            indicators.append(BiasIndicator(
                bias_type="absolute_claims",
                detected=True,
                description="Presents absolute claims without nuance or qualification.",
                evidence_excerpt=", ".join(found_absolute[:2])
            ))

        has_bias = score > 20.0
        summary = "Text exhibits neutral tone with minimal bias indicators." if not has_bias else "Text contains sensational or clickbait framing elements."

        return BiasAnalysisResult(
            has_bias=has_bias,
            sensational_language=bool(found_sensational or has_caps),
            emotional_manipulation=bool(found_sensational),
            clickbait_framing=bool(found_clickbait),
            missing_context=False,
            bias_score=round(min(score, 100.0), 1),
            indicators=indicators,
            summary=summary
        )

bias_detector_agent = BiasDetectorAgent()
