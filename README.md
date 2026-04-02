# AI-Powered Resume Screener
**B.Tech Final Year Project | Computer Science | 2025-26**

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Database
Make sure MongoDB is running on localhost:27017 before starting the backend.

## Project Structure
```
resume_screener/
├── backend/
│   ├── app.py                  # Flask REST API
│   ├── requirements.txt
│   ├── database/
│   │   ├── db.py               # MongoDB connection + indexes
│   │   └── schema.py           # Collection schema reference
│   └── services/
│       ├── resume_parser.py    # PDF/DOCX text extraction
│       ├── jd_analyzer.py      # Job description skill extraction
│       ├── skill_extractor.py  # Resume skill matching
│       └── scorer.py           # Multi-dimensional scoring engine
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Full React dashboard
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
└── docs/
    └── Resume_Screener_Documentation.docx
```

## Scoring
| Component | Weight | Method |
|---|---|---|
| Semantic Similarity | 40% | all-MiniLM-L6-v2 cosine similarity |
| Skill Match | 35% | Set intersection of skill dictionaries |
| Experience | 25% | Years gap scoring |

Final Score → Grade A (≥80) / B (≥65) / C (≥50) / D (≥35) / F (<35)
