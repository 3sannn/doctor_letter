import re
from typing import Optional


def extract_patient_name(html: str) -> Optional[str]:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    patterns = [
        r"Patient(?:\'s)? Name[:\s]+([A-Za-z][A-Za-z\s\.\-]{1,80})",
        r"Re:\s*([A-Za-z][A-Za-z\s\.\-]{1,80})",
        r"Dear\s+([A-Za-z][A-Za-z\s\.\-]{1,80})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
