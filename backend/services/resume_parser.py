"""
services/resume_parser.py
Extracts structured data from PDF/DOCX resumes.
"""

import re
import pdfplumber
import docx2txt
from pathlib import Path


# ── Regex patterns ────────────────────────────────────────────
EMAIL_RE    = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE    = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
NAME_RE     = re.compile(r"^([A-Z][a-z]+(?: [A-Z][a-z]+)+)", re.MULTILINE)

EDUCATION_KEYWORDS = [
    "b.tech", "m.tech", "b.e.", "m.e.", "bsc", "msc", "mba",
    "bachelor", "master", "phd", "doctorate", "engineering",
    "computer science", "information technology",
]

EXPERIENCE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:\+\s*)?(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp\.?)",
    re.IGNORECASE,
)

SECTION_HEADERS = [
    "education", "experience", "skills", "projects",
    "certifications", "summary", "objective", "achievements",
]


def parse_resume(file_path: str) -> dict:
    """Parse a resume file and return structured data."""
    path = Path(file_path)
    ext  = path.suffix.lower()

    if ext == ".pdf":
        text = _extract_pdf(file_path)
    elif ext in (".docx", ".doc"):
        text = docx2txt.process(file_path)
    elif ext == ".txt":
        text = path.read_text(encoding="utf-8", errors="ignore")
    else:
        text = ""

    return {
        "text":             text,
        "name":             _extract_name(text),
        "email":            _extract_email(text),
        "phone":            _extract_phone(text),
        "education":        _extract_education(text),
        "experience_years": _extract_experience_years(text),
        "sections":         _extract_sections(text),
    }


# ── Private helpers ───────────────────────────────────────────

def _extract_pdf(file_path: str) -> str:
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n".join(pages)


def _extract_name(text: str) -> str:
    """Heuristic: first line that looks like a proper name."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:5]:
        if NAME_RE.match(line) and len(line.split()) <= 4:
            return line
    return "Unknown"


def _extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    match = PHONE_RE.search(text)
    return match.group(0).strip() if match else ""


def _extract_education(text: str) -> list:
    lower = text.lower()
    found = []
    for kw in EDUCATION_KEYWORDS:
        if kw in lower:
            found.append(kw.upper())
    return list(dict.fromkeys(found))  # deduplicate preserving order


def _extract_experience_years(text: str) -> float:
    """Extract total years of experience mentioned in resume."""
    matches = EXPERIENCE_RE.findall(text)
    if matches:
        return max(float(m) for m in matches)
    # Fallback: count year ranges like "2019 – 2022"
    year_range_re = re.compile(r"(20\d{2})\s*[-–—to]+\s*(20\d{2}|present|current)", re.IGNORECASE)
    ranges = year_range_re.findall(text)
    total  = 0.0
    import datetime
    cur_year = datetime.datetime.now().year
    for start, end in ranges:
        try:
            s = int(start)
            e = cur_year if end.lower() in ("present", "current") else int(end)
            total += max(0, e - s)
        except ValueError:
            pass
    return round(total, 1)


def _extract_sections(text: str) -> dict:
    """Split resume into labelled sections."""
    sections = {}
    lines    = text.splitlines()
    current  = "header"
    buf      = []

    for line in lines:
        stripped = line.strip().lower()
        if stripped in SECTION_HEADERS:
            sections[current] = "\n".join(buf).strip()
            current = stripped
            buf     = []
        else:
            buf.append(line)

    sections[current] = "\n".join(buf).strip()
    return sections
