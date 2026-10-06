from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DoctorProfile, DoctorProfileUpdate
from app.services.audit import record_audit
from app.services.doctor_profile import doctor_to_profile
from app.services.session import SessionService, get_current_doctor, get_session_service

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=DoctorProfile)
def read_profile(
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    return doctor_to_profile(doctor)


@router.put("", response_model=DoctorProfile)
def update_profile(
    payload: DoctorProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
):
    doctor = get_current_doctor(request, db, session_service)
    doctor.full_name = payload.full_name.strip()
    doctor.registration_number = payload.registration_number.strip()
    doctor.clinic_name = payload.clinic_name.strip()
    doctor.clinic_address = payload.clinic_address.strip()
    db.commit()
    db.refresh(doctor)
    record_audit(db, doctor.id, "profile_update", request)
    return doctor_to_profile(doctor)
