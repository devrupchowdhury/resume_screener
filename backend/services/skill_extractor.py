"""
services/skill_extractor.py
Extracts skills from resume text using the same dictionary + spaCy NER fallback.
"""

import re
from services.jd_analyzer import TECH_SKILLS


def extract_skills(resume_text: str) -> list:
    """
    Returns a list of skills found in the resume text.
    Matches against the shared TECH_SKILLS dictionary (case-insensitive).
    """
    lower  = resume_text.lower()
    found  = []

    for skill in sorted(TECH_SKILLS, key=len, reverse=True):
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, lower):
            found.append(skill)

    # Deduplicate while preserving order
    seen   = set()
    unique = []
    for s in found:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique
