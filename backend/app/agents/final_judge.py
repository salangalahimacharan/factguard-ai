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

VERDICT GUIDELINES:
- VERIFIED: Strong, reliable, high-credibility evidence directly supports the claim.
- FALSE: High-credibility reliable evidence clearly disproves or contradicts the claim.
- MISLEADING: The statement has a kernel of truth but omits vital context, exaggerates details, or uses deceptive framing.
- PARTIALLY TRUE: Part of the claim is accurate while another part is inaccurate or unverified.
- UNVERIFIED: No reliable web evidence could be retrieved to confirm or deny the claim.
- INSUFFICIENT EVIDENCE: The gathered sources are inadequate, low-credibility, vague, or mutually contradictory.

CRITICAL RULES:
1. Never fabricate or invent citations, URLs, or evidence.
2. If evidence is inadequate or missing, strictly output "INSUFFICIENT EVIDENCE" or "UNVERIFIED". Do not force a True/False verdict!
3. Provide a concise, user-readable explanation referencing specific evidence.
4. Return structured JSON.

Expected JSON output format:
{
  "overall_verdict": "VERIFIED",
  "confidence_score": 88.0,
  "summary": "The claim is supported by official announcements and reputable news reporting.",
  "key_context": "The announcement occurred during the annual technical keynote.",
  "limitations": "Analysis based on public web sources available as of current date.",
  "claim_verdicts": [
    {
      "claim_id": "C001",
      "verdict": "VERIFIED",
      "confidence_score": 90.0,
      "explanation": "Primary press releases confirm the model launch in Jan 2026."
    }
  ]
}
"""

class FinalJudgeAgent:
    """Agent 7: The Orchestration Final Judge synthesizing all evidence, credibility, and bias reports into transparent verdicts."""

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

        # Build comprehensive synthesis context for LLM
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

                v_str = cv.get("verdict", "INSUFFICIENT EVIDENCE").upper()
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

    def _parse_verdict(self, v_str: str) -> VerdictType:
        if "VERIFIED" in v_str or "TRUE" == v_str:
            return VerdictType.VERIFIED
        elif "FALSE" in v_str:
            return VerdictType.FALSE
        elif "MISLEADING" in v_str:
            return VerdictType.MISLEADING
        elif "PARTIALLY" in v_str:
            return VerdictType.PARTIALLY_TRUE
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
            ev_strength = ev.evidence_strength if ev else 0.0

            high_cred_sources = [s for s in sources if s.credibility_score >= 70.0]

            if not sources or ev_strength < 20.0 or (num_sup == 0 and num_con == 0 and not high_cred_sources):
                verdict = VerdictType.INSUFFICIENT_EVIDENCE
                confidence = 85.0
                explanation = "Insufficient reliable online evidence could be retrieved to verify or disprove this claim."
            elif num_con > 0 and num_sup == 0:
                verdict = VerdictType.FALSE
                confidence = min(70.0 + (len(high_cred_sources) * 10.0), 95.0)
                explanation = "Retrieved high-credibility sources explicitly disprove or refute this claim."
            elif num_sup > 0 and num_con == 0 and len(high_cred_sources) > 0:
                if bias_analysis.has_bias and bias_analysis.missing_context:
                    verdict = VerdictType.MISLEADING
                    confidence = 80.0
                    explanation = "The core statement has factual basis, but the surrounding post presents it in a misleading manner with missing context."
                else:
                    verdict = VerdictType.VERIFIED
                    confidence = min(75.0 + (len(high_cred_sources) * 8.0), 95.0)
                    explanation = "Retrieved reliable sources and primary reporting confirm the claim."
            elif num_sup > 0 and num_con > 0:
                verdict = VerdictType.PARTIALLY_TRUE
                confidence = 70.0
                explanation = "Sources provide conflicting information; parts of the statement are supported while other parts are challenged."
            elif (bias_analysis.clickbait_framing or bias_analysis.sensational_language) and num_sup > 0:
                verdict = VerdictType.MISLEADING
                confidence = 75.0
                explanation = "The claim uses sensationalized framing or clickbait language that exaggerates the underlying facts."
            else:
                verdict = VerdictType.UNVERIFIED
                confidence = 60.0
                explanation = "Available evidence provides background context but does not conclusively verify the claim."

            results.append(ClaimVerdict(
                claim_id=cid,
                claim_text=claim.claim_text,
                verdict=verdict,
                confidence_score=round(confidence, 1),
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
            return VerdictType.INSUFFICIENT_EVIDENCE, 90.0, "No claims extracted for analysis."

        verdicts = [cv.verdict for cv in claim_verdicts]
        confidences = [cv.confidence_score for cv in claim_verdicts]
        avg_confidence = round(sum(confidences) / len(confidences), 1)

        if all(v == VerdictType.VERIFIED for v in verdicts):
            overall = VerdictType.VERIFIED
            summary = "All extracted claims were verified against reliable external evidence sources."
        elif any(v == VerdictType.FALSE for v in verdicts):
            if any(v == VerdictType.VERIFIED for v in verdicts):
                overall = VerdictType.PARTIALLY_TRUE
                summary = "The submission contains a mixture of verified facts and false statements."
            else:
                overall = VerdictType.FALSE
                summary = "The primary claim is contradicted by credible external sources."
        elif any(v == VerdictType.MISLEADING for v in verdicts):
            overall = VerdictType.MISLEADING
            summary = "The content presents factual elements in a misleading or sensationalized context."
        elif any(v == VerdictType.PARTIALLY_TRUE for v in verdicts):
            overall = VerdictType.PARTIALLY_TRUE
            summary = "The claim is partially accurate but incomplete."
        elif all(v in (VerdictType.INSUFFICIENT_EVIDENCE, VerdictType.UNVERIFIED) for v in verdicts):
            overall = VerdictType.INSUFFICIENT_EVIDENCE
            summary = "Insufficient reliable online evidence was found to confirm or deny the claim."
        else:
            overall = VerdictType.UNVERIFIED
            summary = "Evidence is inconclusive at this time."

        return overall, avg_confidence, summary

final_judge_agent = FinalJudgeAgent()
