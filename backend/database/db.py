"""
database/db.py
MongoDB connection manager.
Collections:
  - jobs    : job postings
  - results : screening results per resume
"""

from pymongo import MongoClient, DESCENDING
import os

_client = None
_db     = None

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME",   "resume_screener")


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db     = _client[DB_NAME]
        _ensure_indexes(_db)
    return _db


def _ensure_indexes(db):
    """Create indexes for performance."""
    # jobs
    db["jobs"].create_index([("created_at", DESCENDING)])
    db["jobs"].create_index([("title", 1)])

    # results
    db["results"].create_index([("job_id", 1), ("final_score", DESCENDING)])
    db["results"].create_index([("job_id", 1)])
    db["results"].create_index([("candidate_name", 1)])
