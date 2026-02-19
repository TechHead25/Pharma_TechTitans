# PharmaGuard: Pharmacogenomic Risk Prediction Engine

**Intelligent VCF-based pharmacogenomic analysis for precision medicine** 🛡️💊

PharmaGuard is a full-stack web application that analyzes VCF (Variant Call Format) files to predict pharmacogenomic risks aligned with CPIC (Clinical Pharmacogenetics Implementation Consortium) guidelines.

## 🎯 Features

### Backend (Python/FastAPI)
- **VCF Parser**: Robust parsing of VCF v4.2 files up to 5 MB
- **Gene Focus**: Analyzes CYP2D6, CYP2C19, CYP2C9, SLCO1B1, TPMT, DPYD
- **Drug Mapping**: Predicts risks for CODEINE, WARFARIN, CLOPIDOGREL, SIMVASTATIN, AZATHIOPRINE, FLUOROURACIL
- **Risk Engine**: CPIC-aligned risk assessment with 5 outcomes: Safe, Adjust Dosage, Toxic, Ineffective, Unknown
- **LLM Integration**: GPT-powered clinical explanations with variant citations and biological mechanisms
- **Strict JSON Output**: Standardized response format for integration

### Frontend (React + Tailwind CSS)
- **Drag-and-Drop Uploader**: Intuitive VCF file upload with real-time validation
- **Color-Coded Results**: Green (Safe), Yellow (Adjust), Red (Toxic), Orange (Ineffective)
- **Expandable Details**: View clinical recommendations and LLM explanations
- **Copy-to-Clipboard**: Export results as JSON
- **Responsive Design**: Works on desktop, tablet, and mobile

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Tailwind)              │
│  - VCF Uploader (Drag-drop, 5MB limit validation)          │
│  - Results Display (Color-coded risk assessment)           │
│  - Copy JSON to Clipboard                                   │
└────────────────────────┬────────────────────────────────────┘
                         │ API Calls (HTTP/REST)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI + Python)                      │
├─────────────────────────────────────────────────────────────┤
│  API Endpoints:                                              │
│  - POST /api/v1/analyze-vcf     → Full VCF analysis       │
│  - POST /api/v1/validate-vcf    → File validation         │
│  - GET  /api/v1/results/{id}    → Retrieve results        │
│  - GET  /api/v1/health          → Health check            │
├─────────────────────────────────────────────────────────────┤
│  Core Modules:                                               │
│  ├─ VCF Parser        → Extracts GENE, STAR, RS tags      │
│  ├─ Risk Engine       → CPIC-aligned phenotype→risk       │
│  ├─ LLM Integration   → OpenAI GPT explanations           │
│  └─ Response Models   → Pydantic validation models        │
└─────────────────────────────────────────────────────────────┘
```

## 📋 JSON Response Schema

```json
{
  "patient_id": "PAT-XXXXXXXXXX",
  "drug": "WARFARIN",
  "timestamp": "2024-02-19T10:30:00Z",
  "risk_assessment": {
    "risk_label": "Adjust Dosage",
    "confidence_score": 0.88,
    "severity": "high"
  },
  "pharmacogenomic_profile": {
    "primary_gene": "CYP2C9",
    "diplotype": "*1/*2",
    "phenotype": "IM",
    "detected_variants": [
      { "rsid": "rs1801159" }
    ]
  },
  "clinical_recommendation": "Recommend dose adjustment for WARFARIN...",
  "llm_generated_explanation": {
    "summary": "Patient has intermediate metabolizer phenotype..."
  },
  "quality_metrics": {
    "vcf_parsing_success": true
  }
}
```

## 🚀 Quick Start

### Prerequisites
- **Backend**: Python 3.10+
- **Frontend**: Node.js 18+
- **Git**: For cloning the repository
- **Optional**: OpenAI API key for LLM explanations

### Step 1: Clone the Repository

#### Method 1: Using HTTPS (Recommended for first-time users)
```bash
git clone https://github.com/yourusername/pharmaguard.git
cd pharmaguard
```

#### Method 2: Using SSH (Recommended if you have SSH keys configured)
```bash
git clone git@github.com:yourusername/pharmaguard.git
cd pharmaguard
```

#### Method 3: Download as ZIP
1. Go to the GitHub repository page
2. Click the green **Code** button
3. Select **Download ZIP**
4. Extract the ZIP file to your desired location
5. Open terminal/command prompt in the extracted folder

### Step 2: Backend Setup

```bash
cd pharmaguard-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key (optional)

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Step 3: Frontend Setup

