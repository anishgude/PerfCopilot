from __future__ import annotations

import re

from app.schemas.benchmark import ParsedDiagnosis

SECTION_MAP = {
    "summary": "summary",
    "best-fit complexity": "best_fit_complexity",
    "regression bullets": "regression_bullets",
    "likely cause(s)": "likely_causes",
    "evidence": "evidence",
    "optimization direction": "optimization_direction",
    "risk/edge cases": "risks",
}


def _to_list(block: str) -> list[str]:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    cleaned: list[str] = []
    for line in lines:
        cleaned.append(re.sub(r"^(?:[-*]\s+|\d+\.\s+)", "", line).strip())
    return [line for line in cleaned if line]


def parse_diagnosis(text: str) -> ParsedDiagnosis | None:
    if not text.strip():
        return None

    sections: dict[str, list[str]] = {}
    current_heading: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched_heading = None
        for candidate in SECTION_MAP:
            prefix = f"{candidate}:"
            if line.lower().startswith(prefix):
                matched_heading = candidate
                current_heading = candidate
                sections.setdefault(candidate, [])
                remainder = line[len(prefix) :].strip()
                if remainder:
                    sections[candidate].append(remainder)
                break

        if matched_heading:
            continue

        if current_heading:
            sections.setdefault(current_heading, []).append(line)

    if not sections:
        return None

    diagnosis = ParsedDiagnosis()
    for heading, key in SECTION_MAP.items():
        block_lines = sections.get(heading)
        block = "\n".join(block_lines) if block_lines else ""
        if not block:
            continue
        if key in {"summary", "best_fit_complexity"}:
            setattr(
                diagnosis,
                key,
                " ".join(line.strip() for line in block.splitlines()).strip(),
            )
        else:
            setattr(diagnosis, key, _to_list(block))

    return diagnosis
