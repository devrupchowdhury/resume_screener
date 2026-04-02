"""
services/scorer.py
Multi-dimensional resume scoring engine.

Score components (weighted):
  40% — Semantic similarity  (sentence-transformers cosine similarity)
  35% — Skill match ratio    (required_skills ∩ candidate_skills)
  25% — Experience score     (years of experience vs JD expectation)

Combined score 0-100 → letter grade A/B/C/D/F
"""

from __future__ import annotations
import re
from typing import Optional

# Lazy-load the heavy model once
_model = None

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # all-MiniLM-L6-v2: fast, accurate, 90%+ on STS benchmarks
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


# ── Experience extraction helper ─────────────────────────────
_EXP_RE = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)", re.IGNORECASE
)

def _parse_required_experience(jd_text: str) -> float:
    """Extract the minimum required years of experience from JD."""
    matches = _EXP_RE.findall(jd_text)
    if matches:
        return float(min(matches))   # take lowest (minimum requirement)
    return 0.0


def _experience_score(candidate_years: float, required_years: float) -> float:
    """
    Returns 0-100.
    - Meets or exceeds: 100
    - Within 1 year short: 70
    - Within 2 years short: 40
    - More than 2 years short: 10
    """
    if required_years <= 0:
        return 75.0   # not specified → neutral
    gap = required_years - candidate_years
    if gap <= 0:
        return 100.0
    elif gap <= 1:
        return 70.0
    elif gap <= 2:
        return 40.0
    else:
        return 10.0


def _grade(score: float) -> str:
    if score >= 80:  return "A"
    if score >= 65:  return "B"
    if score >= 50:  return "C"
    if score >= 35:  return "D"
    return "F"


def _build_explanation(
    semantic: float,
    skill: float,
    exp: float,
    final: float,
    matched: list,
    missing: list,
    grade: str,
) -> str:
    lines = [
        f"Overall Score: {final:.1f}/100 (Grade {grade})",
        "",
        "Score Breakdown:",
        f"  • Semantic Similarity  : {semantic:.1f}/100  (40% weight)",
        f"  • Skill Match          : {skill:.1f}/100  (35% weight)",
        f"  • Experience           : {exp:.1f}/100  (25% weight)",
        "",
    ]
    if matched:
        lines.append(f"Matched Skills ({len(matched)}): {', '.join(matched[:10])}")
    if missing:
        lines.append(f"Missing Skills ({len(missing)}): {', '.join(missing[:10])}")

    if grade == "A":
        lines.append("\nVerdict: Excellent match — highly recommended for interview.")
    elif grade == "B":
        lines.append("\nVerdict: Good match — worth considering.")
    elif grade == "C":
        lines.append("\nVerdict: Partial match — may need additional screening.")
    else:
        lines.append("\nVerdict: Weak match — does not meet core requirements.")

    return "\n".join(lines)


# ── Main scoring function ─────────────────────────────────────

def score_resume(
    resume_text:      str,
    jd_text:          str,
    required_skills:  list,
    candidate_skills: list,
    candidate_exp_years: Optional[float] = None,
) -> dict:
    """
    Returns a dict with all scores and explanations.
    """

    # ── 1. Semantic similarity ────────────────────────────────
    model = _get_model()
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    emb_resume = model.encode([resume_text[:2000]])   # truncate to 2k chars
    emb_jd     = model.encode([jd_text[:2000]])
    cos_sim    = float(cosine_similarity(emb_resume, emb_jd)[0][0])
    semantic_score = round(cos_sim * 100, 2)

    # ── 2. Skill match ────────────────────────────────────────
    req_set  = set(s.lower() for s in required_skills)
    cand_set = set(s.lower() for s in candidate_skills)

    matched = sorted(req_set & cand_set)
    missing = sorted(req_set - cand_set)

    skill_score = round((len(matched) / len(req_set) * 100) if req_set else 75.0, 2)

    # ── 3. Experience score ───────────────────────────────────
    required_exp = _parse_required_experience(jd_text)
    exp_years    = candidate_exp_years if candidate_exp_years is not None else 0.0
    exp_score    = _experience_score(exp_years, required_exp)

    # ── 4. Weighted final score ───────────────────────────────
    final_score = round(
        0.40 * semantic_score +
        0.35 * skill_score    +
        0.25 * exp_score,
        2,
    )

    grade       = _grade(final_score)
    explanation = _build_explanation(
        semantic_score, skill_score, exp_score,
        final_score, matched, missing, grade,
    )

    return {
        "semantic_score":  semantic_score,
        "skill_score":     skill_score,
        "experience_score":exp_score,
        "final_score":     final_score,
        "grade":           grade,
        "matched_skills":  matched,
        "missing_skills":  missing,
        "explanation":     explanation,
    }
