"""
AI-Powered Resume Screener - Backend API
Flask + MongoDB + Sentence Transformers
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
load_dotenv()
import os
import uuid
import json
from datetime import datetime

from database.db import get_db
from services.resume_parser import parse_resume
from services.jd_analyzer import analyze_job_description
from services.scorer import score_resume
from services.skill_extractor import extract_skills

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


CORS(app, origins=[
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", "https://resume-screener.vercel.app")
])

# ─────────────────────────────────────────
# JOB DESCRIPTION
# ─────────────────────────────────────────
@app.route("/api/job", methods=["POST"])
def create_job():
    """Create a new job posting and extract required skills."""
    data = request.json
    title       = data.get("title", "").strip()
    description = data.get("description", "").strip()
    company     = data.get("company", "").strip()

    if not title or not description:
        return jsonify({"error": "title and description are required"}), 400

    required_skills, keywords = analyze_job_description(description)

    job_doc = {
        "_id":             str(uuid.uuid4()),
        "title":           title,
        "company":         company,
        "description":     description,
        "required_skills": required_skills,
        "keywords":        keywords,
        "created_at":      datetime.utcnow().isoformat(),
    }

    db = get_db()
    db["jobs"].insert_one(job_doc)
    return jsonify({"job_id": job_doc["_id"], "required_skills": required_skills, "keywords": keywords}), 201


@app.route("/api/job/<job_id>", methods=["GET"])
def get_job(job_id):
    db = get_db()
    job = db["jobs"].find_one({"_id": job_id}, {"_id": 0})
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    db = get_db()
    jobs = list(db["jobs"].find({}, {"_id": 1, "title": 1, "company": 1, "created_at": 1}))
    return jsonify(jobs)


# ─────────────────────────────────────────
# RESUME UPLOAD & SCREENING
# ─────────────────────────────────────────
@app.route("/api/screen", methods=["POST"])
def screen_resume():
    """
    Upload one or more resumes and screen them against a job.
    Accepts: multipart/form-data with fields:
      - job_id (string)
      - resumes (files, multiple allowed)
    """
    job_id = request.form.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400

    db = get_db()
    job = db["jobs"].find_one({"_id": job_id})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    files = request.files.getlist("resumes")
    if not files:
        return jsonify({"error": "No resume files uploaded"}), 400

    results = []
    for file in files:
        resume_id   = str(uuid.uuid4())
        file_path   = os.path.join(UPLOAD_FOLDER, resume_id + "_" + file.filename)
        file.save(file_path)

        # Parse resume text
        resume_data = parse_resume(file_path)

        # Extract candidate skills
        candidate_skills = extract_skills(resume_data["text"])

        # Score against JD
        scores = score_resume(
            resume_text     = resume_data["text"],
            jd_text         = job["description"],
            required_skills = job["required_skills"],
            candidate_skills= candidate_skills,
        )

        result_doc = {
            "_id":             resume_id,
            "job_id":          job_id,
            "filename":        file.filename,
            "candidate_name":  resume_data.get("name", "Unknown"),
            "email":           resume_data.get("email", ""),
            "phone":           resume_data.get("phone", ""),
            "education":       resume_data.get("education", []),
            "experience_years":resume_data.get("experience_years", 0),
            "candidate_skills":candidate_skills,
            "matched_skills":  scores["matched_skills"],
            "missing_skills":  scores["missing_skills"],
            "semantic_score":  scores["semantic_score"],
            "skill_score":     scores["skill_score"],
            "experience_score":scores["experience_score"],
            "final_score":     scores["final_score"],
            "grade":           scores["grade"],
            "explanation":     scores["explanation"],
            "screened_at":     datetime.utcnow().isoformat(),
        }

        db["results"].insert_one(result_doc)
        results.append(result_doc)

        # Clean up file
        os.remove(file_path)

    # Sort by final_score descending
    results.sort(key=lambda x: x["final_score"], reverse=True)

    return jsonify({"job_id": job_id, "screened": len(results), "results": results}), 200


# ─────────────────────────────────────────
# RESULTS & RANKING
# ─────────────────────────────────────────
@app.route("/api/results/<job_id>", methods=["GET"])
def get_results(job_id):
    """Get ranked results for a job."""
    db = get_db()
    results = list(
        db["results"]
        .find({"job_id": job_id}, {"_id": 0})
        .sort("final_score", -1)
    )
    return jsonify({"job_id": job_id, "total": len(results), "results": results})


@app.route("/api/result/<result_id>", methods=["GET"])
def get_result(result_id):
    db = get_db()
    result = db["results"].find_one({"_id": result_id}, {"_id": 0})
    if not result:
        return jsonify({"error": "Result not found"}), 404
    return jsonify(result)


@app.route("/api/results/<job_id>/top", methods=["GET"])
def get_top_candidates(job_id):
    """Get top N candidates for a job."""
    n  = int(request.args.get("n", 5))
    db = get_db()
    results = list(
        db["results"]
        .find({"job_id": job_id}, {"_id": 0})
        .sort("final_score", -1)
        .limit(n)
    )
    return jsonify({"job_id": job_id, "top_n": n, "results": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
