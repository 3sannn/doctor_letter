from app.models import Doctor
from app.schemas import DoctorProfile


def doctor_to_profile(doctor: Doctor) -> DoctorProfile:
    return DoctorProfile(
        mobile=doctor.mobile,
        full_name=doctor.full_name or "",
        registration_number=doctor.registration_number or "",
        clinic_name=doctor.clinic_name or "",
        clinic_address=doctor.clinic_address or "",
    )
