import time
import logging
from typing import List, Dict, Any, Optional
from app.schemas.fact_check import (
    ClaimExtractionItem, SourceMetadata, EvidenceAnalysisForClaim,
    BiasAnalysisResult, ConsistencyCheckResult, VerdictType, ClaimVerdict
)
from app.utils.llm_client import llm_client

logger = logging.getLogger("factguard.agents.final_judge")

SYSTEM_PROMPT = """You are Agent 7: Final Judge Agent for FactGuard AI.
Your responsibility is to synthesize all findings from prior specialized agents and issue a transparent, evidence-backed verdict.

VERDICT RULES:
- VERIFIED: Strong, reliable, high-credibility evidence directly supports the claim with no meaningful contradiction.
- FALSE: High-credibility reliable evidence clearly disproves or contradicts the claim.
- MISLEADING: The statement has a kernel of truth but omits vital context, exaggerates details, or uses deceptive framing.
- PARTIALLY TRUE: Part of the claim is accurate while another part is inaccurate.
- UNCERTAIN: Available evidence is conflicting, insufficient, irrelevant, or inconclusive.
- INSUFFICIENT EVIDENCE: The gathered sources are inadequate or missing.

CRITICAL RULES:
1. If evidence directly refutes or disproves the claim (e.g. claim says "humans can breathe underwater without equipment", evidence says "humans cannot breathe underwater without scuba apparatus"), THE VERDICT MUST BE "FALSE". NEVER RETURN VERIFIED WHEN CONTRADICTING EVIDENCE IS PRESENT.
2. If evidence is conflicting or inadequate, output "UNCERTAIN" or "INSUFFICIENT EVIDENCE".
3. Return structured JSON.

Expected JSON output format:
{
  "overall_verdict": "FALSE",
  "confidence_score": 90.0,
  "summary": "Scientific evidence confirms humans cannot breathe underwater without specialized breathing equipment.",
  "key_context": "Human lungs lack gills and cannot extract oxygen directly from water.",
  "limitations": "Analysis based on established biological facts and public scientific literature.",
  "claim_verdicts": [
    {
      "claim_id": "C001",
      "verdict": "FALSE",
      "confidence_score": 90.0,
      "explanation": "Scientific literature disproves the claim by confirming humans require artificial apparatus to breathe underwater."
    }
  ]
}
"""

