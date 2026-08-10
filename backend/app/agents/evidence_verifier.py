import time
import logging
from typing import List, Dict, Any
from app.schemas.fact_check import (
    ClaimExtractionItem, SourceMetadata, EvidenceItem, EvidenceAnalysisForClaim
)
from app.utils.llm_client import llm_client

logger = logging.getLogger("factguard.agents.evidence_verifier")

SYSTEM_PROMPT = """You are Agent 3: Evidence Verification Agent for FactGuard AI.
Your task is to analyze retrieved web sources and compare them against an extracted claim.

RULES:
1. Compare the exact statement in the claim against source excerpts.
2. Separate evidence into:
   - "supporting": Source directly confirms the claim.
   - "contradicting": Source directly refutes or disproves the claim.
   - "contextual": Source provides partial context, background, or related information.
3. Assess the evidence strength from 0 to 100 based on direct alignment and facts provided.
4. Detect if the information is outdated or out of context.
5. Do not treat snippets alone as proof if they don't directly address the claim.
6. Return structured JSON.

Expected JSON output format:
{
  "supporting": [
    {
      "source_id": "SRC-C001-01",
      "evidence_text": "Company X officially unveiled the new AI model during its keynote in Jan 2026.",
      "evidence_strength": 90.0,
      "reasoning": "Direct confirmation of launch date and entity."
    }
  ],
  "contradicting": [],
  "contextual": [],
  "evidence_strength": 85.0,
  "reasoning": "Strong primary evidence confirms the model launch."
}
"""

