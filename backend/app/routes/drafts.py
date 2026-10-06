from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LetterDraft
from app.schemas import DraftDetail, DraftSave, DraftSummary, MessageResponse
from app.services.audit import record_audit
from app.services.session import SessionService, get_current_doctor, get_session_service

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


@router.get("", response_model=list[DraftSummary])
def list_drafts(
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    rows = (
        db.query(LetterDraft)
        .filter(LetterDraft.doctor_id == doctor.id)
        .order_by(LetterDraft.updated_at.desc())
        .all()
    )
    return [
        DraftSummary(
            id=row.id,
            template_slug=row.template_slug,
            patient_name=row.patient_name,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.get("/by-template/{slug}", response_model=Optional[DraftDetail])
def get_draft_for_template(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    row = (
        db.query(LetterDraft)
        .filter(LetterDraft.doctor_id == doctor.id, LetterDraft.template_slug == slug)
        .one_or_none()
    )
    if not row:
        return None
    return DraftDetail(
        id=row.id,
        template_slug=row.template_slug,
        patient_name=row.patient_name,
        html_content=row.html_content,
        updated_at=row.updated_at,
    )


@router.put("", response_model=DraftDetail)
def save_draft(
    payload: DraftSave,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    row = (
        db.query(LetterDraft)
        .filter(LetterDraft.doctor_id == doctor.id, LetterDraft.template_slug == payload.template_slug)
        .one_or_none()
    )
    patient_name = (payload.patient_name or "").strip()
    if row:
        row.html_content = payload.html_content
        row.patient_name = patient_name
    else:
        row = LetterDraft(
            doctor_id=doctor.id,
            template_slug=payload.template_slug,
            html_content=payload.html_content,
            patient_name=patient_name,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return DraftDetail(
        id=row.id,
        template_slug=row.template_slug,
        patient_name=row.patient_name,
        html_content=row.html_content,
        updated_at=row.updated_at,
    )


@router.delete("/{draft_id}", response_model=MessageResponse)
def delete_draft(
    draft_id: str,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    row = (
        db.query(LetterDraft)
        .filter(LetterDraft.id == draft_id, LetterDraft.doctor_id == doctor.id)
        .one_or_none()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")
    db.delete(row)
    db.commit()
    record_audit(db, doctor.id, "draft_delete", request, detail=draft_id)
    return MessageResponse(message="Draft removed.")
