export type InputType = 'text' | 'url' | 'image';

export type VerdictType = 
  | 'VERIFIED'
  | 'FALSE'
  | 'MISLEADING'
  | 'PARTIALLY TRUE'
  | 'UNVERIFIED'
  | 'INSUFFICIENT EVIDENCE'
  | 'UNCERTAIN';

export type CredibilityRating = 'Very High' | 'High' | 'Medium' | 'Low' | 'Unknown';

export interface ClaimExtractionItem {
  claim_id: string;
  claim_text: string;
  is_verifiable: boolean;
  entities: string[];
  dates: string[];
  locations: string[];
  organizations: string[];
  numbers_or_stats: string[];
  category?: string;
}

export interface SourceMetadata {
  source_id: string;
  claim_id: string;
  title: string;
  url: string;
  publisher: string;
  publication_date?: string;
  excerpt: string;
  source_type: string;
  credibility_score: number;
  credibility_rating: CredibilityRating;
  reliability_indicators: string[];
}

export interface EvidenceItem {
  evidence_id: string;
  claim_id: string;
  source_id: string;
  source_title: string;
  source_url: string;
  publisher: string;
  evidence_text: string;
  evidence_type: 'supporting' | 'contradicting' | 'contextual';
  evidence_strength: number;
}

export interface EvidenceAnalysisForClaim {
  claim_id: string;
  claim_text: string;
  supporting_evidence: EvidenceItem[];
  contradicting_evidence: EvidenceItem[];
  contextual_evidence: EvidenceItem[];
  evidence_strength: number;
  reasoning: string;
}

export interface BiasIndicator {
  bias_type: string;
  detected: boolean;
  description: string;
  evidence_excerpt?: string;
}

export interface BiasAnalysisResult {
  has_bias: boolean;
  sensational_language: boolean;
  emotional_manipulation: boolean;
  clickbait_framing: boolean;
  missing_context: boolean;
  bias_score: number;
  indicators: BiasIndicator[];
  summary: string;
}

export interface ConsistencyCheckResult {
  claim_id: string;
  sources_agree: boolean;
  sources_contradict: boolean;
  repeating_single_source: boolean;
  independent_sources_count: number;
  consistency_score: number;
  findings: string;
}

export interface ClaimVerdict {
  claim_id: string;
  claim_text: string;
  verdict: VerdictType;
  confidence_score: number;
  explanation: string;
  supporting_sources_count: number;
  contradicting_sources_count: number;
  sources: SourceMetadata[];
  evidence_breakdown?: EvidenceAnalysisForClaim;
  consistency?: ConsistencyCheckResult;
}

export interface AgentLog {
  id?: string;
  agent_name: string;
  status: string;
  message: string;
  execution_time_ms: number;
  created_at: string;
}

export interface FactCheckResponse {
  id: string;
  original_input: string;
  input_type: InputType;
  overall_verdict: VerdictType;
  confidence_score: number;
  summary: string;
  key_context?: string;
  limitations?: string;
  extracted_claims: ClaimExtractionItem[];
  claim_verdicts: ClaimVerdict[];
  sources: SourceMetadata[];
  bias_analysis?: BiasAnalysisResult;
  agent_logs: AgentLog[];
  created_at: string;
  disclaimer: string;
}

export interface FactCheckHistoryItem {
  id: string;
  original_input: string;
  input_type: InputType;
  overall_verdict: VerdictType;
  confidence_score: number;
  claims_count: number;
  created_at: string;
}

export interface DemoClaimItem {
  id: string;
  title: string;
  category: string;
  input_text: string;
  expected_verdict: string;
  description: string;
}

export interface EvaluationMetricsResponse {
  total_fact_checks: number;
  verdict_distribution: Record<string, number>;
  avg_confidence_score: number;
  avg_response_time_ms: number;
  agent_success_rate: number;
  precision_score: number;
  recall_score: number;
  f1_score: number;
}
