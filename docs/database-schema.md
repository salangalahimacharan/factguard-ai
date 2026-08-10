# FactGuard AI Database Schema Documentation

## Relational Entity Schema

```sql
-- Users Table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact Checks Table
CREATE TABLE fact_checks (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    original_input TEXT NOT NULL,
    input_type VARCHAR(20) NOT NULL,
    overall_verdict VARCHAR(50) NOT NULL,
    confidence_score FLOAT NOT NULL,
    summary TEXT,
    key_context TEXT,
    limitations TEXT,
    bias_analysis_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Claims Table
CREATE TABLE claims (
    id VARCHAR(36) PRIMARY KEY,
    fact_check_id VARCHAR(36) REFERENCES fact_checks(id) ON DELETE CASCADE,
    claim_id_code VARCHAR(50) NOT NULL,
    claim_text TEXT NOT NULL,
    is_verifiable BOOLEAN DEFAULT TRUE,
    entities_json JSON,
    verdict VARCHAR(50) NOT NULL,
    confidence_score FLOAT NOT NULL,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sources Table
CREATE TABLE sources (
    id VARCHAR(36) PRIMARY KEY,
    claim_id VARCHAR(36) REFERENCES claims(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    publisher VARCHAR(255) NOT NULL,
    publication_date VARCHAR(100),
    excerpt TEXT,
    source_type VARCHAR(50) DEFAULT 'news',
    credibility_score FLOAT DEFAULT 50.0,
    credibility_rating VARCHAR(50) DEFAULT 'Medium',
    reliability_indicators_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evidence Table
CREATE TABLE evidence (
    id VARCHAR(36) PRIMARY KEY,
    claim_id VARCHAR(36) REFERENCES claims(id) ON DELETE CASCADE,
    source_id VARCHAR(36) REFERENCES sources(id) ON DELETE CASCADE,
    evidence_text TEXT NOT NULL,
    evidence_type VARCHAR(50) NOT NULL,
    evidence_strength FLOAT DEFAULT 50.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Logs Table
CREATE TABLE agent_logs (
    id VARCHAR(36) PRIMARY KEY,
    fact_check_id VARCHAR(36) REFERENCES fact_checks(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    execution_time_ms FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
