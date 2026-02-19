# PharmaGuard 2.0 - Visual Workflow Guide

## Selection-First Workflow (NEW in v2.0)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            START                                         │
│                     PharmaGuard v2.0 Landing                             │
│                    Dual-Layer LLM Analysis                               │
└─────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: SELECT MEDICATION                                  Progress: 1/3 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  "Which medication are you taking?"                                      │
│                                                                           │
│  ┌─────────────────────────────────────────┐                             │
│  │ 🔽 Select Medication...        [Search]  │ ← DrugSelector             │
│  ├─────────────────────────────────────────┤                             │
│  │ CODEINE                                 │                             │
│  │ WARFARIN                                │                             │
│  │ CLOPIDOGREL                             │                             │
│  │ SIMVASTATIN                             │                             │
│  │ AZATHIOPRINE                            │                             │
│  │ FLUOROURACIL                            │                             │
│  └─────────────────────────────────────────┘                             │
│                                                                           │
│  Selected: CODEINE ✓                                                     │
│                                                                           │
└─────────────────────────────┬───────────────────────────────────────────┘
                               │ User selects CODEINE
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: UPLOAD VCF FILE                                   Progress: 2/3 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Selected Medication: CODEINE [Change]                                  │
│                                                                           │
│  "Upload your VCF file for analysis"                                    │
│                                                                           │
│  ┌─────────────────────────────────────────┐                             │
│  │  Drag-and-drop VCF file here            │ ← VCFUploader              │
│  │  or click to select                      │                             │
│  │                                          │                             │
│  │  File: cyp2d6_pm.vcf (2.4 KB) ✓          │                             │
│  │  Status: Valid VCF v4.2                  │                             │
│  └─────────────────────────────────────────┘                             │
│                                                                           │
│  [Analyze Pharmacogenomic Profile] ← Triggers analysis with CODEINE    │
│                                                                           │
└─────────────────────────────┬───────────────────────────────────────────┘
                               │ File uploaded, analysis starts
                               ▼
              ╔═══════════════════════════════════╗
              ║  Backend Processing               ║
              ║  ──────────────────────────────   ║
              ║  1. Parse VCF file                ║
              ║  2. Extract target genes          ║
              ║  3. Infer phenotype (CYP2D6: PM)  ║
              ║  4. Assess CODEINE risk           ║
              ║  5. Generate DUAL explanations:   ║
              ║     - Clinical (technical)        ║
              ║     - Patient (simple)            ║
              ║  6. Return results                ║
              ╚═══════════════════════════════════╝
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: RESULTS & ANALYSIS                                Progress: 3/3 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ ✕ INEFFECTIVE  | HIGH SEVERITY                                    │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │                                                                    │  │
│  │ GENE: CYP2D6      MEDICATION: CODEINE      DIPLOTYPE: *4/*4       │  │
│  │ PHENOTYPE: PM     CONFIDENCE: 95%          [⬇️ Download JSON]     │  │
│  │                                                                    │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │  Clinical Recommendation:                                         │  │
│  │  ────────────────────────                                         │  │
│  │  Poor metabolizer phenotype indicates severely reduced CYP2D6     │  │
│  │  function (< 10% activity). CPIC RECOMMENDATION: AVOID CODEINE    │  │
│  │                                                                    │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │  [📋 Healthcare Pros] [👥 Patient]  ← Toggle between personas     │  │
│  │                                                                    │  │
│  │  📋 CLINICAL SUMMARY (Technical)                                 │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │ Patient carries *4/*4 genotype resulting in poor          │  │  │
│  │  │ metabolizer (PM) phenotype for CYP2D6. Detected variants  │  │  │
│  │  │ rs1065852, rs3892097 are loss-of-function alleles.       │  │  │
│  │  │ CYP2D6 encodes a phase I metabolizing enzyme...           │  │  │
│  │  │ CPIC RECOMMENDATION: AVOID codeine; choose alternative    │  │  │
│  │  │ analgesics with no CYP2D6 dependence.                     │  │  │
│  │  │                                                   [📋 Copy] │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │                                                                    │  │
│  │  👥 PATIENT SUMMARY (Simple & Friendly) - Click to switch         │  │
│  │                                                                    │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │  Detected Variants:                                               │  │
│  │  [rs1065852]  [rs3892097]  ← Gene mutation badges                 │  │
│  │                                                                    │  │
│  │  Patient ID: PAT-ABC123XYZ456 | Generated: 2024-02-19 14:37:22   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  [New Analysis] ← Start over with different drug or file               │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Dual-Layer LLM Explanations

### Clinical Summary (For Healthcare Professionals)
```
Technical Explanation - Suitable for prescribers, pharmacists, genetic counselors

● Specific Variant Information
  - Lists detected RSIDs (e.g., rs1065852, rs3892097)
  - Cites functional impact (loss-of-function, gain-of-function)

● Biological Mechanism
  - Enzyme function: "CYP2D6 encodes phase I metabolizing enzyme..."
  - Substrate phenotype: "PM = <10% enzyme activity..."
  - Drug impact: "Reduced morphine formation → inadequate pain relief..."

● CPIC Guidelines
  - Specific recommendations: "CPIC recommends AVOIDING codeine..."
  - Dosing adjustments or alternatives

● Actionable Information
  - "Consider alternative analgesics..."
  - "Monitor for treatment failure..."

Example Length: 200-300 characters, technical jargon included
```

### Patient Summary (Simple & Friendly)
```
Easy-to-Understand Explanation - Suitable for patients

● Relatable Analogy
  - "Your body has difficulty converting CODEINE..."
  - "It's like trying to drain a bathtub with a narrow pipe..."

● Plain Language
  - No jargon (CYP2D6 → "your body"; phenotype → "genetic makeup")
  - Empathetic tone

● Personalized Information
  - "Your genetic test shows you inherit two copies of a variant (*4/*4)..."
  - "This means the standard dose might not work..."

● Actionable Advice
  - "Your doctor will likely suggest a different pain reliever..."
  - "It works better for your genetics"

Example Length: 150-250 characters, jargon-free
```

## API Endpoint Comparison

### OLD API (v1.0) - Generic Analysis
```
POST /api/v1/analyze-vcf
Content-Type: multipart/form-data

file: <VCF file>

// Returns: Array of results (one per drug per gene)
[
  { drug: "CODEINE", gene: "CYP2D6", risk: "Ineffective", llm_generated_explanation: { summary: "..." } },
  { drug: "WARFARIN", gene: "CYP2C19", risk: "Adjust Dosage", llm_generated_explanation: { summary: "..." } },
  ...
]
```

### NEW API (v2.0) - Selection-First
```
GET /api/v1/drugs
// Returns: { drugs: ["CODEINE", "WARFARIN", ...], count: 6 }

POST /api/v1/analyze-vcf?drug=CODEINE
Content-Type: multipart/form-data

file: <VCF file>
drug: CODEINE

// Returns: Single focused result
{
  drug: "CODEINE",
  gene: "CYP2D6",
  llm_generated_explanation: {
    clinical_summary: "Patient carries *4/*4...",
    patient_summary: "Your body has difficulty..."
  }
}
```

## UI Component Hierarchy

```
App (Main orchestrator)
├── Header (Logo, version, status)
├── Progress Indicators (1/2/3 stages with checkmarks)
├── Error Banner (if applicable)
├── Stage Router
│   ├── Stage 1: DrugSelector
│   │   └── Dropdown with 6 medications
│   ├── Stage 2: VCFUploader + Analysis Button
│   │   └── File drag-and-drop
│   └── Stage 3: ResultsDisplay
│       └── ResultCard component
│           ├── Risk Badge
│           ├── Clinical Recommendation
│           ├── Toggle: Clinical vs Patient
│           ├── Summary Display (with Copy button)
│           ├── Variants List
│           └── Download JSON Button
├── Info Panel (About PharmaGuard)
└── Footer (Copyright, disclaimer)
```

## State Management Flow

```
App Component State:
├── selectedDrug: "CODEINE" | null
├── file: File object | null
├── results: AnalysisResult | null
├── stage: "drug-selection" | "file-upload" | "results"
├── isLoading: true | false
└── error: "Error message" | null

Event Flows:
1. Drug selected → { selectedDrug: "CODEINE", stage: "file-upload" }
2. File selected → { file: vcfFile }
3. Analysis clicked → { isLoading: true }
4. Results received → { results: {...}, stage: "results", isLoading: false }
5. New Analysis → Reset all state to initial
```

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Frontend Build | 202.65 KB (gzip: 66.76 KB) | Production-optimized |
| VCF Parse Time | <100ms | Typical small VCF |
| Risk Assessment | ~50ms | In-memory lookup |
| LLM API Call | 2-5 seconds | OpenAI GPT-3.5-turbo |
| Total Analysis | 3-6 seconds | End-to-end |
| Drug Fetch | <50ms | Lightweight endpoint |

---

**Status: ✅ COMPLETE - Ready for Production Deployment**
