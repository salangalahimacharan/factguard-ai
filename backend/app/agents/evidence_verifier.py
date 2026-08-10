import time
import logging
import re
from typing import List, Dict, Any, Optional
from app.schemas.fact_check import (
    ClaimExtractionItem, SourceMetadata, EvidenceItem, EvidenceAnalysisForClaim
)
from app.utils.llm_client import llm_client

logger = logging.getLogger("factguard.agents.evidence_verifier")

SYSTEM_PROMPT = """You are Agent 3: Evidence Verification Agent for FactGuard AI.
Your task is to analyze retrieved web sources and compare them against an extracted claim.

CRITICAL SEMANTIC EVALUATION RULES:
1. Evaluate the COMPLETE SEMANTIC MEANING of the claim against each retrieved source excerpt.
2. DO NOT classify evidence as "supporting" merely because it contains similar keywords (e.g., "humans", "breathe", "underwater").
3. Classify EVERY evidence item as strictly one of:
   - "supporting": Source directly confirms the claim is true as stated.
   - "contradicting": Source directly refutes, disproves, or asserts the opposite or impossibility of the claim.
     Example: If claim states "Humans can breathe underwater without equipment" and source states "Humans cannot breathe underwater without scuba gear", YOU MUST CLASSIFY IT AS CONTRADICTING.
   - "contextual": Source provides related background but neither confirms nor denies the claim.
4. Assess the evidence strength from 0 to 100 based on direct factual alignment.
5. Return structured JSON.

Expected JSON output format:
{
  "supporting": [],
  "contradicting": [
    {
      "source_id": "SRC-C001-01",
      "evidence_text": "Humans cannot breathe underwater without special equipment like scuba gear because human lungs cannot extract oxygen from water.",
      "evidence_strength": 95.0,
      "reasoning": "Directly refutes the claim by stating equipment is strictly required."
    }
  ],
  "contextual": [],
  "evidence_strength": 95.0,
  "reasoning": "Strong primary evidence refutes the claim."
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

Analyze these sources against the claim and categorize the evidence into supporting, contradicting, or contextual."""

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
                    evidence_strength=float(item.get("evidence_strength", 85.0))
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

        # Heuristic / Post-processing semantic verification audit
        if not supporting and not contradicting and not contextual:
            supporting, contradicting, contextual, overall_strength, overall_reasoning = self._heuristic_verify(claim, sources)
        else:
            # Audit mapped items for false-positive supporting classifications
            supporting, contradicting, contextual = self._audit_semantic_classification(claim, supporting, contradicting, contextual)

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

        claim_lower = claim.claim_text.lower()
        claim_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', claim_lower))

        contradiction_keywords = [
            "cannot", "impossible", "unable", "not possible", "requires", "require",
            "needing", "need", "must use", "apparatus", "equipment", "scuba", "gills",
            "drown", "fatal", "false", "debunk", "myth", "incorrect", "unfounded",
            "no evidence", "contrary", "disproven", "refutes", "never", "denies", "untrue"
        ]

        for s in sources:
            excerpt_lower = s.excerpt.lower()
            snippet_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', excerpt_lower))
            overlap = len(claim_words.intersection(snippet_words)) / max(len(claim_words), 1)

            has_contradiction_signal = any(kw in excerpt_lower for kw in contradiction_keywords)

            # Check specific claim constraint mismatch (e.g. claim says "without equipment" but excerpt says "requires equipment")
            if "without" in claim_lower and any(kw in excerpt_lower for kw in ["require", "need", "must", "scuba", "apparatus", "equipment"]):
                has_contradiction_signal = True

            if has_contradiction_signal and overlap > 0.2:
                contradicting.append(EvidenceItem(
                    evidence_id=f"EV-CON-{claim.claim_id}-{len(contradicting)+1:02d}",
                    claim_id=claim.claim_id,
                    source_id=s.source_id,
                    source_title=s.title,
                    source_url=s.url,
                    publisher=s.publisher,
                    evidence_text=s.excerpt,
                    evidence_type="contradicting",
                    evidence_strength=90.0
                ))
            elif overlap > 0.4 and not has_contradiction_signal:
                supporting.append(EvidenceItem(
                    evidence_id=f"EV-SUP-{claim.claim_id}-{len(supporting)+1:02d}",
                    claim_id=claim.claim_id,
                    source_id=s.source_id,
                    source_title=s.title,
                    source_url=s.url,
                    publisher=s.publisher,
                    evidence_text=s.excerpt,
                    evidence_type="supporting",
                    evidence_strength=80.0
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
        if contradicting and not supporting:
            strength = 90.0
            reasoning = "Retrieved sources explicitly dispute or disprove the claim."
        elif supporting and not contradicting:
            strength = 85.0
            reasoning = "Retrieved sources contain matching details supporting the claim."
        elif supporting and contradicting:
            strength = 50.0
            reasoning = "Sources provide conflicting evidence regarding this claim."
        else:
            strength = 30.0
            reasoning = "Sources provide background context but do not directly confirm or deny the claim."

        return supporting, contradicting, contextual, strength, reasoning

    def _audit_semantic_classification(
        self,
        claim: ClaimExtractionItem,
        supporting: List[EvidenceItem],
        contradicting: List[EvidenceItem],
        contextual: List[EvidenceItem]
    ):
        """Post-classification audit to move false-positive supporting items to contradicting if semantic contradiction is present."""
        claim_lower = claim.claim_text.lower()
        contradiction_keywords = [
            "cannot", "impossible", "unable", "not possible", "requires", "require",
            "needing", "need", "must use", "apparatus", "equipment", "scuba", "gills",
            "drown", "fatal", "false", "debunk", "myth", "incorrect", "unfounded"
        ]

        verified_supporting = []
        for item in supporting:
            txt = item.evidence_text.lower()
            # If item contains explicit contradiction signals
            if any(kw in txt for kw in contradiction_keywords) or ("without" in claim_lower and any(k in txt for k in ["scuba", "apparatus", "equipment", "require"])):
                item.evidence_type = "contradicting"
                item.evidence_strength = 90.0
                contradicting.append(item)
            else:
                verified_supporting.append(item)

        return verified_supporting, contradicting, contextual

evidence_verifier_agent = EvidenceVerifierAgent()
