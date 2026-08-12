from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class InputType(str, Enum):
    TEXT = "text"
    URL = "url"
    IMAGE = "image"

class VerdictType(str, Enum):
    VERIFIED = "VERIFIED"
    FALSE = "FALSE"
    MISLEADING = "MISLEADING"
    PARTIALLY_TRUE = "PARTIALLY TRUE"
    UNVERIFIED = "UNVERIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"
    UNCERTAIN = "UNCERTAIN"

class CredibilityRating(str, Enum):
    VERY_HIGH = "Very High"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"

class FactCheckRequest(BaseModel):
    input_text: str = Field(..., description="Text content, URL, or extracted image text to verify")
    input_type: InputType = Field(default=InputType.TEXT, description="Type of input: text, url, image")

class ClaimExtractionItem(BaseModel):
    claim_id: str
    claim_text: str
    is_verifiable: bool = True
    entities: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    numbers_or_stats: List[str] = Field(default_factory=list)
    category: Optional[str] = "General"

class SourceMetadata(BaseModel):
    source_id: str
    claim_id: str
    title: str
    url: str
    publisher: str
    publication_date: Optional[str] = None
    excerpt: str
    source_type: str = "news" # official, news, academic, blog, social
    credibility_score: float = Field(default=50.0, ge=0.0, le=100.0)
    credibility_rating: CredibilityRating = CredibilityRating.MEDIUM
    reliability_indicators: List[str] = Field(default_factory=list)

class EvidenceItem(BaseModel):
    evidence_id: str
    claim_id: str
    source_id: str
    source_title: str
    source_url: str
    publisher: str
    evidence_text: str
    evidence_type: str # supporting, contradicting, contextual
    evidence_strength: float = Field(default=50.0, ge=0.0, le=100.0)

class EvidenceAnalysisForClaim(BaseModel):
    claim_id: str
    claim_text: str
    supporting_evidence: List[EvidenceItem] = Field(default_factory=list)
    contradicting_evidence: List[EvidenceItem] = Field(default_factory=list)
    contextual_evidence: List[EvidenceItem] = Field(default_factory=list)
    evidence_strength: float = Field(default=50.0, ge=0.0, le=100.0)
    reasoning: str

class BiasIndicator(BaseModel):
    bias_type: str # sensationalism, fear_mongering, clickbait, missing_context, cherry_picking, false_causality
    detected: bool
    description: str
    evidence_excerpt: Optional[str] = None

class BiasAnalysisResult(BaseModel):
    has_bias: bool
    sensational_language: bool = False
    emotional_manipulation: bool = False
    clickbait_framing: bool = False
    missing_context: bool = False
    bias_score: float = Field(default=0.0, ge=0.0, le=100.0) # 0 = neutral, 100 = heavily biased
    indicators: List[BiasIndicator] = Field(default_factory=list)
    summary: str

class ConsistencyCheckResult(BaseModel):
    claim_id: str
    sources_agree: bool
    sources_contradict: bool
    repeating_single_source: bool
    independent_sources_count: int
    consistency_score: float = Field(default=50.0, ge=0.0, le=100.0)
    findings: str

class ClaimVerdict(BaseModel):
    claim_id: str
    claim_text: str
    verdict: VerdictType
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    explanation: str
    supporting_sources_count: int = 0
    contradicting_sources_count: int = 0
    sources: List[SourceMetadata] = Field(default_factory=list)
    evidence_breakdown: Optional[EvidenceAnalysisForClaim] = None
    consistency: Optional[ConsistencyCheckResult] = None

class AgentLog(BaseModel):
    id: Optional[str] = None
    agent_name: str
    status: str # started, completed, failed, skipped
    message: str
    execution_time_ms: float
    created_at: str

class URLAuthenticityStatus(str, Enum):
    AUTHENTIC = "VERIFIED / AUTHENTIC"
    SUSPICIOUS = "SUSPICIOUS"
    UNREACHABLE = "UNREACHABLE / INVALID"

class URLAuthenticityResult(BaseModel):
    url: str
    domain: str
    status: URLAuthenticityStatus
    is_authentic: bool
    is_reachable: bool
    has_ssl: bool
    domain_classification: str
    reputation_score: float = Field(default=50.0, ge=0.0, le=100.0)
    security_notes: List[str] = Field(default_factory=list)

class FactCheckResponse(BaseModel):
    id: str
    status: str = "success"
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    original_input: str
    input_type: InputType
    overall_verdict: VerdictType
    confidence_score: float
    summary: str
    key_context: Optional[str] = None
    limitations: Optional[str] = None
    url_authenticity: Optional[URLAuthenticityResult] = None
    claims: List[ClaimExtractionItem] = Field(default_factory=list)
    supporting_evidence: List[EvidenceItem] = Field(default_factory=list)
    contradicting_evidence: List[EvidenceItem] = Field(default_factory=list)
    cross_source_consistency: float = 85.0
    extracted_claims: List[ClaimExtractionItem] = Field(default_factory=list)
    claim_verdicts: List[ClaimVerdict] = Field(default_factory=list)
    sources: List[SourceMetadata] = Field(default_factory=list)
    bias_analysis: Optional[BiasAnalysisResult] = None
    agent_logs: List[AgentLog] = Field(default_factory=list)
    created_at: str
    disclaimer: str = "FactGuard AI provides evidence-based analysis and is not a substitute for professional fact-checking or authoritative advice."

class FactCheckHistoryItem(BaseModel):
    id: str
    original_input: str
    input_type: InputType
    overall_verdict: VerdictType
    confidence_score: float
    claims_count: int
    created_at: str

class EvaluationMetricsResponse(BaseModel):
    total_fact_checks: int
    verdict_distribution: Dict[str, int]
    avg_confidence_score: float
    avg_response_time_ms: float
    agent_success_rate: float
    precision_score: float
    recall_score: float
    f1_score: float
