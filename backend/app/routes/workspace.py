from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LetterDraft
from app.schemas import DraftDetail, DraftSummary, DoctorProfile, EditorSetupResponse, WorkspaceResponse
from app.services import template_loader
from app.services.doctor_profile import doctor_to_profile
from app.services.session import SessionService, get_current_doctor, get_session_service

router = APIRouter(prefix="/api", tags=["workspace"])


@router.get("/workspace", response_model=WorkspaceResponse)
def load_workspace(
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    drafts = (
        db.query(LetterDraft)
        .filter(LetterDraft.doctor_id == doctor.id)
        .order_by(LetterDraft.updated_at.desc())
        .all()
    )
    return WorkspaceResponse(
        profile=doctor_to_profile(doctor),
        drafts=[
            DraftSummary(
                id=row.id,
                template_slug=row.template_slug,
                patient_name=row.patient_name,
                updated_at=row.updated_at,
            )
            for row in drafts
        ],
    )


@router.get("/editor/{slug}", response_model=EditorSetupResponse)
def load_editor(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    template = template_loader.get_template(slug)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")

    doctor = get_current_doctor(request, db, session_service)
    html = template_loader.load_template_html(slug, doctor)
    if html is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template content missing.")

    draft_row = (
        db.query(LetterDraft)
        .filter(LetterDraft.doctor_id == doctor.id, LetterDraft.template_slug == slug)
        .one_or_none()
    )
    draft = None
    if draft_row:
        draft = DraftDetail(
            id=draft_row.id,
            template_slug=draft_row.template_slug,
            patient_name=draft_row.patient_name,
            html_content=draft_row.html_content,
            updated_at=draft_row.updated_at,
        )

    return EditorSetupResponse(
        slug=template.slug,
        label=template.label,
        description=template.description,
        html=html,
        draft=draft,
    )
