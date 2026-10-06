from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.models import Doctor


@dataclass(frozen=True)
class LetterTemplate:
    slug: str
    label: str
    description: str
    filename: str


TEMPLATES: tuple[LetterTemplate, ...] = (
    LetterTemplate(
        slug="referral-letter",
        label="Referral Letter",
        description="Refer a patient to a specialist with clinical context.",
        filename="referral.html",
    ),
    LetterTemplate(
        slug="thank-you-letter",
        label="Thank You Letter",
        description="Send a thoughtful note of appreciation to a patient or colleague.",
        filename="thank_you.html",
    ),
    LetterTemplate(
        slug="medical-certificate",
        label="Medical Certificate",
        description="Document fitness, rest, or return-to-work guidance.",
        filename="medical_certificate.html",
    ),
)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "letter_templates"


def list_templates() -> list[LetterTemplate]:
    return list(TEMPLATES)


def get_template(slug: str) -> LetterTemplate | None:
    for item in TEMPLATES:
        if item.slug == slug:
            return item
    return None


def hydrate_placeholders(html: str, doctor: Doctor | None = None) -> str:
    today = date.today().strftime("%d %B %Y")
    doctor_name = (doctor.full_name if doctor and doctor.full_name else "Your Name").strip()
    registration = (
        doctor.registration_number if doctor and doctor.registration_number else "Registration number"
    ).strip()
    replacements = {
        "{{date}}": today,
        "{{doctor_name}}": doctor_name,
        "{{patient_name}}": "Patient Name",
        "{{diagnosis}}": "Brief clinical summary",
        "{{registration_number}}": registration,
        "{{rest_or_fitness_note}}": "Rest / fitness guidance for the patient.",
    }
    result = html
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def load_template_html(slug: str, doctor: Doctor | None = None) -> str | None:
    template = get_template(slug)
    if not template:
        return None
    path = _TEMPLATE_DIR / template.filename
    if not path.is_file():
        return None
    return hydrate_placeholders(path.read_text(encoding="utf-8"), doctor)
