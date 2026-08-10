import time
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.schemas.fact_check import (
    FactCheckRequest, FactCheckResponse, FactCheckHistoryItem, InputType,
    SourceMetadata, AgentLog
)
from app.graph.workflow import orchestrator
from app.database.session import get_db
from app.database.models import FactCheckDB, ClaimDB, SourceDB, AgentLogDB
from app.services.ocr_service import ocr_service
from app.services.url_scraper import url_scraper_service
from app.services.pdf_generator import pdf_generator
from app.services.demo_data import DEMO_CLAIMS_DATABASE

logger = logging.getLogger("factguard.api.fact_check")
router = APIRouter(prefix="/fact-check", tags=["Fact Check"])

@router.post("", response_model=FactCheckResponse)
async def create_fact_check(
    request: FactCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute full multi-agent fact check for raw text or post input.
    """
    if not request.input_text or len(request.input_text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Input text must be at least 5 characters long.")

    try:
        response = await orchestrator.execute_fact_check(request, db_session=db)
        return response
    except Exception as e:
        logger.error(f"Fact check pipeline execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Multi-agent workflow error: {str(e)}")

@router.post("/url", response_model=FactCheckResponse)
async def create_fact_check_url(
    url: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape target article/social media URL and execute multi-agent fact check.
    """
    try:
        title, content = await url_scraper_service.fetch_url_content(url)
        request = FactCheckRequest(input_text=content, input_type=InputType.URL)
        response = await orchestrator.execute_fact_check(request, db_session=db)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"URL fact check failed for '{url}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process target URL: {str(e)}")

@router.post("/image", response_model=FactCheckResponse)
async def create_fact_check_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract text from social media screenshot using OCR and execute multi-agent fact check.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image (JPEG, PNG, WebP).")

    try:
        contents = await file.read()
        extracted_text = ocr_service.extract_text_from_image_bytes(contents)
        
        request = FactCheckRequest(input_text=extracted_text, input_type=InputType.IMAGE)
        response = await orchestrator.execute_fact_check(request, db_session=db)
        return response
    except Exception as e:
        logger.error(f"Image OCR fact check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image OCR: {str(e)}")

@router.get("/history", response_model=List[FactCheckHistoryItem])
async def get_fact_check_history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get past fact-checking reports history.
    """
    try:
        stmt = select(FactCheckDB).order_by(FactCheckDB.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        records = result.scalars().all()

        history = []
        for r in records:
            # Count claims
            c_stmt = select(func.count(ClaimDB.id)).where(ClaimDB.fact_check_id == r.id)
            c_res = await db.execute(c_stmt)
            c_count = c_res.scalar() or 1

            history.append(FactCheckHistoryItem(
                id=r.id,
                original_input=r.original_input[:120] + ("..." if len(r.original_input) > 120 else ""),
                input_type=InputType(r.input_type),
                overall_verdict=r.overall_verdict,
                confidence_score=r.confidence_score,
                claims_count=c_count,
                created_at=r.created_at.isoformat()
            ))
        return history
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return []

@router.get("/demo-claims")
async def get_demo_claims():
    """
    Get pre-configured academic demo claims for faculty demonstration.
    """
    return DEMO_CLAIMS_DATABASE

@router.get("/{id}", response_model=FactCheckResponse)
async def get_fact_check_by_id(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve full fact check report by ID.
    """
    stmt = select(FactCheckDB).where(FactCheckDB.id == id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Fact check report not found.")

    # Reconstruct Pydantic model
    request = FactCheckRequest(input_text=record.original_input, input_type=InputType(record.input_type))
    response = await orchestrator.execute_fact_check(request, db_session=db)
    response.id = record.id
    return response

@router.get("/{id}/pdf")
async def download_fact_check_pdf(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Download fact-check report as PDF.
    """
    stmt = select(FactCheckDB).where(FactCheckDB.id == id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Report not found.")

    request = FactCheckRequest(input_text=record.original_input, input_type=InputType(record.input_type))
    fact_check_res = await orchestrator.execute_fact_check(request, db_session=None)
    fact_check_res.id = record.id

    pdf_bytes = pdf_generator.generate_fact_check_pdf(fact_check_res)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=FactGuard_Report_{id[:8]}.pdf"}
    )
