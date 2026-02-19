# PharmaGuard

PharmaGuard is a full-stack pharmacogenomics platform that analyzes VCF files and generates CPIC-aligned drug–gene risk reports.

## Live Demo Link
- Frontend: https://pharmaguard-frontend.vercel.app

## LinkedIn Video Link
- Demo video: https://www.linkedin.com/ (replace with your project video URL)

## Architecture Overview
PharmaGuard follows a client–server architecture:

- Frontend (`React + Vite + Tailwind`)
  - VCF upload (drag-and-drop/file picker)
  - Drug selection (multi-select + optional free-text)
  - Color-coded risk results with copy/download JSON
- Backend (`FastAPI + SQLAlchemy + Pydantic`)
  - VCF validation/parsing
  - Pharmacogenomic interpretation engine
  - CPIC-aligned risk classification
  - Dual-layer explanation generation

High-level flow:
1. User uploads `.vcf` and selects one or more drugs.
2. Frontend submits to backend `/api/v1/analyze-vcf`.
3. Backend parses variants, maps phenotype/risk, and returns structured JSON.
4. Frontend renders risk assessment and export actions.

## Tech Stack
- Frontend: React, Vite, Tailwind CSS, React Router, React Icons
- Backend: FastAPI, Uvicorn, Pydantic, SQLAlchemy, python-jose, bcrypt
- Data/Storage: SQLite
- AI: OpenAI API (optional fallback-aware integration)
- Testing: pytest

## Installation Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### 1) Clone
```bash
git clone <your-repo-url>
cd Pharma
```

### 2) Backend setup
```bash
cd pharmaguard-backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Run backend:
```bash
python run_backend.py
```

Backend URLs:
- API base: `http://localhost:8000`
- Health: `http://localhost:8000/api/v1/health`
- Swagger: `http://localhost:8000/docs`

### 3) Frontend setup
```bash
cd ..\pharmaguard-frontend
npm install
npm run dev
```

Frontend URL:
- `http://localhost:3000` (or next available port shown by Vite)

## API Docs

### Primary endpoints
- `POST /api/v1/validate-vcf` — validates VCF file and returns structured validation result
- `POST /api/v1/analyze-vcf?drug=<DRUGS>` — analyzes uploaded VCF for one or more drugs
- `GET /api/v1/drugs` — returns supported medications metadata
- `GET /api/v1/health` — health check

Interactive API docs:
- `http://localhost:8000/docs`

## Usage Examples

### Analyze a VCF file (single drug)
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-vcf?drug=WARFARIN" \
  -F "file=@sample.vcf"
```

### Analyze a VCF file (multiple drugs)
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-vcf?drug=WARFARIN,CLOPIDOGREL" \
  -F "file=@sample.vcf"
```

### Expected response schema (current)
```json
{
  "patient_id": "PATIENT_XXX",
  "drug": "DRUG_NAME",
  "timestamp": "ISO8601_timestamp",
  "risk_assessment": {
    "risk_label": "Safe|Adjust Dosage|Toxic|Ineffective|Unknown",
    "confidence_score": 0.0,
    "severity": "none|low|moderate|high|critical"
  },
  "pharmacogenomic_profile": {
    "primary_gene": "GENE_SYMBOL",
    "diplotype": "*X/*Y",
    "phenotype": "PM|IM|NM|RM|URM|Unknown",
    "detected_variants": [
      { "rsid": "rsXXXX" }
    ]
  },
  "clinical_recommendation": {
    "action": "...",
    "detail": "..."
  },
  "llm_generated_explanation": {
    "summary": "...",
    "patient_summary": "..."
  },
  "quality_metrics": {
    "vcf_parsing_success": true
  }
}
```

## Team Members
- Shrish Patil
- Add additional members here
