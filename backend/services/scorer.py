"""
services/scorer.py
Lightweight scoring engine - TF-IDF only.
Uses only ~50MB RAM, works perfectly on Render free tier.
No sentence-transformers, no torch, no heavy models.
"""

from __future__ import annotations
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ── Experience helpers ────────────────────────────────────────
_EXP_RE = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)",
    re.IGNORECASE,
)

def _parse_required_experience(jd_text: str) -> float:
    matches = _EXP_RE.findall(jd_text)
    return float(min(matches)) if matches else 0.0

def _experience_score(candidate_years: float, required_years: float) -> float:
    if required_years <= 0: return 75.0
    gap = required_years - candidate_years
    if gap <= 0:   return 100.0
    elif gap <= 1: return 70.0
    elif gap <= 2: return 40.0
    else:          return 10.0

def _grade(score: float) -> str:
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    if score >= 35: return "D"
    return "F"


# ── TF-IDF similarity ─────────────────────────────────────────
def _text_similarity(text1: str, text2: str) -> float:
    """
    Compute similarity using TF-IDF + cosine similarity.
    Boosted by 1.35x to compensate for lower raw TF-IDF scores
    and align with semantic similarity ranges.
    """
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=1000,
            ngram_range=(1, 2),   # bigrams improve accuracy
        )
        matrix = vectorizer.fit_transform([
            text1[:3000],
            text2[:3000],
        ])
        raw = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        # Boost score to realistic range (TF-IDF raw scores are low)
        boosted = min(raw * 1.35 * 100, 95.0)
        return round(boosted, 2)
    except Exception:
        return 50.0


# ── Explanation ───────────────────────────────────────────────
def _build_explanation(sem, skill, exp, final, matched, missing, grade):
    lines = [
        f"Overall Score: {final:.1f}/100 (Grade {grade})",
        "",
        "Score Breakdown:",
        f"  Text Similarity  : {sem:.1f}/100  (40% weight)",
        f"  Skill Match      : {skill:.1f}/100  (35% weight)",
        f"  Experience       : {exp:.1f}/100  (25% weight)",
        "",
    ]
    if matched:
        lines.append(f"Matched Skills ({len(matched)}): {', '.join(matched[:10])}")
    if missing:
        lines.append(f"Missing Skills ({len(missing)}): {', '.join(missing[:10])}")
    verdicts = {
        "A": "Excellent match -- highly recommended for interview.",
        "B": "Good match -- worth considering.",
        "C": "Partial match -- may need additional screening.",
        "D": "Weak match -- does not meet core requirements.",
        "F": "Poor match -- missing most requirements.",
    }
    lines.append(f"\nVerdict: {verdicts.get(grade, '')}")
    return "\n".join(lines)


# ── Main scoring function ─────────────────────────────────────
def score_resume(
    resume_text: str,
    jd_text: str,
    required_skills: list,
    candidate_skills: list,
    candidate_exp_years: float = 0.0,
) -> dict:

    # 1. Text similarity
    semantic_score = _text_similarity(resume_text, jd_text)

    # 2. Skill match
    req_set    = set(s.lower() for s in required_skills)
    cand_set   = set(s.lower() for s in candidate_skills)
    matched    = sorted(req_set & cand_set)
    missing    = sorted(req_set - cand_set)
    skill_score = round(
        (len(matched) / len(req_set) * 100) if req_set else 75.0, 2
    )

    # 3. Experience
    required_exp = _parse_required_experience(jd_text)
    exp_score    = _experience_score(candidate_exp_years, required_exp)

    # 4. Weighted final
    final_score = round(
        0.40 * semantic_score +
        0.35 * skill_score +
        0.25 * exp_score,
        2,
    )

    grade       = _grade(final_score)
    explanation = _build_explanation(
        semantic_score, skill_score, exp_score,
        final_score, matched, missing, grade,
    )

    return {
        "semantic_score":   semantic_score,
        "skill_score":      skill_score,
        "experience_score": exp_score,
        "final_score":      final_score,
        "grade":            grade,
        "matched_skills":   matched,
        "missing_skills":   missing,
        "explanation":      explanation,
    }
