# FactGuard AI Agent Workflow Documentation

## Multi-Agent Workflow Pipeline

Each submitted post undergoes systematic analysis across 7 autonomous agents:

### Agent 1 — Claim Extraction Agent
- **Responsibilities**: Extracts atomic factual claims from raw input text. Identifies entities, dates, locations, organizations, and numbers/statistics.
- **Output**: Array of `ClaimExtractionItem` objects with unique IDs (`C001`, `C002`).

### Agent 2 — Research Agent
- **Responsibilities**: Generates 5 distinct search query variations (exact match, entity+event, date, contradiction, primary source) and executes live web retrieval via DuckDuckGo, Tavily, or Wikipedia.
- **Output**: List of `SourceMetadata` containing titles, URLs, publishers, dates, and excerpts.

### Agent 3 — Evidence Verification Agent
- **Responsibilities**: Compares each claim against retrieved source excerpts. Separates evidence into `supporting`, `contradicting`, and `contextual` buckets.
- **Output**: `EvidenceAnalysisForClaim` with quantitative evidence strength (0-100).

### Agent 4 — Source Credibility Agent
- **Responsibilities**: Calculates domain authority (0-100 score) based on TLD (.gov, .edu), primary publisher track record (Reuters, AP, WHO), and HTTPS transport.
- **Output**: Updated `SourceMetadata` with credibility ratings (`Very High`, `High`, `Medium`, `Low`).

### Agent 5 — Bias & Manipulation Detection Agent
- **Responsibilities**: Analyzes raw input for sensationalism, emotional manipulation, clickbait framing, and absolute claims while keeping tone distinct from factuality.
- **Output**: `BiasAnalysisResult` with bias score and indicator flags.

### Agent 6 — Cross-Source Consistency Agent
- **Responsibilities**: Verifies agreement across independent news publishers and flags single-source echo chambers.
- **Output**: `ConsistencyCheckResult` score and findings summary.

### Agent 7 — Final Judge Agent
- **Responsibilities**: Synthesizes all prior outputs and computes the final verdict (`VERIFIED`, `FALSE`, `MISLEADING`, `PARTIALLY TRUE`, `UNVERIFIED`, `INSUFFICIENT EVIDENCE`) with confidence score.
- **Strict Rule**: If reliable evidence is inadequate, strictly returns `INSUFFICIENT EVIDENCE`.