class EvidenceVerifierAgent:
    """Agent 3: Evaluates retrieved sources against claims to categorize supporting, contradicting, and contextual evidence."""

    async def run(self, claim: ClaimExtractionItem, sources: List[SourceMetadata]) -> EvidenceAnalysisForClaim:
        start_time = time.time()
        logger.info(f"Agent 3 [Evidence Verifier] starting evaluation for claim {claim.claim_id} across {len(sources)} sources...")

        if not sources:
            return EvidenceAnalysisForClaim(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                supporting_evidence=[],
                contradicting_evidence=[],
                contextual_evidence=[],
                evidence_strength=0.0,
                reasoning="No online sources or evidence could be retrieved for this claim."
            )

        # Prepare source payload for LLM analysis
        source_inputs = []
        for s in sources:
            source_inputs.append({
                "source_id": s.source_id,
                "title": s.title,
                "publisher": s.publisher,
                "url": s.url,
                "excerpt": s.excerpt
            })

        prompt = f"""Claim ID: {claim.claim_id}
Claim Text: "{claim.claim_text}"

Retrieved Sources:
{source_inputs}

Analyze these sources against the claim and categorize the evidence."""

        llm_res = await llm_client.generate_json(prompt, SYSTEM_PROMPT)

        supporting: List[EvidenceItem] = []
        contradicting: List[EvidenceItem] = []
        contextual: List[EvidenceItem] = []
        overall_strength = 50.0
        overall_reasoning = "Evidence evaluated across retrieved web sources."

        if llm_res and "evidence_strength" in llm_res:
            overall_strength = float(llm_res.get("evidence_strength", 50.0))
            overall_reasoning = llm_res.get("reasoning", overall_reasoning)

            # Map supporting
            for idx, item in enumerate(llm_res.get("supporting", [])):
                src = self._find_source(item.get("source_id"), sources)
                supporting.append(EvidenceItem(
                    evidence_id=f"EV-SUP-{claim.claim_id}-{idx+1:02d}",
                    claim_id=claim.claim_id,
                    source_id=src.source_id if src else "unknown",
                    source_title=src.title if src else "Retrieved Web Source",
                    source_url=src.url if src else "#",
                    publisher=src.publisher if src else "Web Publisher",
                    evidence_text=item.get("evidence_text", src.excerpt if src else ""),
                    evidence_type="supporting",
                    evidence_strength=float(item.get("evidence_strength", 80.0))
                ))

            # Map contradicting
            for idx, item in enumerate(llm_res.get("contradicting", [])):
                src = self._find_source(item.get("source_id"), sources)
                contradicting.append(EvidenceItem(
                    evidence_id=f"EV-CON-{claim.claim_id}-{idx+1:02d}",
                    claim_id=claim.claim_id,
                    source_id=src.source_id if src else "unknown",
                    source_title=src.title if src else "Retrieved Web Source",
                    source_url=src.url if src else "#",
                    publisher=src.publisher if src else "Web Publisher",
                    evidence_text=item.get("evidence_text", src.excerpt if src else ""),
                    evidence_type="contradicting",
                    evidence_strength=float(item.get("evidence_strength", 80.0))
                ))

            # Map contextual
            for idx, item in enumerate(llm_res.get("contextual", [])):
                src = self._find_source(item.get("source_id"), sources)
                contextual.append(EvidenceItem(
                    evidence_id=f"EV-CTX-{claim.claim_id}-{idx+1:02d}",
                    claim_id=claim.claim_id,
                    source_id=src.source_id if src else "unknown",
                    source_title=src.title if src else "Retrieved Web Source",
                    source_url=src.url if src else "#",
                    publisher=src.publisher if src else "Web Publisher",
                    evidence_text=item.get("evidence_text", src.excerpt if src else ""),
                    evidence_type="contextual",
                    evidence_strength=float(item.get("evidence_strength", 50.0))
                ))

        # Heuristic fallback if LLM returned empty breakdown
        if not supporting and not contradicting and not contextual:
            supporting, contradicting, contextual, overall_strength, overall_reasoning = self._heuristic_verify(claim, sources)

        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Agent 3 [Evidence Verifier] completed in {elapsed}ms. Strength={overall_strength}")
        return EvidenceAnalysisForClaim(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            contextual_evidence=contextual,
            evidence_strength=overall_strength,
            reasoning=overall_reasoning
        )

    def _find_source(self, source_id: Optional[str], sources: List[SourceMetadata]) -> Optional[SourceMetadata]:
        if not source_id:
            return sources[0] if sources else None
        for s in sources:
            if s.source_id == source_id:
                return s
        return sources[0] if sources else None

    def _heuristic_verify(self, claim: ClaimExtractionItem, sources: List[SourceMetadata]):
        supporting = []
        contradicting = []
        contextual = []

        claim_words = set(w.lower() for w in claim.claim_text.split() if len(w) > 3)

        for s in sources:
            snippet_words = set(w.lower() for w in s.excerpt.split() if len(w) > 3)
            overlap = len(claim_words.intersection(snippet_words)) / max(len(claim_words), 1)

            # Check for negation words
            negations = ["false", "debunk", "fake", "incorrect", "denies", "myth", "misleading", "no evidence", "unfounded"]
            has_negation = any(neg in s.excerpt.lower() for neg in negations)

            if has_negation and overlap > 0.2:
                contradicting.append(EvidenceItem(
                    evidence_id=f"EV-CON-{claim.claim_id}-{len(contradicting)+1:02d}",
                    claim_id=claim.claim_id,
                    source_id=s.source_id,
                    source_title=s.title,
                    source_url=s.url,
                    publisher=s.publisher,
                    evidence_text=s.excerpt,
                    evidence_type="contradicting",
                    evidence_strength=75.0
                ))
            elif overlap > 0.4:
                supporting.append(EvidenceItem(
                    evidence_id=f"EV-SUP-{claim.claim_id}-{len(supporting)+1:02d}",
                    claim_id=claim.claim_id,
                    source_id=s.source_id,
                    source_title=s.title,
                    source_url=s.url,
                    publisher=s.publisher,
                    evidence_text=s.excerpt,
                    evidence_type="supporting",
                    evidence_strength=70.0
                ))
            else:
                contextual.append(EvidenceItem(
                    evidence_id=f"EV-CTX-{claim.claim_id}-{len(contextual)+1:02d}",
                    claim_id=claim.claim_id,
                    source_id=s.source_id,
                    source_title=s.title,
                    source_url=s.url,
                    publisher=s.publisher,
                    evidence_text=s.excerpt,
                    evidence_type="contextual",
                    evidence_strength=40.0
                ))

        strength = 50.0
        if supporting and not contradicting:
            strength = 80.0
            reasoning = "Retrieved sources contain matching details supporting the claim."
        elif contradicting and not supporting:
            strength = 15.0
            reasoning = "Retrieved sources explicitly dispute or debunk the claim."
        elif supporting and contradicting:
            strength = 45.0
            reasoning = "Sources provide conflicting information regarding this claim."
        else:
            strength = 30.0
            reasoning = "Sources provide background context but do not directly confirm or deny the claim."

        return supporting, contradicting, contextual, strength, reasoning

evidence_verifier_agent = EvidenceVerifierAgent()
