"""
AI-Powered Resume Screener - Backend API
Flask + MongoDB + Sentence Transformers
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

# Load env
load_dotenv()

# Services
from database.db import get_db
from services.resume_parser import parse_resume
from services.jd_analyzer import analyze_job_description
from services.scorer import score_resume
from services.skill_extractor import extract_skills

# ─────────────────────────────────────────
# APP CONFIG
# ─────────────────────────────────────────
app = Flask(__name__)

# ✅ Single CORS config (fixed)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ✅ File size limit (5MB)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "API is running 🚀"})

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    })

# ─────────────────────────────────────────
# JOB DESCRIPTION
# ─────────────────────────────────────────
@app.route("/api/job", methods=["POST"])
def create_job():
    try:
        data = request.json
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        company = data.get("company", "").strip()

        if not title or not description:
            return jsonify({"error": "title and description are required"}), 400

        required_skills, keywords = analyze_job_description(description)

        job_doc = {
            "_id": str(uuid.uuid4()),
            "title": title,
            "company": company,
            "description": description,
            "required_skills": required_skills,
            "keywords": keywords,
            "created_at": datetime.utcnow().isoformat(),
        }

        db = get_db()
        db["jobs"].insert_one(job_doc)

        return jsonify({
            "job_id": job_doc["_id"],
            "required_skills": required_skills,
            "keywords": keywords
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    jobs = list(db["jobs"].find({}, {
        "_id": 1,
        "title": 1,
        "company": 1,
        "created_at": 1
    }))
    return jsonify(jobs)

# ─────────────────────────────────────────
# RESUME SCREENING
# ─────────────────────────────────────────
@app.route("/api/screen", methods=["POST"])
def screen_resume():
    try:
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
            try:
                resume_id = str(uuid.uuid4())
                file_path = os.path.join(
                    UPLOAD_FOLDER,
                    f"{resume_id}_{file.filename}"
                )

                file.save(file_path)

                # Parse resume
                resume_data = parse_resume(file_path)

                # Extract skills
                candidate_skills = extract_skills(resume_data.get("text", ""))

                # Score resume
                scores = score_resume(
                    resume_text=resume_data.get("text", ""),
                    jd_text=job["description"],
                    required_skills=job["required_skills"],
                    candidate_skills=candidate_skills,
                )

                result_doc = {
                    "_id": resume_id,
                    "job_id": job_id,
                    "filename": file.filename,
                    "candidate_name": resume_data.get("name", "Unknown"),
                    "email": resume_data.get("email", ""),
                    "phone": resume_data.get("phone", ""),
                    "education": resume_data.get("education", []),
                    "experience_years": resume_data.get("experience_years", 0),
                    "candidate_skills": candidate_skills,
                    "matched_skills": scores.get("matched_skills", []),
                    "missing_skills": scores.get("missing_skills", []),
                    "semantic_score": scores.get("semantic_score", 0),
                    "skill_score": scores.get("skill_score", 0),
                    "experience_score": scores.get("experience_score", 0),
                    "final_score": scores.get("final_score", 0),
                    "grade": scores.get("grade", ""),
                    "explanation": scores.get("explanation", ""),
                    "screened_at": datetime.utcnow().isoformat(),
                }

                db["results"].insert_one(result_doc)
                results.append(result_doc)

                # Cleanup
                os.remove(file_path)

            except Exception as file_error:
                results.append({
                    "filename": file.filename,
                    "error": str(file_error)
                })

        # Sort results
        results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        return jsonify({
            "job_id": job_id,
            "screened": len(results),
            "results": results
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────
@app.route("/api/results/<job_id>", methods=["GET"])
def get_results(job_id):
    db = get_db()
    results = list(
        db["results"]
        .find({"job_id": job_id}, {"_id": 0})
        .sort("final_score", -1)
    )

    return jsonify({
        "job_id": job_id,
        "total": len(results),
        "results": results
    })


@app.route("/api/result/<result_id>", methods=["GET"])
def get_result(result_id):
    db = get_db()
    result = db["results"].find_one({"_id": result_id}, {"_id": 0})

    if not result:
        return jsonify({"error": "Result not found"}), 404

    return jsonify(result)


@app.route("/api/results/<job_id>/top", methods=["GET"])
def get_top_candidates(job_id):
    n = int(request.args.get("n", 5))

    db = get_db()
    results = list(
        db["results"]
        .find({"job_id": job_id}, {"_id": 0})
        .sort("final_score", -1)
        .limit(n)
    )

    return jsonify({
        "job_id": job_id,
        "top_n": n,
        "results": results
    })


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)