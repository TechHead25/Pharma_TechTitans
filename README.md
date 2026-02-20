# PharmaGuard

PharmaGuard is a full-stack pharmacogenomics decision-support platform that converts raw VCF genetics data into CPIC-aligned drug risk insights, actionable clinical recommendations, and patient-friendly explanations.

##  Live Demo

###Important for Evaluation:

-The backend is deployed on Render (free tier), which automatically suspends services after 15 minutes of no traffic. If the application takes time to load on first access, it is due to the server waking -up. Please wait briefly and refresh if needed — the system functions normally once active.

### Frontend (Vercel)
- Production: https://pharma-tech-titans1.vercel.app
- Register: https://pharma-tech-titans1.vercel.app/register
- Login: https://pharma-tech-titans1.vercel.app/login

### Backend API (Render)
- API Base URL: https://pharma-techtitans.onrender.com 
- Health Check: https://pharma-techtitans.onrender.com/api/v1/health
- API Docs (Swagger): https://pharma-techtitans.onrender.com/docs
- Supported Drugs Endpoint: https://pharma-techtitans.onrender.com/api/v1/drugs

### Demo Video
- LinkedIn: https://www.linkedin.com/posts/aditi-katti-b872913b2_rift2026-pharmaguard-pharmacogenomics-ugcPost-7430430934736375808-6rIa
- 
##  Problem We Solve

Pharmacogenomic reports are often too technical, fragmented, and hard to act on quickly in real-world workflows. Clinicians need a fast and interpretable summary, while patients need clear plain-language guidance.

PharmaGuard bridges this gap by combining:
- Structured pharmacogenomic interpretation from VCF data
- CPIC-aligned risk stratification
- Dual explanations for both clinicians and patients

##  Why PharmaGuard is Hackathon-Ready

- Real healthcare impact: safer prescribing and reduced adverse drug events
- End-to-end product: upload → analyze → recommend → explain
- Strong engineering stack: production-grade API, typed schemas, deploy-ready architecture
- Explainable AI layer: clinician-grade and patient-grade summaries from the same genomic context
- Demo-friendly UX: clean workflow, instant risk labels, JSON export-ready outputs

##  Core Features

- VCF upload and robust validation
- Drug-first analysis flow (single or multiple drugs)
- CPIC-aligned pharmacogenomic risk assessment engine
- Structured JSON response with strict schema validation
- Dual-layer LLM explanation generation:
  - Clinical summary for professionals
  - Jargon-free summary for patients
- User authentication and role-aware routes
- Record persistence and retrieval APIs
- Frontend dashboard with color-coded severity and recommendations

##  Supported Pharmacogenomic Scope

### Genes
- CYP2D6
- CYP2C19
- CYP2C9
- SLCO1B1
- TPMT
- DPYD

### Drugs
- CODEINE
- WARFARIN
- CLOPIDOGREL
- SIMVASTATIN
- AZATHIOPRINE
- FLUOROURACIL

##  Architecture

PharmaGuard uses a client-server architecture:

- Frontend: React + Vite + Tailwind
  - Upload + selection workflow
  - Visual risk and recommendation display
  - Authenticated user experience
- Backend: FastAPI + SQLAlchemy + Pydantic
  - Parsing, interpretation, risk scoring
  - Auth, records, admin routes
  - Strict API contracts
- Data layer:
  - PostgreSQL-ready deployment support via DATABASE_URL
  - SQLite fallback for local development

High-level flow:
1. User uploads a .vcf file and selects one or more drugs.
2. API validates and parses target variants.
3. Risk engine computes phenotype + risk label + severity + confidence.
4. LLM module generates clinical and patient summaries.
5. Structured response is returned and rendered in UI.

##  Tech Stack

### Frontend
- React
- Vite
- Tailwind CSS
- React Router
- Axios

### Backend
- FastAPI
- SQLAlchemy
- Pydantic
- python-jose (JWT)
- Passlib/Bcrypt

### AI + Data
- Google Gemini API
- PostgreSQL (production) + SQLite fallback (local)

### DevOps / QA
- Render (backend deploy)
- Vercel (frontend deploy)
- Pytest (backend tests)

##  Quick Start (Local)

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### 1) Clone
```bash
git clone <your-repo-url>
cd Pharma
```

### 2) Backend Setup
```bash
cd pharmaguard-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_backend.py
```

Backend local URLs:
- http://localhost:8000
- http://localhost:8000/api/v1/health
- http://localhost:8000/docs

### 3) Frontend Setup
```bash
cd ..\pharmaguard-frontend
npm install
npm run dev
```

Frontend local URL:
- http://localhost:5173 (or the port Vite prints)

##  Environment Variables

### Backend (Render / local)
- GEMINI_API_KEY
- SECRET_KEY
- DATABASE_URL (recommended for production)

### Frontend (Vercel)
- VITE_API_URL=https://pharma-techtitans.onrender.com

##  API Endpoints

### Core
- POST /api/v1/validate-vcf
- POST /api/v1/analyze-vcf?drug=<DRUGS>
- GET /api/v1/drugs
- GET /api/v1/health

### Authentication
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET /api/v1/auth/me

### Records
- POST /api/v1/records/save
- GET /api/v1/records/user
- GET /api/v1/records/{id}

##  Structured Response Schema

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

##  Hackathon Judging Highlights

- Innovation: combines deterministic pharmacogenomic logic with explainable LLM output
- Technical depth: full-stack, secure auth, schema-driven APIs, deployment on cloud platforms
- Impact: supports precision medicine decisions with interpretable risk context
- Product readiness: live deployed frontend/backend with documented setup and API docs
- Scalability: clean modular backend, database portability, and extensible gene-drug mapping

##  Roadmap

- Expand to additional CPIC drug-gene pairs
- Add clinician report PDF export
- Add cohort analytics for population-level insights
- Introduce audit trail + explainability confidence metadata
- Integrate EHR-compatible interoperability formats

##  Team

- Shrish Patil
- Aditi Katti
- Sinchana Hebaar KM
- Priyanka B
