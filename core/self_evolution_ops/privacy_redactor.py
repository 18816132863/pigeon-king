from __future__ import annotations

import re
from typing import Dict
from .schemas import RedactionReport, PrivacyLevel, new_id


class PrivacyRedactor:
    """V111: privacy scanner and redaction vault."""

    PATTERNS = {
        "api_key": re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}"),
        "phone": re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)"),
        "email": re.compile(r"[\w\.-]+@[\w\.-]+\.\w+"),
        "id_card": re.compile(r"(?<!\d)(\d{17}[\dXx])(?!\d)"),
        "bank_card": re.compile(r"(?<!\d)(\d{16,19})(?!\d)"),
    }

    def redact(self, text: str) -> RedactionReport:
        safe = text
        replacements: Dict[str, int] = {}
        for name, pat in self.PATTERNS.items():
            safe, count = pat.subn(f"[REDACTED_{name.upper()}]", safe)
            if count:
                replacements[name] = count

        if "api_key" in replacements or "bank_card" in replacements or "id_card" in replacements:
            level = PrivacyLevel.SECRET
        elif replacements:
            level = PrivacyLevel.SENSITIVE
        elif any(x in text for x in ["内部", "客户", "合同", "报价"]):
            level = PrivacyLevel.INTERNAL
        else:
            level = PrivacyLevel.PUBLIC

        return RedactionReport(
            id=new_id("redact"),
            privacy_level=level,
            original_length=len(text),
            redacted_length=len(safe),
            replacements=replacements,
            safe_text=safe,
        )
