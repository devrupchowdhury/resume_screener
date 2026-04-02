"""
database/schema.py
MongoDB Collection Schemas (for documentation / validation reference)

Collections:
  1. jobs    – One document per job posting
  2. results – One document per resume-job screening result
"""

# ── jobs ─────────────────────────────────────────────────────
JOB_SCHEMA = {
    "_id":             "string  (UUID v4)",
    "title":           "string  – Job title",
    "company":         "string  – Company name",
    "description":     "string  – Full JD text",
    "required_skills": "list    – Skills extracted from JD  e.g. ['python','flask']",
    "keywords":        "list    – High-frequency JD keywords",
    "created_at":      "string  (ISO 8601 UTC)",
}

# ── results ──────────────────────────────────────────────────
RESULT_SCHEMA = {
    "_id":              "string  (UUID v4)",
    "job_id":           "string  → jobs._id",
    "filename":         "string  – Original upload filename",
    "candidate_name":   "string",
    "email":            "string",
    "phone":            "string",
    "education":        "list    – Detected degree keywords",
    "experience_years": "float   – Inferred years of exp",
    "candidate_skills": "list    – Skills found in resume",
    "matched_skills":   "list    – required_skills ∩ candidate_skills",
    "missing_skills":   "list    – required_skills − candidate_skills",

    # Scores (0-100 each)
    "semantic_score":   "float   – Cosine similarity × 100",
    "skill_score":      "float   – Skill match ratio × 100",
    "experience_score": "float   – Experience adequacy 0/10/40/70/100",
    "final_score":      "float   – Weighted: 40×sem + 35×skill + 25×exp",
    "grade":            "string  – A/B/C/D/F",
    "explanation":      "string  – Human-readable breakdown",

    "screened_at":      "string  (ISO 8601 UTC)",
}

# ── Indexes ───────────────────────────────────────────────────
INDEXES = {
    "jobs":    ["created_at DESC", "title ASC"],
    "results": ["(job_id, final_score DESC)", "job_id ASC", "candidate_name ASC"],
}
