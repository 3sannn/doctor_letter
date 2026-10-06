from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import DoctorProfile, MessageResponse, SessionCreate, SessionResponse
from app.services.audit import record_audit
from app.services.doctor_profile import doctor_to_profile
from app.services.rate_limit import get_session_rate_limiter
from app.services.session import (
    SessionService,
    clear_session_cookie,
    get_current_doctor,
    get_or_create_doctor,
    get_session_service,
    set_session_cookie,
)

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("", response_model=SessionResponse)
def start_session(
    payload: SessionCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    settings = get_settings()
    get_session_rate_limiter(settings).check(request)
    doctor = get_or_create_doctor(db, payload.mobile)
    token = session_service.issue_token(doctor.id)
    set_session_cookie(response, token, settings)
    record_audit(db, doctor.id, "session_start", request)
    return SessionResponse(mobile=doctor.mobile)


@router.get("/me", response_model=DoctorProfile)
def read_session_profile(
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    return doctor_to_profile(doctor)


@router.post("/logout", response_model=MessageResponse)
def end_session(response: Response):
    settings = get_settings()
    clear_session_cookie(response, settings)
    return MessageResponse(message="Signed out.")
