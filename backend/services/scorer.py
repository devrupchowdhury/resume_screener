"""
services/scorer.py
Memory-efficient scoring engine for Render free tier.
Loads all-MiniLM-L6-v2 ONCE at startup in background thread.
Falls back to TF-IDF if model fails to load.
"""

from __future__ import annotations
import re
import threading
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# ── Load model ONCE at startup ────────────────────────────────
_model = None
_model_lock = threading.Lock()

def _get_model():
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is None:
            try:
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer(
                    "all-MiniLM-L6-v2",
                    cache_folder="/tmp/st_cache",
                )
                print("[scorer] Transformer model loaded OK")
            except Exception as e:
                print(f"[scorer] Model load failed, using TF-IDF: {e}")
                _model = "tfidf"
    return _model

# Pre-load in background when gunicorn starts
threading.Thread(target=_get_model, daemon=True).start()


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


# ── Semantic similarity ───────────────────────────────────────
def _semantic_similarity(text1: str, text2: str) -> float:
    model = _get_model()
    if model != "tfidf":
        try:
            e1 = model.encode([text1[:512]], convert_to_numpy=True)
            e2 = model.encode([text2[:512]], convert_to_numpy=True)
            return round(float(cosine_similarity(e1, e2)[0][0]) * 100, 2)
        except Exception as e:
            print(f"[scorer] Inference failed: {e}")
    # TF-IDF fallback
    try:
        vec = TfidfVectorizer(stop_words="english", max_features=500)
        mat = vec.fit_transform([text1[:2000], text2[:2000]])
        return round(float(cosine_similarity(mat[0:1], mat[1:2])[0][0]) * 100, 2)
    except Exception:
        return 50.0


# ── Explanation ───────────────────────────────────────────────
def _build_explanation(sem, skill, exp, final, matched, missing, grade):
    lines = [
        f"Overall Score: {final:.1f}/100 (Grade {grade})",
        "",
        "Score Breakdown:",
        f"  Semantic Similarity  : {sem:.1f}/100  (40% weight)",
        f"  Skill Match          : {skill:.1f}/100  (35% weight)",
        f"  Experience           : {exp:.1f}/100  (25% weight)",
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

    semantic_score = _semantic_similarity(resume_text, jd_text)

    req_set    = set(s.lower() for s in required_skills)
    cand_set   = set(s.lower() for s in candidate_skills)
    matched    = sorted(req_set & cand_set)
    missing    = sorted(req_set - cand_set)
    skill_score = round(
        (len(matched) / len(req_set) * 100) if req_set else 75.0, 2
    )

    required_exp = _parse_required_experience(jd_text)
    exp_score    = _experience_score(candidate_exp_years, required_exp)

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
