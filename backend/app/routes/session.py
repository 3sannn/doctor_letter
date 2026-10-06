from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas import (
    DoctorProfile,
    MessageResponse,
    OtpRequest,
    OtpRequestResponse,
    OtpVerify,
    SessionBootstrap,
    SessionCreate,
    SessionResponse,
)
from app.services.audit import record_audit
from app.services.doctor_profile import doctor_to_profile
from app.services.otp import request_otp, verify_otp
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


@router.get("/bootstrap", response_model=SessionBootstrap)
def session_bootstrap():
    settings = get_settings()
    return SessionBootstrap(otp_enabled=settings.otp_enabled)


@router.post("/otp/request", response_model=OtpRequestResponse)
def send_otp(
    payload: OtpRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if not settings.otp_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP is disabled.")
    get_session_rate_limiter(settings).check(request, mobile=payload.mobile)
    result = request_otp(db, settings, payload.mobile)
    return OtpRequestResponse(**result)


@router.post("/otp/verify", response_model=SessionResponse)
def confirm_otp(
    payload: OtpVerify,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    settings = get_settings()
    if not settings.otp_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP is disabled.")
    get_session_rate_limiter(settings).check(request, mobile=payload.mobile)
    verify_otp(db, settings, payload.mobile, payload.code)
    doctor = get_or_create_doctor(db, payload.mobile)
    token = session_service.issue_token(doctor.id)
    set_session_cookie(response, token, settings)
    record_audit(db, doctor.id, "session_start", request)
    return SessionResponse(mobile=doctor.mobile)


@router.post("", response_model=SessionResponse)
def start_session(
    payload: SessionCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    settings = get_settings()
    if settings.otp_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Use the verification code sent to your mobile.",
        )
    get_session_rate_limiter(settings).check(request, mobile=payload.mobile)
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
