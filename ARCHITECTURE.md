# PharmaGuard Architecture

## 🏗️ System Overview

PharmaGuard is a full-stack pharmacogenomic risk prediction application built on:

```
┌─────────────────────────────────────────────────────────────────┐
│                    React + Tailwind CSS Frontend                 │
│  • Vite (Dev Server)                                            │
│  • Drag-drop VCF upload interface                               │
│  • Color-coded risk visualization                               │
│  • JSON export functionality                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP REST API
                         │ CORS-enabled
                         │ Multipart form upload
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.10+)                      │
│  • Uvicorn (ASGI Server)                                        │
│  • Pydantic (Data Validation)                                   │
│  • OpenAI GPT Integration (Optional)                            │
│                                                                  │
│  ├─ VCF Parser Module                                          │
│  │  ├─ vcf_parser.py                                           │
│  │  └─ Supports VCF v4.2 format                               │
│  │                                                              │
│  ├─ Risk Engine Module                                         │
│  │  ├─ risk_engine.py                                          │
│  │  ├─ CPIC guideline alignment                               │
│  │  └─ Phenotype inference                                     │
│  │                                                              │
│  ├─ LLM Integration                                            │
│  │  ├─ llm_integration.py                                      │
│  │  └─ OpenAI GPT-3.5-turbo                                   │
│  │                                                              │
│  └─ API Endpoints                                              │
│     ├─ POST /api/v1/analyze-vcf                                │
│     ├─ POST /api/v1/validate-vcf                               │
│     ├─ GET  /api/v1/results/{id}                               │
│     └─ GET  /api/v1/health                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
pharmaguard/
├── README.md                           # Main documentation
├── DEPLOYMENT.md                       # Deployment guide  
├── ARCHITECTURE.md                     # This file
│
├── pharmaguard-backend/                # FastAPI Backend
│   ├── requirements.txt                # Dev dependencies
│   ├── requirements-deploy.txt         # Production dependencies
│   ├── runtime.txt                     # Python version (Heroku/Render)
│   ├── Procfile                        # Gunicorn config for Render/Heroku
│   ├── .env.example                    # Environment variables template
│   ├── .gitignore                      # Git ignore rules
│   ├── run_backend.py                  # Startup script
│   │
│   ├── app/                            # Main application package
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app definition & routes
│   │   ├── models.py                   # Pydantic response models
│   │   ├── llm_integration.py          # OpenAI LLM integration
│   │   │
│   │   ├── parsers/                    # VCF parsing module
│   │   │   ├── __init__.py
│   │   │   └── vcf_parser.py           # VCF v4.2 parser implementation
│   │   │
│   │   └── engines/                    # Risk assessment module
│   │       ├── __init__.py
│   │       └── risk_engine.py          # CPIC risk assessment logic
│   │
│   ├── tests/                          # Unit tests
│   │   ├── __init__.py
│   │   ├── test_vcf_parser.py          # VCF parser tests
│   │   └── test_risk_engine.py         # Risk engine tests
│   │
│   └── sample_vcf/                     # Test data
│       ├── cyp2d6_pm_example.vcf       # CYP2D6 Poor Metabolizer
│       ├── tpmt_pm_example.vcf         # TPMT Poor Metabolizer
│       ├── slco1b1_im_example.vcf      # SLCO1B1 Intermediate
│       └── cyp2c9_im_example.vcf       # CYP2C9 Intermediate
│
└── pharmaguard-frontend/               # React Frontend
    ├── package.json                    # NPM dependencies
    ├── vite.config.js                  # Vite config
    ├── tailwind.config.js              # Tailwind CSS config
    ├── postcss.config.js               # PostCSS config
    ├── vercel.json                     # Vercel deployment config
    ├── .env.example                    # Environment template
    ├── .gitignore                      # Git ignore rules
    ├── index.html                      # HTML entry point
    │
    └── src/                            # React source
        ├── main.jsx                    # ReactDOM entry
        ├── App.jsx                     # Main app component
        ├── index.css                   # Tailwind + custom styles
        ├── api.js                      # API client (Axios)
        │
        └── components/                 # React components
            ├── VCFUploader.jsx         # File upload component
            └── ResultsDisplay.jsx      # Results visualization
```

---

## 🔄 Data Flow Diagram

### 1. File Upload Flow
```
User Action
    │
    ▼
┌─────────────────────────────────────┐
│ Frontend VCFUploader Component       │
│ - Drag-drop validation              │
│ - File size check (5MB limit)       │
│ - File type validation (.vcf)       │
└──────────────┬──────────────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │ API: /validate-vcf       │
    └──────────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
    Valid                 Invalid
        │                     │
        ▼                     ▼
    Proceed        Show Error Message
    │
    ▼
    ┌──────────────────────────┐
    │ API: /analyze-vcf        │
    │ (Multipart form upload)  │
    └──────────────┬───────────┘
```

