import time
import logging
from typing import List
from app.schemas.fact_check import ClaimExtractionItem, SourceMetadata, EvidenceAnalysisForClaim, ConsistencyCheckResult
from app.utils.llm_client import llm_client

logger = logging.getLogger("factguard.agents.consistency_checker")

class ConsistencyCheckerAgent:
    """Agent 6: Cross-Source Consistency Agent evaluating agreement and independence across independent publishers."""

    async def run(
        self,
        claim: ClaimExtractionItem,
        sources: List[SourceMetadata],
        evidence: EvidenceAnalysisForClaim
    ) -> ConsistencyCheckResult:
        start_time = time.time()
        logger.info(f"Agent 6 [Consistency Checker] analyzing cross-source consistency for claim {claim.claim_id}...")

        if not sources:
            return ConsistencyCheckResult(
                claim_id=claim.claim_id,
                sources_agree=False,
                sources_contradict=False,
                repeating_single_source=False,
                independent_sources_count=0,
                consistency_score=0.0,
                findings="No external sources available to evaluate cross-source consistency."
            )

        # Count independent domains
        unique_publishers = set(s.publisher.lower() for s in sources if s.publisher)
        independent_count = len(unique_publishers)

        num_supporting = len(evidence.supporting_evidence)
        num_contradicting = len(evidence.contradicting_evidence)

        sources_agree = num_supporting > 1 and num_contradicting == 0
        sources_contradict = num_supporting > 0 and num_contradicting > 0
        repeating_single_source = independent_count == 1 and len(sources) > 1

        # Compute consistency score
        if sources_agree:
            score = min(70.0 + (independent_count * 10.0), 95.0)
            findings = f"Multiple independent sources ({independent_count} publishers) consistently support this claim."
        elif sources_contradict:
            score = 30.0
            findings = f"Significant disagreement detected between retrieved sources ({num_supporting} supporting vs {num_contradicting} contradicting)."
        elif num_contradicting > 0 and num_supporting == 0:
            score = 85.0 # High consistency in refuting the claim
            findings = f"Independent sources consistently dispute or debunk this claim."
        elif repeating_single_source:
            score = 50.0
            findings = "Multiple entries trace back to a single primary source without independent confirmation."
        else:
            score = 45.0
            findings = "Limited source overlap; additional independent confirmation recommended."

        elapsed = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Agent 6 [Consistency Checker] completed in {elapsed}ms. Consistency Score={score}")
        return ConsistencyCheckResult(
            claim_id=claim.claim_id,
            sources_agree=sources_agree,
            sources_contradict=sources_contradict,
            repeating_single_source=repeating_single_source,
            independent_sources_count=independent_count,
            consistency_score=round(score, 1),
            findings=findings
        )

consistency_checker_agent = ConsistencyCheckerAgent()
