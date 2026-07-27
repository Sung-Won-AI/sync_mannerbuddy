import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MaskingResult:
    masked_text: str
    replacements: dict[str, str]


class MaskingService:
    _patterns = (
        (
            "EMAIL",
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        ),
        (
            "PHONE",
            re.compile(
                r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?"
                r"(?:\(?\d{2,4}\)?[-.\s]?)\d{3,4}[-.\s]?\d{4}(?!\d)"
            ),
        ),
        (
            "MONEY",
            re.compile(
                r"(?<!\w)(?:[$€£¥₩]\s?[\d,]+(?:\.\d{1,2})?"
                r"|[\d,]+(?:\.\d{1,2})?\s?(?:USD|EUR|KRW|JPY|CNY))(?!\w)",
                re.IGNORECASE,
            ),
        ),
    )

    def mask(self, text: str) -> MaskingResult:
        masked_text = text
        replacements: dict[str, str] = {}

        for label, pattern in self._patterns:
            counter = 0

            def replace(match: re.Match[str]) -> str:
                nonlocal counter
                counter += 1
                token = f"[{label}_{counter}]"
                replacements[token] = match.group(0)
                return token

            masked_text = pattern.sub(replace, masked_text)

        return MaskingResult(
            masked_text=masked_text,
            replacements=replacements,
        )

    def restore(self, text: str, replacements: dict[str, str]) -> str:
        restored = text
        for token, original in replacements.items():
            restored = restored.replace(token, original)
        return restored


masking_service = MaskingService()
