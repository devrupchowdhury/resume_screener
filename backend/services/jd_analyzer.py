"""
services/jd_analyzer.py
Extracts required skills and keywords from a Job Description.
"""

import re
from collections import Counter

# ── Comprehensive tech skill dictionary ──────────────────────
TECH_SKILLS = {
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "kotlin", "swift", "ruby", "php", "scala", "r", "matlab", "dart",
    # Web
    "react", "angular", "vue", "next.js", "node.js", "express", "django",
    "flask", "fastapi", "spring boot", "asp.net", "html", "css", "tailwind",
    # Data / ML
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "matplotlib", "seaborn", "opencv", "hugging face", "transformers",
    "bert", "gpt", "llm", "rag", "langchain",
    # Data Engineering
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "cassandra", "sqlite", "oracle", "dynamodb",
    "spark", "hadoop", "kafka", "airflow", "dbt", "snowflake",
    # DevOps / Cloud
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
    "jenkins", "ci/cd", "github actions", "linux", "bash",
    # Tools
    "git", "github", "jira", "agile", "scrum", "rest api", "graphql",
    "microservices", "system design",
    # Soft skills
    "communication", "teamwork", "leadership", "problem solving",
    "analytical", "project management",
}

STOP_WORDS = {
    "the", "and", "for", "with", "that", "this", "will", "have",
    "are", "you", "our", "your", "from", "into", "using", "work",
    "experience", "required", "preferred", "must", "good", "strong",
    "ability", "skills", "knowledge", "understanding",
}


def analyze_job_description(jd_text: str):
    """
    Returns:
      required_skills : list of matched skill keywords
      keywords        : list of high-frequency important words
    """
    lower = jd_text.lower()

    # ── 1. Skill matching ─────────────────────────────────────
    required_skills = []
    for skill in sorted(TECH_SKILLS, key=len, reverse=True):   # long skills first
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, lower):
            required_skills.append(skill)

    # ── 2. Keyword frequency ─────────────────────────────────
    tokens  = re.findall(r"\b[a-z][a-z+#.\-]{2,}\b", lower)
    counts  = Counter(t for t in tokens if t not in STOP_WORDS)
    keywords = [w for w, _ in counts.most_common(20) if w not in required_skills]

    return required_skills, keywords[:15]
