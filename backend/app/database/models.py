import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    fact_checks = relationship("FactCheckDB", back_populates="user", cascade="all, delete-orphan")

class FactCheckDB(Base):
    __tablename__ = "fact_checks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    original_input = Column(Text, nullable=False)
    input_type = Column(String(20), nullable=False, default="text")
    overall_verdict = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    summary = Column(Text, nullable=True)
    key_context = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    bias_analysis_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="fact_checks")
    claims = relationship("ClaimDB", back_populates="fact_check", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLogDB", back_populates="fact_check", cascade="all, delete-orphan")

class ClaimDB(Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fact_check_id = Column(String(36), ForeignKey("fact_checks.id"), nullable=False)
    claim_id_code = Column(String(50), nullable=False) # e.g. C001
    claim_text = Column(Text, nullable=False)
    is_verifiable = Column(Boolean, default=True)
    entities_json = Column(JSON, nullable=True)
    verdict = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    fact_check = relationship("FactCheckDB", back_populates="claims")
    sources = relationship("SourceDB", back_populates="claim", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceDB", back_populates="claim", cascade="all, delete-orphan")

class SourceDB(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id"), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    publisher = Column(String(255), nullable=False)
    publication_date = Column(String(100), nullable=True)
    excerpt = Column(Text, nullable=True)
    source_type = Column(String(50), default="news")
    credibility_score = Column(Float, default=50.0)
    credibility_rating = Column(String(50), default="Medium")
    reliability_indicators_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    claim = relationship("ClaimDB", back_populates="sources")
    evidence_items = relationship("EvidenceDB", back_populates="source", cascade="all, delete-orphan")

class EvidenceDB(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id"), nullable=False)
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=True)
    evidence_text = Column(Text, nullable=False)
    evidence_type = Column(String(50), nullable=False) # supporting, contradicting, contextual
    evidence_strength = Column(Float, default=50.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    claim = relationship("ClaimDB", back_populates="evidence_items")
    source = relationship("SourceDB", back_populates="evidence_items")

class AgentLogDB(Base):
    __tablename__ = "agent_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fact_check_id = Column(String(36), ForeignKey("fact_checks.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False) # started, completed, failed
    message = Column(Text, nullable=False)
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    fact_check = relationship("FactCheckDB", back_populates="agent_logs")

class EvaluationDB(Base):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fact_check_id = Column(String(36), nullable=True)
    metric_type = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
