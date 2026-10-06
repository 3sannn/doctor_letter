from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TemplateDetail, TemplateSummary
from app.services import template_loader
from app.services.session import SessionService, get_current_doctor, get_session_service

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateSummary])
def list_letter_templates():
    return [
        TemplateSummary(
            slug=item.slug,
            label=item.label,
            description=item.description,
        )
        for item in template_loader.list_templates()
    ]


@router.get("/{slug}", response_model=TemplateDetail)
def get_letter_template(
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
    return TemplateDetail(
        slug=template.slug,
        label=template.label,
        description=template.description,
        html=html,
    )