```bash
# Go back to root directory first
cd ..
cd pharmaguard-frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local if backend is not at localhost:8000

# Start development server
npm run dev
```

App will open at `http://localhost:3000`

### Step 4: Verify Installation

1. **Check Backend**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   You should see: `{"status": "healthy"}`

2. **Check Frontend**:
   - Open browser and navigate to `http://localhost:3000`
   - You should see the PharmaGuard login interface

---

## 📖 After Cloning: Common Tasks

### Making Changes and Pushing Back to GitHub

1. **Create a new branch for your changes**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** to the code

3. **Add and commit your changes**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

4. **Push to GitHub**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub to merge your branch into main

### Updating Local Repository with Latest Changes

If someone else has made changes on GitHub, pull them into your local copy:

```bash
git pull origin main
```

### Checking What You've Changed

```bash
# See what files have been modified
git status

# See detailed changes
git diff

# See commit history
git log --oneline
```

---

## 🛠️ Using Helper Scripts

After cloning, you can use the included startup scripts:

### Windows
```bash
start-dev.bat
```

### macOS/Linux
```bash
bash start-dev.sh
```

These scripts will:
- Activate the Python virtual environment
- Install dependencies
- Start both backend and frontend servers
- Open the application in your browser

## 📖 Sample VCF File

```vcf
##fileformat=VCFv4.2
##fileDate=20240219
#CHROM  POS       ID          REF ALT QUAL FILTER  INFO
chr22   42127941  rs1065852   G   A   60   PASS    GENE=CYP2D6;STAR=*4;RS=rs1065852
chr10   96621094  rs2687119   G   C   60   PASS    GENE=CYP2C19;STAR=*2;RS=rs2687119
```

Sample VCF files are included in `sample_vcf/` directory for testing.

## 🧬 Gene-Drug Mappings

| Gene | Drugs | Phenotype Outcomes |
|------|-------|-------------------|
| CYP2D6 | CODEINE | PM, IM, NM, RM, URM |
| CYP2C19 | WARFARIN, CLOPIDOGREL | PM, IM, NM, RM, URM |
| CYP2C9 | WARFARIN | PM, IM, NM, RM, URM |
| SLCO1B1 | SIMVASTATIN | PM, IM, NM, RM, URM |
| TPMT | AZATHIOPRINE | PM, IM, NM, RM, URM |
| DPYD | FLUOROURACIL | PM, IM, NM, RM, URM |

**Phenotype Codes**:
- **PM** = Poor Metabolizer (reduced/absent activity)
- **IM** = Intermediate Metabolizer (reduced activity)
- **NM** = Normal Metabolizer (normal activity)
- **RM** = Rapid Metabolizer (increased activity)
- **URM** = Ultra-Rapid Metabolizer (very high activity)

## 🔐 Risk Assessment Outcomes

1. **Safe** ✓
   - Patient can take standard dosage
   - Confidence: 95%+

2. **Adjust Dosage** ⚠️
   - Dose modification recommended
   - Confidence: 85-90%

3. **Toxic** ✕
   - High toxicity risk
   - Confidence: 90%+
   - May require alternative therapy

4. **Ineffective** —
   - Reduced/no therapeutic response
   - Confidence: 88%+
   - Consider alternative drug

5. **Unknown** ?
   - Insufficient data
   - Baseline dosing recommended
   - Requires clinical monitoring

## 📡 API Endpoints

### POST /api/v1/analyze-vcf
Upload VCF file for comprehensive analysis

**Request**:
```bash
curl -X POST -F "file=@sample.vcf" http://localhost:8000/api/v1/analyze-vcf
```

**Response**: PharmaGuardResponse object (see schema above)

### POST /api/v1/validate-vcf
Validate VCF file without full analysis

**Response**:
```json
{
  "valid": true,
  "message": "Valid VCF structure",
  "size_mb": 0.05,
  "file_name": "sample.vcf"
}
```

### GET /api/v1/health
Health check endpoint

## 🌐 Deployment

### Frontend Deployment (Vercel)

1. **Connect Repository** to Vercel
2. **Configure Environment**:
   ```
   VITE_API_URL=https://your-backend-url.com
   ```
3. **Deploy**: Auto-deploys on push to main

