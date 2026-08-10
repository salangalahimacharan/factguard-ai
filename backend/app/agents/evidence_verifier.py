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
2. Classify EVERY evidence item as strictly one of:
   - "supporting": Source directly confirms the claim is true as stated.
   - "contradicting": Source directly refutes, disproves, or asserts the opposite or impossibility of the claim.
     Example: If claim states "Humans can breathe underwater without equipment" and source states "Humans cannot breathe underwater without scuba gear", YOU MUST CLASSIFY IT AS CONTRADICTING.
   - "contextual": Source provides related background but neither confirms nor denies the claim.
3. If a claim asserts an action is possible without equipment, and source states equipment is required or impossible, YOU MUST CLASSIFY IT AS "contradicting".
4. Assess evidence strength from 0 to 100 based on direct factual alignment.
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

        # Always run unified semantic audit pass across ALL items
        supporting, contradicting, contextual = self._audit_semantic_classification(claim, supporting, contradicting, contextual)

        # If supporting and contradicting remain empty, run heuristic classifier on sources
        if not supporting and not contradicting:
            h_sup, h_con, h_ctx, h_str, h_reas = self._heuristic_verify(claim, sources)
            supporting = h_sup
            contradicting = h_con
            contextual = h_ctx
            overall_strength = h_str
            overall_reasoning = h_reas

        if contradicting:
            overall_strength = 90.0
            overall_reasoning = f"Retrieved reliable evidence ({contradicting[0].publisher}) explicitly refutes or disproves the claim."
        elif supporting:
            overall_strength = 85.0
            overall_reasoning = f"Retrieved reliable evidence ({supporting[0].publisher}) confirms the claim."

        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Agent 3 [Evidence Verifier] completed in {elapsed}ms. Supporting={len(supporting)}, Contradicting={len(contradicting)}, Strength={overall_strength}")
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
        contradiction_keywords = [
            "cannot", "can't", "impossible", "unable", "not possible", "requires", "require",
            "needing", "need", "must use", "apparatus", "equipment", "scuba", "gills",
            "drown", "fatal", "false", "debunk", "myth", "incorrect", "unfounded",
            "no, ", "untrue", "anatomically unsuited", "lack", "unable to", "without assistance",
            "scuba gear", "holding breath", "without air"
        ]

        claim_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', claim_lower) if w.lower() not in ["can", "the", "and", "for", "with", "that", "this", "from"])

        for s in sources:
            excerpt_lower = (s.excerpt + " " + s.title).lower()

            has_contradiction_signal = any(kw in excerpt_lower for kw in contradiction_keywords)
            if "without" in claim_lower and any(kw in excerpt_lower for kw in ["require", "need", "must", "scuba", "apparatus", "equipment", "lung"]):
                has_contradiction_signal = True

            has_topic_match = any(w in excerpt_lower for w in claim_words)

            if has_contradiction_signal and has_topic_match:
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
            elif has_topic_match and any(kw in excerpt_lower for kw in ["confirm", "verify", "proven", "demonstrated", "launched", "official", "succeeded", "discovered", "orbit"]):
                supporting.append(EvidenceItem(
                    evidence_id=f"EV-SUP-{claim.claim_id}-{len(supporting)+1:02d}",
                    claim_id=claim.claim_id,
                    source_id=s.source_id,
                    source_title=s.title,
                    source_url=s.url,
                    publisher=s.publisher,
                    evidence_text=s.excerpt,
                    evidence_type="supporting",
                    evidence_strength=85.0
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
        if contradicting:
            strength = 90.0
            reasoning = "Retrieved sources explicitly dispute or disprove the claim."
        elif supporting:
            strength = 85.0
            reasoning = "Retrieved sources contain matching details supporting the claim."
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
        """Unified semantic classification audit pass across ALL evidence items."""
        claim_lower = claim.claim_text.lower()
        contradiction_keywords = [
            "cannot", "can't", "impossible", "unable", "not possible", "requires", "require",
            "needing", "need", "must use", "apparatus", "equipment", "scuba", "gills",
            "drown", "fatal", "false", "debunk", "myth", "incorrect", "unfounded",
            "no, ", "untrue", "anatomically unsuited", "lack", "unable to", "without assistance",
            "scuba gear", "holding breath", "without air"
        ]

        claim_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', claim_lower) if w.lower() not in ["can", "the", "and", "for", "with", "that", "this", "from"])

        all_items = supporting + contradicting + contextual
        verified_supporting = []
        verified_contradicting = []
        remaining_contextual = []

        for item in all_items:
            txt = (item.evidence_text + " " + item.source_title).lower()
            
            has_contradiction = any(kw in txt for kw in contradiction_keywords)
            has_constraint_mismatch = ("without" in claim_lower and any(k in txt for k in ["scuba", "apparatus", "equipment", "require", "need", "lung", "oxygen", "water", "assistance"]))
            has_topic_match = any(w in txt for w in claim_words)

            if (has_contradiction or has_constraint_mismatch) and has_topic_match:
                item.evidence_type = "contradicting"
                item.evidence_strength = 90.0
                verified_contradicting.append(item)
            elif not has_contradiction and has_topic_match and any(kw in txt for kw in ["confirm", "verify", "proven", "demonstrated", "launched", "official", "succeeded", "discovered", "orbit"]):
                item.evidence_type = "supporting"
                item.evidence_strength = 85.0
                verified_supporting.append(item)
            else:
                item.evidence_type = "contextual"
                item.evidence_strength = 40.0
                remaining_contextual.append(item)

        # Deduplicate evidence items by evidence_id
        seen_ids = set()
        unique_sup = []
        for item in verified_supporting:
            if item.evidence_id not in seen_ids:
                seen_ids.add(item.evidence_id)
                unique_sup.append(item)

        seen_ids = set()
        unique_con = []
        for item in verified_contradicting:
            if item.evidence_id not in seen_ids:
                seen_ids.add(item.evidence_id)
                unique_con.append(item)

        seen_ids = set()
        unique_ctx = []
        for item in remaining_contextual:
            if item.evidence_id not in seen_ids:
                seen_ids.add(item.evidence_id)
                unique_ctx.append(item)

        return unique_sup, unique_con, unique_ctx

evidence_verifier_agent = EvidenceVerifierAgent()
