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
    group: str = "clinical"


TEMPLATES: tuple[LetterTemplate, ...] = (
    LetterTemplate(
        slug="blank-letter",
        label="Blank letter",
        description="Your letterhead only. Write the full letter yourself in the editor.",
        filename="blank.html",
        group="custom",
    ),
    LetterTemplate(
        slug="referral-letter",
        label="Referral letter",
        description="Refer a patient to a colleague or specialist with clinical context.",
        filename="referral.html",
        group="clinical",
    ),
    LetterTemplate(
        slug="follow-up-letter",
        label="Follow-up letter",
        description="Summarise the visit and next steps for the patient.",
        filename="follow_up.html",
        group="clinical",
    ),
    LetterTemplate(
        slug="discharge-summary",
        label="Discharge summary",
        description="Handover summary after admission or a procedure.",
        filename="discharge_summary.html",
        group="clinical",
    ),
    LetterTemplate(
        slug="thank-you-letter",
        label="Thank you letter",
        description="A short note of thanks to a patient or colleague.",
        filename="thank_you.html",
        group="general",
    ),
    LetterTemplate(
        slug="medical-certificate",
        label="Medical certificate",
        description="Fitness, rest, or return-to-work wording.",
        filename="medical_certificate.html",
        group="certificates",
    ),
    LetterTemplate(
        slug="sick-leave-note",
        label="Sick leave note",
        description="Recommend time away from work with clinical reason.",
        filename="sick_leave.html",
        group="certificates",
    ),
    LetterTemplate(
        slug="fitness-for-duty",
        label="Fitness for duty",
        description="Confirm whether a patient may resume work or duties.",
        filename="fitness_for_duty.html",
        group="certificates",
    ),
    LetterTemplate(
        slug="procedure-consent",
        label="Procedure consent",
        description="Document that risks and consent were explained.",
        filename="procedure_consent.html",
        group="clinical",
    ),
    LetterTemplate(
        slug="records-request",
        label="Records request",
        description="Request files from another hospital or clinic.",
        filename="records_request.html",
        group="administrative",
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
    clinic_name = (doctor.clinic_name if doctor and doctor.clinic_name else "Clinic name").strip()
    clinic_address = (doctor.clinic_address if doctor and doctor.clinic_address else "Clinic address").strip()
    replacements = {
        "{{date}}": today,
        "{{doctor_name}}": doctor_name,
        "{{patient_name}}": "Patient Name",
        "{{diagnosis}}": "Brief clinical summary",
        "{{registration_number}}": registration,
        "{{clinic_name}}": clinic_name,
        "{{clinic_address}}": clinic_address,
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