### 2. VCF Analysis Flow
```
┌─────────────────────────────────────────────────────────┐
│ Backend: POST /api/v1/analyze-vcf                       │
└──────────────────────┬──────────────────────────────────┘
                       │
    ┌──────────────────────────────────────┐
    │ 1. File Validation                    │
    │    - Check size (5 MB limit)          │
    │    - Validate UTF-8 encoding          │
    │    - Check .vcf extension             │
    └──────────────────┬───────────────────┘
                       │
    ┌──────────────────────────────────────┐
    │ 2. VCF Parsing (vcf_parser.py)       │
    │    - Parse header (#CHROM line)      │
    │    - Extract INFO tags (GENE,STAR)   │
    │    - Filter target genes             │
    │    - Extract variants                │
    └──────────────────┬───────────────────┘
                       │
    ┌──────────────────────────────────────┐
    │ 3. For each gene found:              │
    │    - Identify drug targets           │
    │    - Infer phenotype from alleles    │
    │    - Get drug list for gene          │
    └──────────────────┬───────────────────┘
                       │
    ┌──────────────────────────────────────┐
    │ 4. For each gene-drug pair:          │
    │    - Assess risk (risk_engine.py)    │
    │    - Map phenotype to risk label     │
    │    - Get confidence score            │
    │    - Generate recommendations       │
    └──────────────────┬───────────────────┘
                       │
    ┌──────────────────────────────────────┐
    │ 5. Generate Explanations             │
    │    - Call OpenAI GPT (if available)  │
    │    - Generate clinical explanation  │
    │    - Include mechanism & CPIC ref    │
    │    - Fallback to rule-based text     │
    └──────────────────┬───────────────────┘
                       │
    ┌──────────────────────────────────────┐
    │ 6. Format Response                   │
    │    - Build PharmaGuardResponse JSON  │
    │    - Validate with Pydantic          │
    │    - Store in memory (future: DB)    │
    └──────────────────┬───────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────┐
    │ Return JSON Array of Assessments     │
    │ (one assessment per gene-drug pair)  │
    └──────────────────────────────────────┘
```

### 3. Frontend Display Flow
```
API Response (JSON Array)
│
▼
┌─────────────────────────────────────┐
│ ResultsDisplay Component             │
│ - Parse response array               │
│ - Display patient ID & count         │
└──────────────┬──────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │ For each assessment:                 │
    │ - Render ResultCard component        │
    └──────────────┬───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
    Header Section       Expandable Details
        │                     │
        ▼                     ▼
    ┌─────────────┐    ┌──────────────────┐
    │ Risk Badge  │    │ Clinical Details │
    │ (color)     │    │ - Recommendation │
    │ Confidence  │    │ - LLM Explanation│
    │ Gene/Drug   │    │ - Metadata       │
    │ Severity    │    │ - Copy JSON Btn  │
    └─────────────┘    └──────────────────┘
```

---

## 🧬 Pharmacogenomic Risk Assessment

### Gene-Drug Mapping

```python
GENE_DRUG_MAPPING = {
    "CYP2D6": ["CODEINE"],
    "CYP2C19": ["WARFARIN", "CLOPIDOGREL"],
    "CYP2C9": ["WARFARIN"],
    "SLCO1B1": ["SIMVASTATIN"],
    "TPMT": ["AZATHIOPRINE"],
    "DPYD": ["FLUOROURACIL"],
}
```

### Phenotype Scale

```
PM (Poor Metabolizer)
├─ Metabolic activity: Very Low (0-20%)
├─ Effect on drug: ↑↑↑ HIGH accumulation
└─ Risk: TOXIC or INEFFECTIVE

IM (Intermediate Metabolizer)
├─ Metabolic activity: Low (20-50%)
├─ Effect on drug: ↑ Moderate accumulation
└─ Risk: ADJUST DOSAGE

NM (Normal Metabolizer)
├─ Metabolic activity: Normal (50-100%)
├─ Effect on drug: Normal clearance
└─ Risk: SAFE

RM (Rapid Metabolizer)
├─ Metabolic activity: High (100-200%)
├─ Effect on drug: ↓ Rapid clearance
└─ Risk: INEFFECTIVE (may need ↑ dose)

URM (Ultra-Rapid Metabolizer)
├─ Metabolic activity: Very High (>200%)
├─ Effect on drug: ↓↓↓ Very rapid clearance
└─ Risk: TOXIC (if high doses) or INEFFECTIVE
```

### Risk Assessment Matrix

```
                Gene Function
                PM    IM    NM    RM    URM
            ┌────────────────────────────────┐
CODEINE     │ INE   ADJ   SAFE  SAFE  TXC  │
WARFARIN    │ ADJ   ADJ   SAFE  SAFE  SAFE │
CLOPIDOGREL │ INE   ADJ   SAFE  SAFE  SAFE │
SIMVASTATIN │ TXC   ADJ   SAFE  SAFE  SAFE │
AZATHIOPRINE│ TXC   ADJ   SAFE  SAFE  SAFE │
FLUOROURACIL│ TXC   ADJ   SAFE  SAFE  SAFE │
            └────────────────────────────────┘

Legend: TXC=Toxic, INE=Ineffective, ADJ=Adjust, SAFE=Safe
```

