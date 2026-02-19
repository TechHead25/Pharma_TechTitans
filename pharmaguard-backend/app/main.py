from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
from typing import Optional, List
import os
from dotenv import load_dotenv

from app.models import PharmaGuardResponse, RiskAssessment, PharmacogenomicProfile, DetectedVariant, LLMGeneratedExplanation, QualityMetrics
from app.parsers.vcf_parser import parse_vcf_file, VCFParser
from app.engines.risk_engine import RiskAssessmentEngine
from app.llm_integration import generate_dual_explanations

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="PharmaGuard",
    description="Pharmacogenomic Risk Prediction Engine",
    version="2.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "https://pharmaguard-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supported drugs for selection-first workflow with professional metadata
DRUGS_DATABASE = {
    "CODEINE": {
        "name": "Codeine",
        "category": "Analgesic (Opioid)",
        "genes": ["CYP2D6"],
        "description": "Opioid pain reliever"
    },
    "WARFARIN": {
        "name": "Warfarin",
        "category": "Anticoagulant",
        "genes": ["CYP2C19", "CYP2C9"],
        "description": "Blood thinner for stroke/clot prevention"
    },
    "CLOPIDOGREL": {
        "name": "Clopidogrel (Plavix)",
        "category": "Antiplatelet",
        "genes": ["CYP2C19"],
        "description": "Antiplatelet agent for cardiovascular events"
    },
    "SIMVASTATIN": {
        "name": "Simvastatin",
        "category": "Statin (Lipid-Lowering)",
        "genes": ["SLCO1B1"],
        "description": "Cholesterol management"
    },
    "AZATHIOPRINE": {
        "name": "Azathioprine",
        "category": "Immunosuppressant",
        "genes": ["TPMT"],
        "description": "Immune system suppressor for autoimmune conditions"
    },
    "FLUOROURACIL": {
        "name": "Fluorouracil (5-FU)",
        "category": "Chemotherapy",
        "genes": ["DPYD"],
        "description": "Anticancer agent"
    },
    "METOPROLOL": {
        "name": "Metoprolol",
        "category": "Beta-Blocker",
        "genes": ["CYP2D6"],
        "description": "Blood pressure & heart rate control"
    },
    "ATENOLOL": {
        "name": "Atenolol",
        "category": "Beta-Blocker",
        "genes": ["CYP2D6"],
        "description": "Hypertension and angina management"
    },
    "SERTRALINE": {
        "name": "Sertraline (Zoloft)",
        "category": "SSRI (Antidepressant)",
        "genes": ["CYP2D6", "CYP2C19"],
        "description": "Depression and anxiety treatment"
    },
    "ESCITALOPRAM": {
        "name": "Escitalopram (Lexapro)",
        "category": "SSRI (Antidepressant)",
        "genes": ["CYP2C19"],
        "description": "Depression and anxiety management"
    },
    "TOPIRAMATE": {
        "name": "Topiramate (Topamax)",
        "category": "Anticonvulsant",
        "genes": ["CYP2D6"],
        "description": "Seizure control and migraine prevention"
    },
    "PHENYTOIN": {
        "name": "Phenytoin (Dilantin)",
        "category": "Anticonvulsant",
        "genes": ["CYP2C19", "CYP2C9"],
        "description": "Seizure prevention"
    },
}

SUPPORTED_DRUGS = list(DRUGS_DATABASE.keys())

# In-memory storage for results (in production, use database)
analysis_results = {}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "active",
        "service": "PharmaGuard Pharmacogenomic Risk Prediction",
        "version": "2.0.0",
    }


@app.get("/api/v1/drugs")
async def get_supported_drugs():
    """Get list of supported drugs with metadata"""
    drugs_list = [
        {
            "id": drug_id,
            **drug_info
        }
        for drug_id, drug_info in DRUGS_DATABASE.items()
    ]
    return {
        "drugs": drugs_list,
        "count": len(drugs_list),
        "categories": list(set(d["category"] for d in drugs_list))
    }


