import base64

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Letter, LetterDraft
from app.schemas import (
    LetterDownload,
    LetterFinalize,
    LetterPreviewRequest,
    LetterPreviewResponse,
    LetterSummary,
    MessageResponse,
)
from app.services import template_loader
from app.services.audit import record_audit
from app.services.pdf import build_pdf_from_editor_html, guess_patient_name
from app.services.session import SessionService, get_current_doctor, get_session_service
from app.services.storage import build_s3_storage

router = APIRouter(prefix="/api/letters", tags=["letters"])


@router.get("", response_model=list[LetterSummary])
def list_letters(
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    rows = (
        db.query(Letter)
        .filter(Letter.doctor_id == doctor.id)
        .order_by(Letter.created_at.desc())
        .all()
    )
    return [
        LetterSummary(
            id=row.id,
            template_slug=row.template_slug,
            template_label=row.template_label,
            patient_name=row.patient_name,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/preview", response_model=LetterPreviewResponse)
def preview_letter(
    payload: LetterPreviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    template = template_loader.get_template(payload.template_slug)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")
    try:
        pdf_bytes = build_pdf_from_editor_html(payload.html_content, template.label)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit(db, doctor.id, "letter_preview", request, detail=template.slug)
    encoded = base64.b64encode(pdf_bytes).decode("ascii")
    return LetterPreviewResponse(pdf_base64=encoded)


@router.post("/finalize", response_model=LetterSummary, status_code=status.HTTP_201_CREATED)
def finalize_letter(
    payload: LetterFinalize,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    template = template_loader.get_template(payload.template_slug)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")

    try:
        pdf_bytes = build_pdf_from_editor_html(payload.html_content, template.label)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    settings = get_settings()
    try:
        storage = build_s3_storage(settings)
        storage_key = storage.save_pdf(doctor.id, pdf_bytes)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    patient_name = guess_patient_name(payload.html_content, payload.patient_name or "")

    letter = Letter(
        doctor_id=doctor.id,
        template_slug=template.slug,
        template_label=template.label,
        patient_name=patient_name,
        storage_key=storage_key,
    )
    db.add(letter)
    db.commit()
    db.refresh(letter)

    db.query(LetterDraft).filter(
        LetterDraft.doctor_id == doctor.id,
        LetterDraft.template_slug == template.slug,
    ).delete(synchronize_session=False)
    db.commit()

    record_audit(db, doctor.id, "letter_finalize", request, letter_id=letter.id)
    return LetterSummary(
        id=letter.id,
        template_slug=letter.template_slug,
        template_label=letter.template_label,
        patient_name=letter.patient_name,
        created_at=letter.created_at,
    )


@router.get("/{letter_id}/download", response_model=LetterDownload)
def download_letter(
    letter_id: str,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    letter = (
        db.query(Letter)
        .filter(Letter.id == letter_id, Letter.doctor_id == doctor.id)
        .one_or_none()
    )
    if not letter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Letter not found.")

    settings = get_settings()
    try:
        storage = build_s3_storage(settings)
        expires_in = settings.s3_presign_expiry_seconds
        url = storage.create_download_url(letter.storage_key, expires_in=expires_in)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    record_audit(db, doctor.id, "letter_download", request, letter_id=letter.id)
    return LetterDownload(url=url, expires_in_seconds=expires_in)


@router.delete("/{letter_id}", response_model=MessageResponse)
def delete_letter(
    letter_id: str,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    letter = (
        db.query(Letter)
        .filter(Letter.id == letter_id, Letter.doctor_id == doctor.id)
        .one_or_none()
    )
    if not letter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Letter not found.")

    settings = get_settings()
    try:
        storage = build_s3_storage(settings)
        storage.delete_pdf(letter.storage_key)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    db.delete(letter)
    db.commit()
    record_audit(db, doctor.id, "letter_delete", request, letter_id=letter_id)
    return MessageResponse(message="Letter removed from your history.")
