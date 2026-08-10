import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.fact_check import (
    FactCheckRequest, FactCheckResponse, InputType, VerdictType, AgentLog,
    ClaimExtractionItem, SourceMetadata, EvidenceAnalysisForClaim,
    BiasAnalysisResult, ConsistencyCheckResult, ClaimVerdict
)
from app.agents.claim_extractor import claim_extractor_agent
from app.agents.researcher import research_agent
from app.agents.evidence_verifier import evidence_verifier_agent
from app.agents.source_credibility import source_credibility_agent
from app.agents.bias_detector import bias_detector_agent
from app.agents.consistency_checker import consistency_checker_agent
from app.agents.final_judge import final_judge_agent
from app.rag.vector_store import vector_rag
from app.database.models import FactCheckDB, ClaimDB, SourceDB, EvidenceDB, AgentLogDB

logger = logging.getLogger("factguard.orchestrator")

class FactGuardOrchestrator:
    """
    Multi-Agent Stateful Graph Orchestrator for FactGuard AI.
    Executes Agent 1 -> Agent 2 -> Agent 3 -> Agent 4 -> Agent 5 -> Agent 6 -> Agent 7 pipeline.
    """

    async def execute_fact_check(
        self,
        request: FactCheckRequest,
        db_session: Optional[AsyncSession] = None
    ) -> FactCheckResponse:
        fact_check_id = str(uuid.uuid4())
        start_pipeline_time = time.time()
        agent_logs: List[AgentLog] = []

        logger.info(f"Starting FactGuard Multi-Agent Pipeline for Fact-Check ID: {fact_check_id}")

        # -------------------------------------------------------------
        # STEP 1: Agent 1 - Claim Extraction Agent
        # -------------------------------------------------------------
        a1_start = time.time()
        agent_logs.append(AgentLog(
            agent_name="Claim Extraction Agent",
            status="started",
            message="Analyzing submitted input text and breaking into atomic verifiable claims...",
            execution_time_ms=0.0,
            created_at=datetime.utcnow().isoformat()
        ))
        
        extracted_claims: List[ClaimExtractionItem] = await claim_extractor_agent.run(request.input_text)
        a1_time = round((time.time() - a1_start) * 1000, 2)
        
        agent_logs[-1].status = "completed"
        agent_logs[-1].message = f"Extracted {len(extracted_claims)} verifiable claim(s)."
        agent_logs[-1].execution_time_ms = a1_time

        # -------------------------------------------------------------
        # STEP 2, 3, 4, 6: Parallel per-claim research & evaluation
        # -------------------------------------------------------------
        claim_sources: Dict[str, List[SourceMetadata]] = {}
        claim_evidence: Dict[str, EvidenceAnalysisForClaim] = {}
        claim_consistency: Dict[str, ConsistencyCheckResult] = {}
        all_flattened_sources: List[SourceMetadata] = []

        for claim in extracted_claims:
            cid = claim.claim_id
            
            # Agent 2: Web Research
            a2_start = time.time()
            sources = await research_agent.run(claim)
            a2_time = round((time.time() - a2_start) * 1000, 2)
            agent_logs.append(AgentLog(
                agent_name=f"Research Agent ({cid})",
                status="completed",
                message=f"Retrieved {len(sources)} web sources across multi-query strategies.",
                execution_time_ms=a2_time,
                created_at=datetime.utcnow().isoformat()
            ))

            # Agent 4: Source Credibility Evaluation
            a4_start = time.time()
            evaluated_sources = await source_credibility_agent.run(sources)
            a4_time = round((time.time() - a4_start) * 1000, 2)
            agent_logs.append(AgentLog(
                agent_name=f"Source Credibility Agent ({cid})",
                status="completed",
                message=f"Evaluated domain authority and credibility ratings for {len(evaluated_sources)} sources.",
                execution_time_ms=a4_time,
                created_at=datetime.utcnow().isoformat()
            ))

            claim_sources[cid] = evaluated_sources
            all_flattened_sources.extend(evaluated_sources)

            # Agent 3: Evidence Verification
            a3_start = time.time()
            ev_analysis = await evidence_verifier_agent.run(claim, evaluated_sources)
            a3_time = round((time.time() - a3_start) * 1000, 2)
            agent_logs.append(AgentLog(
                agent_name=f"Evidence Verification Agent ({cid})",
                status="completed",
                message=f"Categorized evidence into {len(ev_analysis.supporting_evidence)} supporting and {len(ev_analysis.contradicting_evidence)} contradicting items.",
                execution_time_ms=a3_time,
                created_at=datetime.utcnow().isoformat()
            ))

            claim_evidence[cid] = ev_analysis

            # Store evidence in RAG Vector Store
            try:
                evidence_items_dict = [
                    item.model_dump() for item in ev_analysis.supporting_evidence + ev_analysis.contradicting_evidence + ev_analysis.contextual_evidence
                ]
                vector_rag.add_evidence_chunks(claim_id=cid, evidence_items=evidence_items_dict)
            except Exception as e:
                logger.warning(f"Failed to add evidence to RAG: {e}")

            # Agent 6: Cross-Source Consistency Checker
            a6_start = time.time()
            consistency_res = await consistency_checker_agent.run(claim, evaluated_sources, ev_analysis)
            a6_time = round((time.time() - a6_start) * 1000, 2)
            agent_logs.append(AgentLog(
                agent_name=f"Cross-Source Consistency Agent ({cid})",
                status="completed",
                message=consistency_res.findings,
                execution_time_ms=a6_time,
                created_at=datetime.utcnow().isoformat()
            ))

            claim_consistency[cid] = consistency_res

        # -------------------------------------------------------------
        # STEP 5: Agent 5 - Bias & Manipulation Detection Agent
        # -------------------------------------------------------------
        a5_start = time.time()
        bias_analysis: BiasAnalysisResult = await bias_detector_agent.run(request.input_text)
        a5_time = round((time.time() - a5_start) * 1000, 2)
        agent_logs.append(AgentLog(
            agent_name="Bias & Manipulation Detection Agent",
            status="completed",
            message=bias_analysis.summary,
            execution_time_ms=a5_time,
            created_at=datetime.utcnow().isoformat()
        ))

        # -------------------------------------------------------------
        # STEP 7: Agent 7 - Final Judge Agent
        # -------------------------------------------------------------
        a7_start = time.time()
        final_judge_res = await final_judge_agent.run(
            original_input=request.input_text,
            claims=extracted_claims,
            claim_sources=claim_sources,
            claim_evidence=claim_evidence,
            claim_consistency=claim_consistency,
            bias_analysis=bias_analysis
        )
        a7_time = round((time.time() - a7_start) * 1000, 2)
        agent_logs.append(AgentLog(
            agent_name="Final Judge Agent",
            status="completed",
            message=f"Final Verdict issued: {final_judge_res['overall_verdict']} with {final_judge_res['confidence_score']}% confidence.",
            execution_time_ms=a7_time,
            created_at=datetime.utcnow().isoformat()
        ))

        # Deduplicate all sources for final payload
        unique_sources: List[SourceMetadata] = []
        seen_urls = set()
        for s in all_flattened_sources:
            if s.url not in seen_urls:
                seen_urls.add(s.url)
                unique_sources.append(s)

        response = FactCheckResponse(
            id=fact_check_id,
            original_input=request.input_text,
            input_type=request.input_type,
            overall_verdict=final_judge_res["overall_verdict"],
            confidence_score=final_judge_res["confidence_score"],
            summary=final_judge_res["summary"],
            key_context=final_judge_res.get("key_context"),
            limitations=final_judge_res.get("limitations"),
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
                logger.error(f"Error persisting fact-check to database: {db_err}")

        total_time = round((time.time() - start_pipeline_time) * 1000, 2)
        logger.info(f"FactGuard Multi-Agent Pipeline completed in {total_time}ms.")
        return response

    async def _persist_fact_check(self, res: FactCheckResponse, db: AsyncSession):
        fact_check_db = FactCheckDB(
            id=res.id,
            original_input=res.original_input,
            input_type=res.input_type.value,
            overall_verdict=res.overall_verdict.value,
            confidence_score=res.confidence_score,
            summary=res.summary,
            key_context=res.key_context,
            limitations=res.limitations,
            bias_analysis_json=res.bias_analysis.model_dump() if res.bias_analysis else None,
            created_at=datetime.fromisoformat(res.created_at)
        )
        db.add(fact_check_db)

        # Save Claims & Sources
        for cv in res.claim_verdicts:
            claim_db = ClaimDB(
                id=str(uuid.uuid4()),
                fact_check_id=res.id,
                claim_id_code=cv.claim_id,
                claim_text=cv.claim_text,
                verdict=cv.verdict.value,
                confidence_score=cv.confidence_score,
                explanation=cv.explanation
            )
            db.add(claim_db)

        # Save Agent Logs
        for log in res.agent_logs:
            log_db = AgentLogDB(
                id=str(uuid.uuid4()),
                fact_check_id=res.id,
                agent_name=log.agent_name,
                status=log.status,
                message=log.message,
                execution_time_ms=log.execution_time_ms
            )
            db.add(log_db)

        await db.commit()

orchestrator = FactGuardOrchestrator()
