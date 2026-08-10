# FactGuard AI Architecture Documentation

## System Architecture Overview

FactGuard AI is built around a decoupled **Multi-Agent Evidence-First Framework**. The core design prevents LLM hallucination by establishing an strict rule: **No factual verdict is produced without corroborating web evidence**.

```
+-----------------------------------------------------------------------+
|                            React 18 Frontend                          |
|  (Landing, Workspace, Dashboard, Sources, History, Analytics, Demo)   |
+----------------------------------- border-t --------------------------+
                                    | HTTP / REST
                                    v
+-----------------------------------------------------------------------+
|                         FastAPI Engine (Python 3.14)                  |
|          Endpoints: /fact-check, /url, /image, /pdf, /evaluations     |
+----------------------------------- border-t --------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                   Multi-Agent Graph Orchestrator                      |
|                                                                       |
|  [Agent 1: Claim Extractor] ---> [Agent 2: Multi-Query Researcher]   |
|                                                |                      |
|  [Agent 5: Bias Detector]   <--- [Agent 3: Evidence Verifier]         |
|             |                                  |                      |
|             v                                  v                      |
|  [Agent 6: Consistency]     <--- [Agent 4: Source Credibility]        |
|             |                                                         |
|             v                                                         |
|  [Agent 7: Final Judge]                                               |
+----------------------------------- border-t --------------------------+
                                    |
            +-----------------------+-----------------------+
            v                                               v
+-----------------------+                       +-----------------------+
| Async SQLAlchemy ORM  |                       | ChromaDB Vector Store |
|  (SQLite / Postgres)  |                       |  (RAG Evidence Chunks)|
+-----------------------+                       +-----------------------+
```

## Core Components
1. **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons + Recharts.
2. **REST API**: FastAPI async server running on Uvicorn with Pydantic v2 validation schemas.
3. **Multi-Agent Engine**: Modular Python classes implementing 7 specialized agents.
4. **Vector Store RAG**: ChromaDB indexing evidence excerpts, URLs, and embeddings for rapid retrieval.
5. **Relational DB**: Async SQLAlchemy ORM supporting SQLite and PostgreSQL.
