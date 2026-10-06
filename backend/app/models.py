import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    mobile: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(256), default="")
    registration_number: Mapped[str] = mapped_column(String(128), default="")
    clinic_name: Mapped[str] = mapped_column(String(256), default="")
    clinic_address: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    letters: Mapped[list["Letter"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
    drafts: Mapped[list["LetterDraft"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")


class Letter(Base):
    __tablename__ = "letters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctors.id"), index=True, nullable=False)
    template_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    template_label: Mapped[str] = mapped_column(String(128), nullable=False)
    patient_name: Mapped[str] = mapped_column(String(256), default="")
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    doctor: Mapped["Doctor"] = relationship(back_populates="letters")


class LetterDraft(Base):
    __tablename__ = "letter_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctors.id"), index=True, nullable=False)
    template_slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    patient_name: Mapped[str] = mapped_column(String(256), default="")
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor: Mapped["Doctor"] = relationship(back_populates="drafts")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctors.id"), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    letter_id: Mapped[str] = mapped_column(String(36), default="")
    detail: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    doctor: Mapped["Doctor"] = relationship(back_populates="audit_events")
