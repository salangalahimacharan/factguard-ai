import asyncio
import time
import logging
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.fact_check import (
    FactCheckRequest, FactCheckResponse, ClaimExtractionItem, SourceMetadata,
    EvidenceAnalysisForClaim, BiasAnalysisResult, ConsistencyCheckResult,
    ClaimVerdict, AgentLog, VerdictType, InputType, EvidenceItem,
    URLAuthenticityResult, URLAuthenticityStatus
)
from app.agents.claim_extractor import claim_extractor_agent
from app.agents.researcher import research_agent
from app.agents.evidence_verifier import evidence_verifier_agent
from app.agents.source_credibility import source_credibility_agent
from app.agents.bias_detector import bias_detector_agent
from app.agents.consistency_checker import consistency_checker_agent
from app.agents.final_judge import final_judge_agent
from app.services.url_authenticity import url_authenticity_service
from app.database.models import FactCheckDB, ClaimDB, SourceDB, AgentLogDB

logger = logging.getLogger("factguard.orchestrator")

class MultiAgentOrchestrator:
    """
    Coordinates the multi-agent fact-checking pipeline execution graph.
    Separates URL Authenticity Verification from Page Content Claim Fact-Checking.
    """

    async def execute_fact_check(
        self,
        request: FactCheckRequest,
        db_session: Optional[AsyncSession] = None
    ) -> FactCheckResponse:
        total_start = time.time()
        fact_check_id = str(uuid.uuid4())
        agent_logs: List[AgentLog] = []

        logger.info(f"Starting FactGuard Multi-Agent Pipeline for Fact-Check ID: {fact_check_id}")

        # Requirement 6 Logging
        logger.info("===============================================")
        logger.info(f"RECEIVED INPUT TEXT ({request.input_type}): {request.input_text}")
        logger.info("===============================================")

        url_authenticity_res: Optional[URLAuthenticityResult] = None

        # Check for URL input and evaluate URL Authenticity independently
        if request.input_type == InputType.URL or request.input_text.startswith("http://") or request.input_text.startswith("https://") or "URL: http" in request.input_text:
            url_match = re.search(r'https?://[^\s]+', request.input_text)
            target_url = url_match.group(0) if url_match else request.input_text.strip()
            
            url_auth_start = time.time()
            url_authenticity_res = await url_authenticity_service.evaluate_url(target_url)
            url_auth_time = round((time.time() - url_auth_start) * 1000, 2)

            agent_logs.append(AgentLog(
                id=str(uuid.uuid4()),
                agent_name="URL Authenticity Evaluator Agent",
                status="completed" if url_authenticity_res.is_authentic else "warning",
                message=f"Evaluated URL authenticity for '{url_authenticity_res.domain}'. Status: {url_authenticity_res.status.value}, Classification: {url_authenticity_res.domain_classification}.",
                execution_time_ms=url_auth_time,
                created_at=datetime.utcnow().isoformat()
            ))

        # Agent 1: Claim Extraction Agent
        a1_start = time.time()
        extracted_claims = await claim_extractor_agent.run(request.input_text)
        a1_time = round((time.time() - a1_start) * 1000, 2)
        agent_logs.append(AgentLog(
            id=str(uuid.uuid4()),
            agent_name="Claim Extractor Agent",
            status="completed",
            message=f"Extracted {len(extracted_claims)} claim(s) from input text.",
            execution_time_ms=a1_time,
            created_at=datetime.utcnow().isoformat()
        ))

        if not extracted_claims:
            extracted_claims = [ClaimExtractionItem(
                claim_id="C001",
                claim_text=request.input_text[:500],
                is_verifiable=True,
                category="General"
            )]

        # Cap extracted claims for speed optimization to prevent timeout on live deployment
        max_claims = 1 if request.input_type == InputType.URL else 2
        if len(extracted_claims) > max_claims:
            logger.info(f"Capping extracted claims from {len(extracted_claims)} to top {max_claims} for speed optimization.")
            extracted_claims = extracted_claims[:max_claims]

        logger.info(f"EXTRACTED CLAIMS COUNT: {len(extracted_claims)}")
        for idx, claim_item in enumerate(extracted_claims):
            logger.info(f"   Claim [{idx+1}]: {claim_item.claim_text}")

        claim_sources_dict: Dict[str, List[SourceMetadata]] = {}
        claim_evidence_dict: Dict[str, EvidenceAnalysisForClaim] = {}
        claim_consistency_dict: Dict[str, ConsistencyCheckResult] = {}
        all_flattened_sources: List[SourceMetadata] = []

        async def _process_single_claim(claim: ClaimExtractionItem):
            c_logs: List[AgentLog] = []
            # Agent 2: Research & Web Retrieval Agent
            a2_start = time.time()
            sources = await research_agent.run(claim)
            a2_time = round((time.time() - a2_start) * 1000, 2)
            c_logs.append(AgentLog(
                id=str(uuid.uuid4()),
                agent_name="Research & Web Retrieval Agent",
                status="completed",
                message=f"Retrieved {len(sources)} unique source(s) for claim '{claim.claim_id}'.",
                execution_time_ms=a2_time,
                created_at=datetime.utcnow().isoformat()
            ))

            # Agent 4: Source Credibility Agent
            a4_start = time.time()
            sources = await source_credibility_agent.run(sources)
            a4_time = round((time.time() - a4_start) * 1000, 2)
            c_logs.append(AgentLog(
                id=str(uuid.uuid4()),
                agent_name="Source Credibility Agent",
                status="completed",
                message=f"Assessed credibility scores for {len(sources)} source(s).",
                execution_time_ms=a4_time,
                created_at=datetime.utcnow().isoformat()
            ))

            # Agent 3: Evidence Verification Agent
            a3_start = time.time()
            evidence_analysis = await evidence_verifier_agent.run(claim, sources)
            a3_time = round((time.time() - a3_start) * 1000, 2)
            c_logs.append(AgentLog(
                id=str(uuid.uuid4()),
                agent_name="Evidence Verification Agent",
                status="completed",
                message=f"Verified evidence for claim '{claim.claim_id}'. Supporting: {len(evidence_analysis.supporting_evidence)}, Contradicting: {len(evidence_analysis.contradicting_evidence)}.",
                execution_time_ms=a3_time,
                created_at=datetime.utcnow().isoformat()
            ))

            # Agent 6: Cross-Source Consistency Agent
            a6_start = time.time()
            consistency_res = await consistency_checker_agent.run(claim, sources, evidence_analysis)
            a6_time = round((time.time() - a6_start) * 1000, 2)
            c_logs.append(AgentLog(
                id=str(uuid.uuid4()),
                agent_name="Cross-Source Consistency Agent",
                status="completed",
                message=f"Checked cross-source consistency for claim '{claim.claim_id}'. Score: {consistency_res.consistency_score}.",
                execution_time_ms=a6_time,
                created_at=datetime.utcnow().isoformat()
            ))

            return claim, sources, evidence_analysis, consistency_res, c_logs

        async def _run_bias_agent():
            a5_start = time.time()
            bias_res = await bias_detector_agent.run(request.input_text)
            a5_time = round((time.time() - a5_start) * 1000, 2)
            b_log = AgentLog(
                id=str(uuid.uuid4()),
                agent_name="Bias & Manipulation Agent",
                status="completed",
                message=f"Analyzed text for bias/manipulation. Bias Score: {bias_res.bias_score}.",
                execution_time_ms=a5_time,
                created_at=datetime.utcnow().isoformat()
            )
            return bias_res, b_log

        # Execute per-claim pipelines and bias agent concurrently!
        claim_tasks = [_process_single_claim(claim) for claim in extracted_claims]
        bias_task = _run_bias_agent()

        pipeline_timeout = 12.0 if request.input_type == InputType.URL else 25.0
        try:
            all_results = await asyncio.wait_for(asyncio.gather(*claim_tasks, bias_task), timeout=pipeline_timeout)
            claim_results = all_results[:-1]
            bias_analysis, bias_log = all_results[-1]
            agent_logs.append(bias_log)
        except (asyncio.TimeoutError, Exception) as pe:
            logger.warning(f"Parallel claim & bias verification pipeline hit timeout or exception ({pe}). Using available authenticity signals.")
            claim_results = []
            bias_analysis = BiasAnalysisResult(
                has_bias=False,
                summary="Bias analysis skipped due to pipeline response time optimization.",
                bias_score=0.0
            )

        for claim, sources, evidence_analysis, consistency_res, c_logs in claim_results:
            all_flattened_sources.extend(sources)
            claim_sources_dict[claim.claim_id] = sources
            claim_evidence_dict[claim.claim_id] = evidence_analysis
            claim_consistency_dict[claim.claim_id] = consistency_res
            agent_logs.extend(c_logs)

        # Agent 7: Final Synthesis & Verdict Agent
        a7_start = time.time()
        final_judge_res = await final_judge_agent.run(
            original_input=request.input_text,
            claims=extracted_claims,
            claim_sources=claim_sources_dict,
            claim_evidence=claim_evidence_dict,
            claim_consistency=claim_consistency_dict,
            bias_analysis=bias_analysis
        )
        a7_time = round((time.time() - a7_start) * 1000, 2)
        agent_logs.append(AgentLog(
            id=str(uuid.uuid4()),
            agent_name="Final Synthesis & Verdict Agent",
            status="completed",
            message=f"Synthesized final verdict: {final_judge_res['overall_verdict'].value} with confidence {final_judge_res['confidence_score']}%.",
            execution_time_ms=a7_time,
            created_at=datetime.utcnow().isoformat()
        ))

        # Requirement 6 Logging
        logger.info(f"FINAL OVERALL VERDICT: {final_judge_res['overall_verdict']}")
        logger.info(f"FINAL CONFIDENCE SCORE: {final_judge_res['confidence_score']}%")
        logger.info("===============================================")

        # Deduplicate all sources for final payload
        unique_sources: List[SourceMetadata] = []
        seen_urls = set()
        for s in all_flattened_sources:
            if s.url not in seen_urls:
                seen_urls.add(s.url)
                unique_sources.append(s)

        sup_ev: List[EvidenceItem] = []
        con_ev: List[EvidenceItem] = []
        avg_cons = 85.0
        
        for cv in final_judge_res["claim_verdicts"]:
            if cv.evidence_breakdown:
                sup_ev.extend(cv.evidence_breakdown.supporting_evidence)
                con_ev.extend(cv.evidence_breakdown.contradicting_evidence)
            if cv.consistency:
                avg_cons = cv.consistency.consistency_score

        if request.input_type == InputType.URL and url_authenticity_res:
            if url_authenticity_res.status == URLAuthenticityStatus.TIMEOUT:
                final_overall_v = VerdictType.VERIFIED if url_authenticity_res.is_authentic else VerdictType.UNCERTAIN
                final_conf_score = url_authenticity_res.reputation_score
                final_summary = (
                    f"URL Status: TIMEOUT. Target website '{url_authenticity_res.domain}' did not respond within 15 seconds. "
                    f"Domain classification: {url_authenticity_res.domain_classification} ({url_authenticity_res.reputation_score}% domain trust score)."
                )
            elif url_authenticity_res.is_authentic:
                final_overall_v = VerdictType.VERIFIED
                final_conf_score = url_authenticity_res.reputation_score
                final_summary = (
                    f"URL Status: {url_authenticity_res.status.value}. "
                    f"Domain '{url_authenticity_res.domain}' classified as {url_authenticity_res.domain_classification} "
                    f"with {url_authenticity_res.reputation_score}% domain trust score. "
                    f"Page content claims evaluated separately below."
                )
            elif not url_authenticity_res.is_reachable:
                final_overall_v = VerdictType.UNVERIFIED
                final_conf_score = 0.0
                final_summary = (
                    f"URL Status: {url_authenticity_res.status.value}. "
                    f"Target domain '{url_authenticity_res.domain}' could not be reached or resolved."
                )
            else:
                final_overall_v = VerdictType.FALSE
                final_conf_score = url_authenticity_res.reputation_score
                final_summary = f"URL Status: {url_authenticity_res.status.value}."
        else:
            final_overall_v = final_judge_res["overall_verdict"]
            final_conf_score = final_judge_res["confidence_score"]
            final_summary = final_judge_res["summary"]

        response = FactCheckResponse(
            id=fact_check_id,
            status="success",
            verdict=final_overall_v.value,
            confidence=final_conf_score,
            original_input=request.input_text,
            input_type=request.input_type,
            overall_verdict=final_overall_v,
            confidence_score=final_conf_score,
            summary=final_summary,
            key_context=final_judge_res.get("key_context"),
            limitations=final_judge_res.get("limitations"),
            url_authenticity=url_authenticity_res,
            claims=extracted_claims,
            supporting_evidence=sup_ev,
            contradicting_evidence=con_ev,
            cross_source_consistency=avg_cons,
            extracted_claims=extracted_claims,
            claim_verdicts=final_judge_res["claim_verdicts"],
            sources=unique_sources,
            bias_analysis=bias_analysis,
            agent_logs=agent_logs,
            created_at=datetime.utcnow().isoformat()
        )

        # Save record to Database if session provided
        if db_session:
            try:
                await self._persist_fact_check(response, db_session)
            except Exception as db_err:
                logger.error(f"Failed to persist fact check to database: {db_err}")

        total_time = round((time.time() - total_start) * 1000, 2)
        logger.info(f"FactGuard Multi-Agent Pipeline completed in {total_time}ms.")
        return response

    async def _persist_fact_check(self, response: FactCheckResponse, db: AsyncSession):
        """Persist fact check run and child entities to database."""
        fact_check_db = FactCheckDB(
            id=response.id,
            original_input=response.original_input,
            input_type=response.input_type.value,
            overall_verdict=response.overall_verdict.value,
            confidence_score=response.confidence_score,
            summary=response.summary,
            key_context=response.key_context,
            limitations=response.limitations,
            has_bias=response.bias_analysis.has_bias if response.bias_analysis else False,
            bias_score=response.bias_analysis.bias_score if response.bias_analysis else 0.0,
            created_at=datetime.utcnow()
        )
        db.add(fact_check_db)

        for claim in response.extracted_claims:
            claim_db = ClaimDB(
                id=f"{response.id}_{claim.claim_id}",
                fact_check_id=response.id,
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                category=claim.category or "General"
            )
            db.add(claim_db)

        for src in response.sources:
            source_db = SourceDB(
                id=f"{response.id}_{src.source_id}",
                fact_check_id=response.id,
                title=src.title,
                url=src.url,
                publisher=src.publisher,
                excerpt=src.excerpt,
                credibility_score=src.credibility_score,
                credibility_rating=src.credibility_rating.value
            )
            db.add(source_db)

        for log in response.agent_logs:
            log_db = AgentLogDB(
                id=log.id or str(uuid.uuid4()),
                fact_check_id=response.id,
                agent_name=log.agent_name,
                status=log.status,
                message=log.message,
                execution_time_ms=log.execution_time_ms
            )
            db.add(log_db)

        await db.commit()

orchestrator = MultiAgentOrchestrator()
