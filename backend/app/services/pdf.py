import re
from html import escape

from app.services.letter_text import extract_patient_name


def wrap_letter_document(body_html: str, title: str) -> str:
    safe_title = escape(title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{safe_title}</title>
  <style>
    @page {{
      size: A4;
      margin: 2cm;
    }}
    body {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: 12pt;
      line-height: 1.55;
      color: #1a1a1a;
    }}
    h1, h2, h3 {{
      font-family: "Segoe UI", Arial, sans-serif;
      color: #0f172a;
    }}
    p {{
      margin: 0 0 0.75em 0;
    }}
  </style>
</head>
<body>
{body_html}
</body>
</html>"""


def render_pdf_bytes(html_document: str) -> bytes:
    from io import BytesIO

    from xhtml2pdf import pisa

    buffer = BytesIO()
    status = pisa.CreatePDF(html_document, dest=buffer, encoding="utf-8")
    if status.err:
        raise ValueError("Could not create the letter PDF. Please review the content and try again.")
    return buffer.getvalue()


def build_pdf_from_editor_html(html_content: str, template_label: str) -> bytes:
    document = wrap_letter_document(html_content, template_label)
    return render_pdf_bytes(document)


def guess_patient_name(html_content: str, provided: str) -> str:
    if provided and provided.strip():
        return provided.strip()[:256]
    extracted = extract_patient_name(html_content)
    if extracted:
        return extracted[:256]
    return "Patient"
