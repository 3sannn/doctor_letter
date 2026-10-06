from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SessionCreate(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=15)

    @field_validator("mobile")
    @classmethod
    def normalize_mobile(cls, value: str) -> str:
        digits = "".join(ch for ch in value.strip() if ch.isdigit())
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("Enter a valid mobile number.")
        return digits


class SessionResponse(BaseModel):
    mobile: str
    message: str = "You are signed in."


class DoctorProfile(BaseModel):
    mobile: str
    full_name: str = ""
    registration_number: str = ""
    clinic_name: str = ""
    clinic_address: str = ""


class DoctorProfileUpdate(BaseModel):
    full_name: str = Field(default="", max_length=256)
    registration_number: str = Field(default="", max_length=128)
    clinic_name: str = Field(default="", max_length=256)
    clinic_address: str = Field(default="", max_length=512)


class TemplateSummary(BaseModel):
    slug: str
    label: str
    description: str


class TemplateDetail(TemplateSummary):
    html: str


class LetterFinalize(BaseModel):
    template_slug: str
    html_content: str = Field(..., min_length=20)
    patient_name: Optional[str] = Field(default="", max_length=256)
    draft_id: Optional[str] = None


class LetterPreviewRequest(BaseModel):
    template_slug: str
    html_content: str = Field(..., min_length=20)


class LetterPreviewResponse(BaseModel):
    pdf_base64: str


class LetterSummary(BaseModel):
    id: str
    template_slug: str
    template_label: str
    patient_name: str
    created_at: datetime


class LetterDownload(BaseModel):
    url: str
    expires_in_seconds: int


class DraftSummary(BaseModel):
    id: str
    template_slug: str
    patient_name: str
    updated_at: datetime


class DraftDetail(DraftSummary):
    html_content: str


class DraftSave(BaseModel):
    template_slug: str
    html_content: str = Field(..., min_length=1)
    patient_name: Optional[str] = Field(default="", max_length=256)


class MessageResponse(BaseModel):
    message: str