@app.post("/api/v1/analyze-vcf")
async def analyze_vcf(file: UploadFile = File(...), drug: str = Query(...)):
    """
    Upload and analyze VCF file with pre-selected drug(s)
    
    Args:
        file: VCF file
        drug: Pre-selected drug(s) - single drug (CODEINE) or multiple comma-separated (CODEINE,WARFARIN)
    
    Returns:
        Analysis results in PharmaGuardResponse format or list of results for multiple drugs
    """
    
    # Parse drugs (support both single and comma-separated)
    drug_list = [d.strip().upper() for d in drug.split(",")]
    
    # Validate drug selections
    invalid_drugs = [d for d in drug_list if d not in SUPPORTED_DRUGS]
    if invalid_drugs:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid drugs: {', '.join(invalid_drugs)}. Supported: {', '.join(SUPPORTED_DRUGS[:6])}..."
        )
    
    # Remove duplicates while preserving order
    drug_list = list(dict.fromkeys(drug_list))
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
            
        if not file.filename.endswith('.vcf'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: '{file.filename}'. Must be .vcf file"
            )
        
        # Read file content
        content = await file.read()
        
        # Check for empty file
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Check file size (5 MB limit)
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > 5:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size_mb:.2f} MB (max 5 MB)"
            )
        
        # Decode content
        try:
            vcf_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400, 
                detail="File encoding error: must be valid UTF-8"
            )
        
        # Check if file has minimum content
        if len(vcf_content.strip()) < 10:
            raise HTTPException(status_code=400, detail="VCF file is too small or invalid")
        
        # Parse VCF
        parsed_data, success = parse_vcf_file(vcf_content)
        
        if not success:
            error_msg = parsed_data.get('error', 'Unknown parsing error')
            raise HTTPException(
                status_code=400,
                detail=f"VCF parsing failed: {error_msg}"
            )
        
        # Generate patient ID
        patient_id = f"PAT-{uuid.uuid4().hex[:12].upper()}"
        
        # Extract variants
        variants = parsed_data.get('variants', [])
        target_genes = parsed_data.get('target_genes_found', [])
        
        # If multiple drugs, return list of results
        if len(drug_list) > 1:
            results = []
            for drug_choice in drug_list:
                result = analyze_single_drug(
                    patient_id, drug_choice, variants, parsed_data, file.filename
                )
                results.append(result)
            return {"analyses": results, "patient_id": patient_id, "drug_count": len(results)}
        else:
            # Single drug analysis
            return analyze_single_drug(
                patient_id, drug_list[0], variants, parsed_data, file.filename
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


def analyze_single_drug(patient_id: str, drug: str, variants: list, parsed_data: dict, filename: str):
    """Analyze VCF for a single drug"""
    
    # Drug to gene mapping
    drug_gene_mapping = {drug_id: info["genes"] for drug_id, info in DRUGS_DATABASE.items()}
    
    # Get relevant genes for this drug
    relevant_genes = drug_gene_mapping.get(drug, [])
    
    # Filter variants to relevant genes only
    relevant_variants = [v for v in variants if v.get('gene') in relevant_genes]
    
    # If no relevant variants found
    if not relevant_variants:
        return create_no_variants_response(patient_id, drug, variants)
    
    # Get the first relevant gene found
    gene = relevant_variants[0].get('gene')
    
    # Extract variant data
    variant_rsids = [v.get('rsid') or f"chr{v.get('chrom')}_{v.get('pos')}" for v in relevant_variants if v.get('rsid')]
    star_allele = relevant_variants[0].get('star') or '*1'
    diplotype = f"{star_allele}/{star_allele}"
    
    # Infer phenotype
    risk_engine = RiskAssessmentEngine()
    phenotype, phenotype_confidence = risk_engine.infer_phenotype([star_allele])
    
    # Assess risk for this drug-gene pair
    risk = risk_engine.assess_risk(gene, drug, phenotype, variant_rsids, diplotype)
    
    # Generate DUAL-LAYER explanations
    clinical_summary, patient_summary = generate_dual_explanations(
        gene=gene,
        drug=drug,
        phenotype=phenotype,
        risk_label=risk['risk_label'],
        detected_variants=variant_rsids,
        diplotype=diplotype,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create response
    response = PharmaGuardResponse(
        patient_id=patient_id,
        drug=drug,
        timestamp=datetime.utcnow().isoformat() + "Z",
        risk_assessment=RiskAssessment(
            risk_label=risk['risk_label'],
            confidence_score=risk['confidence_score'],
            severity=risk['severity']
        ),
        pharmacogenomic_profile=PharmacogenomicProfile(
            primary_gene=gene,
            diplotype=diplotype,
            phenotype=phenotype,
            detected_variants=[DetectedVariant(rsid=rsid) for rsid in variant_rsids]
        ),
        clinical_recommendation=risk_engine.get_clinical_recommendation(
            risk['risk_label'], drug, phenotype
        ),
        llm_generated_explanation=LLMGeneratedExplanation(
            clinical_summary=clinical_summary,
            patient_summary=patient_summary
        ),
        quality_metrics=QualityMetrics(
            vcf_parsing_success=True
        )
    )
    
    # Store results
    analysis_results[patient_id] = {
        "timestamp": datetime.utcnow().isoformat(),
        "assessment": response.model_dump(),
        "file_name": filename,
    }
    
    return response


def create_no_variants_response(patient_id: str, drug: str, variants: list):
    """Create a safe response when no target variants found"""
    return PharmaGuardResponse(
        patient_id=patient_id,
        drug=drug,
        timestamp=datetime.utcnow().isoformat() + "Z",
        risk_assessment=RiskAssessment(
            risk_label="Safe",
            confidence_score=0.6,
            severity="none"
        ),
        pharmacogenomic_profile=PharmacogenomicProfile(
            primary_gene="No Target Genes",
            diplotype="*1/*1",
            phenotype="Unknown",
            detected_variants=[]
        ),
        clinical_recommendation=f"No significant pharmacogenomic variants detected for {drug}. Standard drug dosing recommended.",
        llm_generated_explanation=LLMGeneratedExplanation(
            clinical_summary=f"Patient VCF does not contain variants in genes related to {drug} metabolism. Pharmacogenomic profile is typical. Standard dosing protocols are appropriate. Regular clinical monitoring recommended as with all medications.",
            patient_summary=f"Your genetic test shows you process {drug} normally, just like most people. Your doctor can prescribe the standard dose with confidence. All the normal safety studies apply to you!"
        ),
        quality_metrics=QualityMetrics(
            vcf_parsing_success=True
        )
    )


@app.get("/api/v1/results/{patient_id}")
async def get_results(patient_id: str):
    """Retrieve analysis results for a patient"""
    if patient_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return analysis_results[patient_id]


@app.post("/api/v1/validate-vcf")
async def validate_vcf(file: UploadFile = File(...)):
    """Validate VCF file with detailed error reporting"""
    
    try:
        if not file:
            return {
                "valid": False,
                "error": "No file provided",
                "errorCode": "NO_FILE",
                "size_mb": 0
            }
        
        if not file.filename:
            return {
                "valid": False,
                "error": "File has no name",
                "errorCode": "NO_FILENAME",
                "size_mb": 0
            }
        
        # Check file extension
        if not file.filename.lower().endswith('.vcf'):
            return {
                "valid": False,
                "error": f"Invalid file type: '{file.filename}'. Expected .vcf file",
                "errorCode": "INVALID_EXTENSION",
                "size_mb": 0,
                "file_name": file.filename
            }
        
        # Read file content
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        # Check for empty file
        if len(content) == 0:
            return {
                "valid": False,
                "error": "File is empty",
                "errorCode": "EMPTY_FILE",
                "size_mb": 0,
                "file_name": file.filename
            }
        
        # Check file size
        if file_size_mb > 5:
            return {
                "valid": False,
                "error": f"File too large: {file_size_mb:.2f} MB (maximum 5 MB)",
                "errorCode": "FILE_TOO_LARGE",
                "size_mb": file_size_mb,
                "file_name": file.filename
            }
        
        # Try to decode
        try:
            vcf_content = content.decode('utf-8')
        except UnicodeDecodeError as e:
            return {
                "valid": False,
                "error": f"File encoding error: unable to decode as UTF-8. Try saving as UTF-8 text.",
                "errorCode": "ENCODING_ERROR",
                "size_mb": file_size_mb,
                "file_name": file.filename,
                "details": str(e)
            }
        
        # Check if file has minimum content
        if len(vcf_content.strip()) < 10:
            return {
                "valid": False,
                "error": "VCF file is too small or contains only whitespace",
                "errorCode": "CONTENT_TOO_SMALL",
                "size_mb": file_size_mb,
                "file_name": file.filename
            }
        
        # Validate VCF structure
        parser = VCFParser()
        is_valid, message = parser.validate_vcf_structure(vcf_content)
        
        # Count variants
        variant_count = sum(1 for line in vcf_content.split('\n') if line and not line.startswith('#'))
        
        return {
            "valid": is_valid,
            "message": message,
            "size_mb": file_size_mb,
            "file_name": file.filename,
            "variant_count": variant_count,
            "errorCode": None if is_valid else "INVALID_VCF_STRUCTURE"
        }
    
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "errorCode": "VALIDATION_ERROR",
            "size_mb": 0
        }


@app.get("/api/v1/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PharmaGuard"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