class FinalJudgeAgent:
    """Agent 7: The Orchestration Final Judge synthesizing all evidence, credibility, and bias reports into transparent verdicts with Step 8 Validation."""

    async def run(
        self,
        original_input: str,
        claims: List[ClaimExtractionItem],
        claim_sources: Dict[str, List[SourceMetadata]],
        claim_evidence: Dict[str, EvidenceAnalysisForClaim],
        claim_consistency: Dict[str, ConsistencyCheckResult],
        bias_analysis: BiasAnalysisResult
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Agent 7 [Final Judge] synthesizing final verdict for {len(claims)} claims...")

        synthesis_input = []
        for claim in claims:
            cid = claim.claim_id
            sources = claim_sources.get(cid, [])
            ev = claim_evidence.get(cid)
            cons = claim_consistency.get(cid)

            synthesis_input.append({
                "claim_id": cid,
                "claim_text": claim.claim_text,
                "sources_count": len(sources),
                "high_credibility_sources": [s.publisher for s in sources if s.credibility_score >= 70.0],
                "supporting_evidence_count": len(ev.supporting_evidence) if ev else 0,
                "contradicting_evidence_count": len(ev.contradicting_evidence) if ev else 0,
                "contradicting_excerpts": [item.evidence_text for item in ev.contradicting_evidence] if ev else [],
                "evidence_strength": ev.evidence_strength if ev else 0.0,
                "evidence_reasoning": ev.reasoning if ev else "",
                "cross_source_consistency_score": cons.consistency_score if cons else 0.0,
                "cross_source_findings": cons.findings if cons else ""
            })

        prompt = f"""Original Input: "{original_input}"
Bias Analysis Summary: {bias_analysis.summary} (Bias Score: {bias_analysis.bias_score})

Claims Evidence Breakdown:
{synthesis_input}

Synthesize these findings and produce the final verdicts."""

        llm_res = await llm_client.generate_json(prompt, SYSTEM_PROMPT)

        claim_verdicts: List[ClaimVerdict] = []

        if llm_res and "claim_verdicts" in llm_res and isinstance(llm_res["claim_verdicts"], list):
            for cv in llm_res["claim_verdicts"]:
                cid = cv.get("claim_id")
                matching_claim = next((c for c in claims if c.claim_id == cid), claims[0] if claims else None)
                if not matching_claim:
                    continue

                sources = claim_sources.get(cid, [])
                ev = claim_evidence.get(cid)
                cons = claim_consistency.get(cid)

                v_str = cv.get("verdict", "UNCERTAIN").upper()
                verdict_enum = self._parse_verdict(v_str)

                claim_verdicts.append(ClaimVerdict(
                    claim_id=cid,
                    claim_text=matching_claim.claim_text,
                    verdict=verdict_enum,
                    confidence_score=float(cv.get("confidence_score", 70.0)),
                    explanation=cv.get("explanation", "Verdict based on evidence evaluation."),
                    supporting_sources_count=len(ev.supporting_evidence) if ev else 0,
                    contradicting_sources_count=len(ev.contradicting_evidence) if ev else 0,
                    sources=sources,
                    evidence_breakdown=ev,
                    consistency=cons
                ))

        # Heuristic fallback if LLM is unavailable
        if not claim_verdicts:
            claim_verdicts = self._heuristic_judge_claims(claims, claim_sources, claim_evidence, claim_consistency, bias_analysis)

        # -------------------------------------------------------------
        # STEP 8: VERDICT VALIDATION AUDIT (Prevents Logically Flawed Verdicts)
        # -------------------------------------------------------------
        claim_verdicts = self._validate_and_finalize_verdicts(claim_verdicts, bias_analysis)

        # Determine overall verdict
        overall_verdict, overall_confidence, overall_summary = self._compute_overall_verdict(claim_verdicts, bias_analysis)

        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Agent 7 [Final Judge] finalized overall verdict '{overall_verdict}' in {elapsed}ms.")

        return {
            "overall_verdict": overall_verdict,
            "confidence_score": overall_confidence,
            "summary": llm_res.get("summary") if llm_res and llm_res.get("summary") else overall_summary,
            "key_context": llm_res.get("key_context") if llm_res else "Analysis synthesizes evidence from public web research and cross-source verification.",
            "limitations": llm_res.get("limitations") if llm_res else "Automated agent analysis based on current available search indices.",
            "claim_verdicts": claim_verdicts
        }

    def _validate_and_finalize_verdicts(
        self,
        claim_verdicts: List[ClaimVerdict],
        bias_analysis: BiasAnalysisResult
    ) -> List[ClaimVerdict]:
        """
        Step 8: Final Verdict Validation Step
        Audits every claim verdict against evidence to ensure strict logical consistency.
        """
        validated = []
        for cv in claim_verdicts:
            ev = cv.evidence_breakdown
            num_sup = len(ev.supporting_evidence) if ev else 0
            num_con = len(ev.contradicting_evidence) if ev else 0
            sources = cv.sources

            # Rule 1: Strong contradicting evidence + no meaningful support -> MUST BE FALSE
            if num_con > 0 and num_sup == 0:
                cv.verdict = VerdictType.FALSE
                publisher_name = ev.contradicting_evidence[0].publisher if ev and ev.contradicting_evidence else "web research"
                cv.explanation = f"Retrieved reliable evidence ({publisher_name}) explicitly contradicts the claim."
            # Rule 2: Strong supporting evidence + no contradiction -> VERIFIED
            elif num_sup > 0 and num_con == 0:
                if bias_analysis.has_bias and bias_analysis.missing_context:
                    cv.verdict = VerdictType.MISLEADING
                else:
                    cv.verdict = VerdictType.VERIFIED
            # Rule 3: Conflicting evidence on both sides -> UNCERTAIN
            elif num_sup > 0 and num_con > 0:
                cv.verdict = VerdictType.UNCERTAIN
                cv.explanation = f"Conflicting evidence detected across retrieved sources ({num_sup} supporting vs {num_con} contradicting)."
            # Rule 4: Insufficient or irrelevant evidence -> UNCERTAIN / INSUFFICIENT EVIDENCE
            elif num_sup == 0 and num_con == 0:
                cv.verdict = VerdictType.UNCERTAIN
                cv.explanation = "Insufficient or irrelevant reliable evidence could be retrieved to confirm or deny this claim."

            # Calculate dynamic confidence (Requirement 7)
            cv.confidence_score = self._calculate_dynamic_confidence(ev, sources, cv.consistency, cv.verdict)
            validated.append(cv)

        return validated

    def _calculate_dynamic_confidence(
        self,
        ev: Optional[EvidenceAnalysisForClaim],
        sources: List[SourceMetadata],
        cons: Optional[ConsistencyCheckResult],
        verdict: VerdictType
    ) -> float:
        """Requirement 7: Calculates dynamic confidence score from evidence strength, credibility, and consistency."""
        if not sources or not ev:
            return 50.0

        high_cred_sources = [s for s in sources if s.credibility_score >= 70.0]
        avg_cred = sum(s.credibility_score for s in sources) / len(sources) if sources else 50.0

        if verdict == VerdictType.FALSE:
            con_strengths = [item.evidence_strength for item in ev.contradicting_evidence]
            avg_con_strength = sum(con_strengths) / len(con_strengths) if con_strengths else 85.0
            confidence = 0.4 * avg_con_strength + 0.4 * avg_cred + 0.2 * (min(len(high_cred_sources), 3) * 10)
        elif verdict == VerdictType.VERIFIED:
            sup_strengths = [item.evidence_strength for item in ev.supporting_evidence]
            avg_sup_strength = sum(sup_strengths) / len(sup_strengths) if sup_strengths else 80.0
            cons_score = cons.consistency_score if cons else 50.0
            confidence = 0.4 * avg_sup_strength + 0.3 * avg_cred + 0.3 * cons_score
        elif verdict in (VerdictType.UNCERTAIN, VerdictType.INSUFFICIENT_EVIDENCE, VerdictType.UNVERIFIED):
            confidence = 50.0 + (min(len(sources), 2) * 5.0)
        else:
            confidence = 70.0

        return round(max(35.0, min(confidence, 98.0)), 1)

    def _parse_verdict(self, v_str: str) -> VerdictType:
        if "VERIFIED" in v_str or "TRUE" == v_str:
            return VerdictType.VERIFIED
        elif "FALSE" in v_str:
            return VerdictType.FALSE
        elif "MISLEADING" in v_str:
            return VerdictType.MISLEADING
        elif "PARTIALLY" in v_str:
            return VerdictType.PARTIALLY_TRUE
        elif "UNCERTAIN" in v_str:
            return VerdictType.UNCERTAIN
        elif "UNVERIFIED" in v_str:
            return VerdictType.UNVERIFIED
        else:
            return VerdictType.INSUFFICIENT_EVIDENCE

    def _heuristic_judge_claims(
        self,
        claims: List[ClaimExtractionItem],
        claim_sources: Dict[str, List[SourceMetadata]],
        claim_evidence: Dict[str, EvidenceAnalysisForClaim],
        claim_consistency: Dict[str, ConsistencyCheckResult],
        bias_analysis: BiasAnalysisResult
    ) -> List[ClaimVerdict]:
        results = []

        for claim in claims:
            cid = claim.claim_id
            sources = claim_sources.get(cid, [])
            ev = claim_evidence.get(cid)
            cons = claim_consistency.get(cid)

            num_sup = len(ev.supporting_evidence) if ev else 0
            num_con = len(ev.contradicting_evidence) if ev else 0

            if num_con > 0 and num_sup == 0:
                verdict = VerdictType.FALSE
                explanation = "Retrieved high-credibility evidence explicitly refutes or disproves this claim."
            elif num_sup > 0 and num_con == 0:
                verdict = VerdictType.VERIFIED
                explanation = "Retrieved reliable sources and primary reporting confirm the claim."
            elif num_sup > 0 and num_con > 0:
                verdict = VerdictType.UNCERTAIN
                explanation = "Conflicting evidence exists across retrieved sources."
            else:
                verdict = VerdictType.UNCERTAIN
                explanation = "Insufficient or irrelevant evidence could be retrieved."

            confidence = self._calculate_dynamic_confidence(ev, sources, cons, verdict)

            results.append(ClaimVerdict(
                claim_id=cid,
                claim_text=claim.claim_text,
                verdict=verdict,
                confidence_score=confidence,
                explanation=explanation,
                supporting_sources_count=num_sup,
                contradicting_sources_count=num_con,
                sources=sources,
                evidence_breakdown=ev,
                consistency=cons
            ))

        return results

    def _compute_overall_verdict(
        self,
        claim_verdicts: List[ClaimVerdict],
        bias_analysis: BiasAnalysisResult
    ) -> tuple[VerdictType, float, str]:
        if not claim_verdicts:
            return VerdictType.UNCERTAIN, 50.0, "No claims extracted for analysis."

        verdicts = [cv.verdict for cv in claim_verdicts]
        confidences = [cv.confidence_score for cv in claim_verdicts]
        avg_confidence = round(sum(confidences) / len(confidences), 1)

        if all(v == VerdictType.VERIFIED for v in verdicts):
            overall = VerdictType.VERIFIED
            summary = "All extracted claims were verified against reliable external evidence sources."
        elif any(v == VerdictType.FALSE for v in verdicts):
            overall = VerdictType.FALSE
            summary = "The claim is contradicted and disproven by credible external evidence."
        elif any(v == VerdictType.UNCERTAIN for v in verdicts):
            overall = VerdictType.UNCERTAIN
            summary = "Evidence for the claim is conflicting, insufficient, or inconclusive."
        elif any(v == VerdictType.MISLEADING for v in verdicts):
            overall = VerdictType.MISLEADING
            summary = "The content presents factual elements in a misleading context."
        else:
            overall = VerdictType.UNCERTAIN
            summary = "Evidence is inconclusive at this time."

        return overall, avg_confidence, summary

final_judge_agent = FinalJudgeAgent()
