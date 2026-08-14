# FactGuard AI — Multi-Agent AI Fact-Checking Platform

Live Project : https://factguard-ai.ai.studio/


> **B.Tech Final-Year Academic Project Demonstration**  
> An Evidence-First, Production-Quality Multi-Agent Fact-Checking Platform for Social Media Content.

---

## 1. Problem Statement & Motivation
Misinformation on social media spreads rapidly due to viral clickbait framing, emotional manipulation, and lack of real-time source verification. Standard single-prompt LLM chatbots often invent citations, hallucinate URLs, or present unsupported opinions as absolute facts. 

**FactGuard AI** solves this by establishing a **strict evidence-first, multi-agent architecture** where specialized autonomous agents independently perform claim extraction, multi-query live web research, evidence verification, publisher credibility scoring, linguistic bias analysis, and cross-source consistency checking before a Final Judge Agent produces a transparent verdict.

If reliable evidence cannot be found, the system strictly reports:  
**`"INSUFFICIENT EVIDENCE to determine the claim."`**

---

## 2. Multi-Agent Architecture

```
                               ┌──────────────────────────────────┐
                               │           React UI               │
                               │ (Landing, Check, Dashboard,      │
                               │  History, Sources, Demo, Docs)   │
                               └────────────────┬─────────────────┘
                                                │ REST API
                                                ▼
                               ┌──────────────────────────────────┐
                               │       FastAPI REST Engine        │
                               └────────────────┬─────────────────┘
                                                │
                                                ▼
                               ┌──────────────────────────────────┐
                               │     Multi-Agent Orchestrator     │
                               │       (LangGraph Workflow)       │
                               └────────────────┬─────────────────┘
                                                │
        ┌───────────────────┬───────────────────┼───────────────────┬───────────────────┐
        ▼                   ▼                   ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│Agent 1: Claim │   │Agent 2: Web   │   │Agent 3: Evidence│ │Agent 4: Source│   │Agent 5: Bias &│
│  Extraction   │   │  Researcher   │   │ Verification  │   │  Credibility  │   │ Manipulation  │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │                   │                   │
        └───────────────────┴───────────────────┼───────────────────┴───────────────────┘
                                                ▼
                                ┌────────────────────────────────┐
                                │ Agent 6: Cross-Source          │
                                │ Consistency Checker            │
                                └───────────────┬────────────────┘
                                                ▼
                                ┌────────────────────────────────┐
                                │ Agent 7: Final Judge           │
                                └───────────────┬────────────────┘
                                                │
                    ┌───────────────────────────┴───────────────────────────┐
                    ▼                                                       ▼
     ┌─────────────────────────────┐                         ┌─────────────────────────────┐
     │ SQLite / PostgreSQL DB      │                         │ ChromaDB / Vector Store RAG │
     │  (Fact-checks, Claims, Logs)│                         │  (Evidence Chunks & Index)  │
     └─────────────────────────────┘                         └─────────────────────────────┘
```

---

## 3. Specialized Agents Breakdown

- **Agent 1 — Claim Extractor**: Parses submitted text, separates opinions from verifiable facts, extracts atomic claim IDs (`C001`, `C002`), entities, dates, and locations.
- **Agent 2 — Web Researcher**: Executes 5 search query variations (exact, entity+event, date, contradiction, primary source) using live DuckDuckGo, Tavily, and Wikipedia APIs without fabricating URLs.
- **Agent 3 — Evidence Verifier**: Categorizes retrieved evidence into supporting, contradicting, and contextual data with strength scores.
- **Agent 4 — Source Credibility**: Evaluates TLD authority (.gov, .edu), primary news agency reputation, and HTTPS transport to assign a 0–100 credibility score.
- **Agent 5 — Bias & Manipulation Detector**: Identifies sensationalism, clickbait, and emotional manipulation while keeping tone analysis separate from factuality.
- **Agent 6 — Consistency Checker**: Analyzes agreement/disagreement across independent publishers.
- **Agent 7 — Final Judge Agent**: Synthesizes all findings into transparent verdicts (`VERIFIED`, `FALSE`, `MISLEADING`, `PARTIALLY TRUE`, `UNVERIFIED`, `INSUFFICIENT EVIDENCE`) with confidence scores.

---

## 4. Key Features

- **Multi-Input Verification**: Text claims, news article URLs (with SSRF protection), and social media screenshot image OCR.
- **Evidence-First Guarantee**: Never hallucinates citations or forces a True/False answer without backing.
- **Dynamic Real-Time Pipeline Tracker**: Animated agent progress status during verification.
- **Interactive Results Dashboard**: Confidence gauges, evidence balance visual bar, expandable claim breakdowns, source explorer, and agent execution logs.
- **Academic Demo Mode**: Pre-loaded with 10 academic test scenarios (True, False, Partially True, Misleading, Insufficient Evidence, Prompt Injection, etc.).
- **PDF Report Export**: One-click generation of academic fact-check reports using ReportLab.
- **Evaluation & Analytics Dashboard**: Metrics tracking precision, recall, latency, and verdict distributions.

---

## 5. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts, React Router v6.
- **Backend Engine**: FastAPI, Python 3.14, Pydantic Settings, BeautifulSoup4, HTTPX, ReportLab.
- **Database & Storage**: Async SQLAlchemy, SQLite / PostgreSQL, ChromaDB Vector Store.
- **Search & OCR**: DuckDuckGo Search API, Wikipedia API, PIL, Pytesseract OCR.

---

## 6. Local Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js v18+

### Step 1: Clone & Configure Environment
```powershell
cp .env.example .env
```

### Step 2: Start Backend API Engine
```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend API interactive Swagger docs available at: `http://localhost:8000/docs`

### Step 3: Start React Frontend
```powershell
cd frontend
npm install
npm run dev
```
Access frontend UI at: `http://localhost:5173`

---

## 7. Running Automated Test Suite

Run Pytest suite verifying all agents, prompt injection guardrails, and 10 test scenarios:

```powershell
pytest -v tests/test_agents.py
```

---

## 8. Academic Project Information

- **Project Title**: FactGuard AI — Multi-Agent AI Fact-Checking Platform
- **Degree**: B.Tech Final-Year Academic Project
- **Disclaimer**: FactGuard AI provides evidence-based analysis and is not a substitute for professional fact-checking or authoritative advice.