**Live Frontend**: 🔗 [https://pharmaguard-frontend.vercel.app](https://pharmaguard-frontend.vercel.app) *(Update this with your actual URL)*

### Backend Deployment (Render or Railway)

#### Option 1: Render
1. Push code to GitHub
2. Create new Web Service on Render
3. Connect repository
4. Set environment variables in Render dashboard
5. Deploy

**Live Backend**: 🔗 [https://pharmaguard-backend.onrender.com](https://pharmaguard-backend.onrender.com) *(Update this with your actual URL)*

#### Option 2: Railway
1. Connect GitHub account
2. Create new project from repository
3. Railway auto-detects Python app
4. Configure environment variables
5. Deploy

## 📚 VCF Parsing Details

### Supported VCF v4.2 Features
- Header lines (##fileformat, ##fileDate, etc.)
- Column definitions (#CHROM POS ID REF ALT QUAL FILTER INFO)
- INFO field parsing (key=value format)
- Multi-allelic variants support

### Required INFO Tags
- **GENE**: Gene symbol (e.g., "CYP2D6")
- **STAR**: Star allele notation (e.g., "*1", "*2")
- **RS**: dbSNP rsid (e.g., "rs1065852")

### File Size Limits
- Maximum: 5 MB
- Format: UTF-8 text
- Extension: .vcf

## 🤖 LLM Integration

### OpenAI GPT Integration
If OPENAI_API_KEY is configured, PharmaGuard uses GPT-3.5-turbo to generate clinical explanations including:
- Biological mechanism of gene-drug interaction
- Why phenotype matters for dosing
- CPIC recommendation
- Monitoring recommendations

### Fallback Mode
If no API key or LLM unavailable, generates rule-based clinical explanations.

## 🧪 Testing

### Backend Tests
```bash
cd pharmaguard-backend
pytest
```

### Sample Data
Test with included VCF files:
- `cyp2d6_pm_example.vcf` - CYP2D6 poor metabolizer
- `tpmt_pm_example.vcf` - TPMT poor metabolizer
- `slco1b1_im_example.vcf` - SLCO1B1 intermediate metabolizer
- `cyp2c9_im_example.vcf` - CYP2C9 intermediate metabolizer

## 🎓 Educational Purpose

**Disclaimer**: PharmaGuard is designed for educational and research purposes. It is **NOT** a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers and clinical pharmacists for actual patient care.

## 📖 References

- **CPIC Guidelines**: https://cpicpgx.org
- **PharmGen Data**: https://www.pharmgkb.org
- **VCF Specification**: https://samtools.github.io/hts-specs/VCFv4.2.pdf
- **Pharmacogenomics**: https://www.ncbi.nlm.nih.gov/grc/human

## 👥 Contributing

This project is open for improvements. Key areas for contribution:
- Additional gene-drug interactions
- Enhanced VCF parsing
- More sophisticated phenotype inference
- Additional clinical guidelines (FDA, EMA)

## 📄 License

MIT License - See LICENSE file for details

## 📱 Demo & Live Deployment

### 🌐 Live URLs
- **Frontend Application**: https://pharmaguard-frontend.vercel.app *(Update with your Vercel deployment)*
- **Backend API Docs**: https://pharmaguard-backend.onrender.com/docs *(Update with your Render deployment)*
- **GitHub Repository**: https://github.com/yourusername/pharmaguard

### 📹 Demo & Documentation
- **LinkedIn Project Video**: [Create & link your demo video] *(Record pharmacogenomic analysis demo)*
- **Architecture Overview**: See [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Deployment Guide**: See [DEPLOYMENT.md](./DEPLOYMENT.md)

### ⚡ Quick Start (Development)
```bash
# Windows
start-dev.bat

# macOS/Linux
bash start-dev.sh

# Or manual
# Terminal 1: Backend
cd pharmaguard-backend && python run_backend.py

# Terminal 2: Frontend  
cd pharmaguard-frontend && npm run dev
```

### 🚀 Deploy in Minutes

**Frontend (Vercel)**:
```bash
cd pharmaguard-frontend
vercel --prod
```

**Backend (Render)**:
1. Push code to GitHub
2. Connect on Render.com
3. Set `OPENAI_API_KEY` environment variable
4. Deploy automatically

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete instructions

## 👤 Author

**Health-Tech Engineer**
Specialized in pharmacogenomic data analysis and precision medicine

---

**Last Updated**: February 19, 2024
**Version**: 1.0.0
