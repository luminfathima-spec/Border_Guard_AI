import re
from typing import Dict, Any, Tuple, Optional

class ReportInputSanitizer:
    """
    Guards the Report Generation Service against Indirect Prompt Injections (IPI)
    and adversarial command execution embedded in video filenames, camera labels,
    user remarks, or external telemetry metadata.
    """

    ADVERSARIAL_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|earlier|above)\s+instructions?", re.IGNORECASE),
        re.compile(r"disregard\s+(all\s+)?(previous|earlier|security)\s+(alerts?|instructions?|rules?)", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(an?\s+)?", re.IGNORECASE),
        re.compile(r"system\s*:\s*", re.IGNORECASE),
        re.compile(r"<\s*\|\s*im_start\s*\|\s*>", re.IGNORECASE),
        re.compile(r"<\s*\|\s*endoftext\s*\|\s*>", re.IGNORECASE),
        re.compile(r"\[\s*INST\s*\]", re.IGNORECASE),
        re.compile(r"<<\s*SYS\s*>>", re.IGNORECASE),
        re.compile(r"classify\s+all\s+(subjects?|targets?|people)\s+as\s+(friendly|authorized|safe|benign)", re.IGNORECASE),
        re.compile(r"(delete|drop|truncate|purge)\s+(all\s+)?(audit|records?|logs?|database)", re.IGNORECASE),
        re.compile(r"bypass\s+(all\s+)?(verification|security|safety)", re.IGNORECASE),
    ]

    CONTROL_DELIMITERS = [
        ("```json", "[code-block-json]"),
        ("```", "[code-block]"),
        ("---", " - "),
        ("<system>", "[system-tag]"),
        ("</system>", "[/system-tag]"),
    ]

    @classmethod
    def sanitize_text(cls, text: Optional[str]) -> Tuple[str, bool]:
        """
        Sanitizes text by neutralizing delimiters and stripping adversarial command patterns.
        Returns: (sanitized_text, injection_detected)
        """
        if not text:
            return "", False

        cleaned = str(text)
        injection_detected = False

        # 1. Detect adversarial patterns
        for pattern in cls.ADVERSARIAL_PATTERNS:
            if pattern.search(cleaned):
                injection_detected = True
                cleaned = pattern.sub("[DEFANGED_COMMAND]", cleaned)

        # 2. Defang markdown & syntax control delimiters
        for delim, replacement in cls.CONTROL_DELIMITERS:
            if delim in cleaned:
                cleaned = cleaned.replace(delim, replacement)

        return cleaned.strip(), injection_detected

    @classmethod
    def encapsulate_untrusted(cls, label: str, data: Any) -> Tuple[str, bool]:
        """
        Wraps data in rigid XML-style isolated boundaries with explicit untrusted metadata tagging.
        """
        raw_str = str(data) if data is not None else ""
        cleaned_str, detected = cls.sanitize_text(raw_str)
        wrapped = f'<untrusted_metadata field="{label}">\n{cleaned_str}\n</untrusted_metadata>'
        return wrapped, detected

    @classmethod
    def sanitize_incident_metadata(cls, metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Deep-sanitizes all text fields within an incident telemetry payload.
        Returns: (sanitized_dict, total_injections_deflected)
        """
        sanitized = {}
        deflections = 0

        for key, value in metadata.items():
            if isinstance(value, str):
                cleaned, detected = cls.sanitize_text(value)
                sanitized[key] = cleaned
                if detected:
                    deflections += 1
            elif isinstance(value, dict):
                sub_dict, sub_deflections = cls.sanitize_incident_metadata(value)
                sanitized[key] = sub_dict
                deflections += sub_deflections
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, str):
                        cleaned, detected = cls.sanitize_text(item)
                        new_list.append(cleaned)
                        if detected:
                            deflections += 1
                    elif isinstance(item, dict):
                        sub_dict, sub_deflections = cls.sanitize_incident_metadata(item)
                        new_list.append(sub_dict)
                        deflections += sub_deflections
                    else:
                        new_list.append(item)
                sanitized[key] = new_list
            else:
                sanitized[key] = value

        return sanitized, deflections
