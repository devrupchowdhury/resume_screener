"""
services/scorer.py
Lightweight multi-dimensional resume scoring engine.
Uses TF-IDF cosine similarity instead of sentence-transformers
to stay within Render free tier 512MB RAM limit.

Score components (weighted):
  40% - Text similarity     (TF-IDF cosine similarity)
  35% - Skill match ratio   (required_skills intersection candidate_skills)
  25% - Experience score    (years of experience vs JD expectation)
"""

from __future__ import annotations
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ── Experience extraction ─────────────────────────────────────
_EXP_RE = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)",
    re.IGNORECASE,
)


def _parse_required_experience(jd_text: str) -> float:
    matches = _EXP_RE.findall(jd_text)
    if matches:
        return float(min(matches))
    return 0.0


def _experience_score(candidate_years: float, required_years: float) -> float:
    if required_years <= 0:
        return 75.0
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
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    if score >= 35: return "D"
    return "F"


def _tfidf_similarity(text1: str, text2: str) -> float:
    """Compute cosine similarity between two texts using TF-IDF."""
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
        tfidf_matrix = vectorizer.fit_transform([text1[:3000], text2[:3000]])
        score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        return round(score * 100, 2)
    except Exception:
        return 50.0


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
        f"  Semantic Similarity  : {semantic:.1f}/100  (40% weight)",
        f"  Skill Match          : {skill:.1f}/100  (35% weight)",
        f"  Experience           : {exp:.1f}/100  (25% weight)",
        "",
    ]
    if matched:
        lines.append(f"Matched Skills ({len(matched)}): {', '.join(matched[:10])}")
    if missing:
        lines.append(f"Missing Skills ({len(missing)}): {', '.join(missing[:10])}")

    if grade == "A":
        lines.append("\nVerdict: Excellent match -- highly recommended for interview.")
    elif grade == "B":
        lines.append("\nVerdict: Good match -- worth considering.")
    elif grade == "C":
        lines.append("\nVerdict: Partial match -- may need additional screening.")
    else:
        lines.append("\nVerdict: Weak match -- does not meet core requirements.")

    return "\n".join(lines)


def score_resume(
    resume_text: str,
    jd_text: str,
    required_skills: list,
    candidate_skills: list,
    candidate_exp_years: float = 0.0,
) -> dict:
    # 1. Text similarity via TF-IDF
    semantic_score = _tfidf_similarity(resume_text, jd_text)

    # 2. Skill match
    req_set  = set(s.lower() for s in required_skills)
    cand_set = set(s.lower() for s in candidate_skills)
    matched  = sorted(req_set & cand_set)
    missing  = sorted(req_set - cand_set)
    skill_score = round((len(matched) / len(req_set) * 100) if req_set else 75.0, 2)

    # 3. Experience score
    required_exp = _parse_required_experience(jd_text)
    exp_score    = _experience_score(candidate_exp_years, required_exp)

    # 4. Weighted final score
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