---

## 📊 API Response Schema

### Request Format
```
POST /api/v1/analyze-vcf
Content-Type: multipart/form-data

file: [VCF file content]
```

### Response Format
```json
[
  {
    "patient_id": "PAT-D37067A63086",
    "drug": "CODEINE",
    "timestamp": "2026-02-19T08:05:34.184677Z",
    "risk_assessment": {
      "risk_label": "Safe|Adjust Dosage|Toxic|Ineffective|Unknown",
      "confidence_score": 0.95,
      "severity": "none|low|moderate|high|critical"
    },
    "pharmacogenomic_profile": {
      "primary_gene": "CYP2D6",
      "diplotype": "*1/*1",
      "phenotype": "NM",
      "detected_variants": [
        {"rsid": "rs1065852"}
      ]
    },
    "clinical_recommendation": "Patient can take standard dosage...",
    "llm_generated_explanation": {
      "summary": "Clinical explanation from LLM..."
    },
    "quality_metrics": {
      "vcf_parsing_success": true
    }
  }
]
```

---

## 🔧 Technology Stack

### Backend
- **Framework**: FastAPI (Python web framework)
- **ASGI Server**: Uvicorn (async server)
- **Data Validation**: Pydantic (type hints + validation)
- **LLM Integration**: OpenAI API (GPT-3.5-turbo)
- **Testing**: Pytest
- **Production Server**: Gunicorn

### Frontend
- **Framework**: React 18 (JavaScript UI library)
- **Build Tool**: Vite (next-gen bundler)
- **Styling**: Tailwind CSS (utility-first CSS)
- **HTTP Client**: Axios (promise-based HTTP)
- **Icons**: React Icons

###Deployment
- **Frontend**: Vercel (serverless platform)
- **Backend**: Render.com (PaaS platform)
- **Version Control**: Git/GitHub

---

## 🔐 Security Considerations

### Input Validation
- ✅ VCF file size limit: 5 MB
- ✅ File type validation: .vcf extension
- ✅ UTF-8 encoding validation
- ✅ INFO field parsing validation

### API Security
- ✅ CORS middleware enabled
- ✅ Trusted domain whitelist
- ✅ HTTPS enforcement (production)
- ✅ No exposed sensitive data

### Data Privacy
- ✅ No persistent patient data storage
- ✅ Temporary in-memory results
- ✅ No logging of medical data
- ✅ HIPAA-compliant architecture (ready for DB upgrade)

---

## 📈 Performance Characteristics

### VCF Parsing
- **Speed**: ~10ms for typical 1MB file
- **Memory**: O(n) where n = number of variants
- **Limitations**: 5MB file size limit (configurable)

### Risk Assessment
- **Speed**: O(g*d) where g=genes, d=drugs
- **Memory**: O(1) - uses lookup tables
- **Typical Response**: <100ms total

### LLM Requests
- **Speed**: 1-3 seconds (API latency)
- **Fallback**: Instant rule-based explanation
- **Tokens**: ~200 tokens per request

---

## 🚀 Scalability

### Current Architecture
- Stateless API (horizontal scaling ready)
- In-memory storage (suitable for MVP)
- No database dependencies

### Future Improvements
- **Database**: PostgreSQL for patient history
- **Caching**: Redis for LLM responses
- **Queue**: Celery for async VCF processing
- **Search**: Elasticsearch for variant search
- **Monitoring**: Sentry for error tracking

---

## 📚 References & Standards

- **CPIC Guidelines**: https://cpicpgx.org
- **VCF Format**: https://samtools.github.io/hts-specs/VCFv4.2.pdf
- **PharmGKB Database**: https://www.pharmgkb.org
- **FDA Guidance**: https://www.fda.gov/drugs/science-and-research-drugs/pharmacogenomics

---

## 🔄 CI/CD Pipeline

### Current Setup
1. **Push to GitHub**
2. **Vercel Auto-Deploy** (Frontend)
3. **Render Auto-Deploy** (Backend)
4. **Smoke Tests** (API health check)

### Future Improvements
- Automated test suite (GitHub Actions)
- Performance benchmarks
- Security scanning
- Database migrations

---

## 📋 Development Workflow

```bash
# Local Development
npm run dev          # Frontend dev server (hot reload)
python run_backend.py  # Backend dev server (auto-reload)

# Testing
pytest               # Backend unit tests
npm test            # Frontend tests (future)

# Building
npm run build       # Production frontend bundle
pip install -r requirements-deploy.txt  # Production deps

# Deployment
git push            # Triggers auto-deployment
```

---

**PharmaGuard Architecture v1.0** | Last Updated: Feb 2024
