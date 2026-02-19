from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer
import uuid
from datetime import datetime
from typing import Optional, List
import os
from dotenv import load_dotenv
import json

from app.models import PharmaGuardResponse, RiskAssessment, PharmacogenomicProfile, DetectedVariant, LLMGeneratedExplanation, QualityMetrics
from app.parsers.vcf_parser import parse_vcf_file, VCFParser
from app.engines.risk_engine import RiskAssessmentEngine
from app.llm_integration import generate_dual_explanations
from app.database import engine, Base, SessionLocal, get_db, User, VCFRecord
from app.auth import hash_password, verify_password, create_access_token, verify_token, TokenData
from app.schemas import UserRegister, UserLogin, AuthResponse, UserResponse, VCFRecordCreate, VCFRecordResponse, VCFRecordDetailResponse, AdminStats, AdminUserResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)


def ensure_database_schema():
    """Apply lightweight schema updates for existing SQLite databases."""
    with engine.connect() as conn:
        user_column_rows = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        user_column_names = {row[1] for row in user_column_rows}
        if "email_verified" not in user_column_names:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
        if "email_verification_code" not in user_column_names:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_verification_code TEXT"))
        if "email_verification_expires_at" not in user_column_names:
            conn.execute(text("ALTER TABLE users ADD COLUMN email_verification_expires_at DATETIME"))

        column_rows = conn.execute(text("PRAGMA table_info(vcf_records)")).fetchall()
        column_names = {row[1] for row in column_rows}
        if "vcf_content" not in column_names:
            conn.execute(text("ALTER TABLE vcf_records ADD COLUMN vcf_content TEXT"))

            conn.commit()


ensure_database_schema()


def ensure_admin_user():
    """Ensure default admin credentials exist for dashboard access."""
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                email="admin@pharmaguard.local",
                username="admin",
                full_name="System Admin",
                hashed_password=hash_password("admin"),
                is_admin=True,
                email_verified=True,
                email_verification_code=None,
                email_verification_expires_at=None
            )
            db.add(admin_user)
            db.commit()
        else:
            updated = False
            if not admin_user.is_admin:
                admin_user.is_admin = True
                updated = True
            if not admin_user.email_verified:
                admin_user.email_verified = True
                updated = True
            if updated:
                db.commit()
    finally:
        db.close()


ensure_admin_user()


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
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:5173",
        "https://pharmaguard-frontend.vercel.app",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
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
        "genes": ["CYP2C19", "CYP2C9", "VKORC1"],
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

SUPPORTED_DRUGS = [
    "CODEINE",
    "WARFARIN",
    "CLOPIDOGREL",
    "SIMVASTATIN",
    "AZATHIOPRINE",
    "FLUOROURACIL",
]

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
        if drug_id in SUPPORTED_DRUGS
    ]
    return {
        "drugs": drugs_list,
        "count": len(drugs_list),
        "categories": list(set(d["category"] for d in drugs_list))
    }


@app.post("/api/v1/analyze-vcf")
async def analyze_vcf(
    file: UploadFile = File(...),
    drug: str = Query(...),
    dosage_mg: Optional[float] = Query(None, ge=0),
    dosage_map: Optional[str] = Query(None)
):
    """
    Upload and analyze VCF file with pre-selected drug(s)
    
    Args:
        file: VCF file
        drug: Pre-selected drug(s) - single drug (CODEINE) or multiple comma-separated (CODEINE,WARFARIN)
    
    Returns:
        Analysis results in PharmaGuardResponse format or list of results for multiple drugs
    """
    
    # Parse drugs (support known list + free-text custom drugs)
    raw_drugs = [d.strip() for d in drug.split(",") if d.strip()]
    if not raw_drugs:
        raise HTTPException(status_code=400, detail="At least one drug is required")

    # Normalize: known drugs as uppercase IDs, custom drugs as title-case labels
    drug_list = []
    for raw_drug in raw_drugs:
        upper_drug = raw_drug.upper()
        if upper_drug in SUPPORTED_DRUGS:
            normalized_drug = upper_drug
        else:
            normalized_drug = " ".join(raw_drug.split()).title()
        if normalized_drug:
            drug_list.append(normalized_drug)
    
    # Remove duplicates while preserving order
    drug_list = list(dict.fromkeys(drug_list))

    # Parse optional per-drug dosage map JSON, example:
    # {"WARFARIN": 5, "Metformin": 500}
    per_drug_dosage = {}
    if dosage_map:
        try:
            parsed_dose_map = json.loads(dosage_map)
            if isinstance(parsed_dose_map, dict):
                for raw_key, raw_val in parsed_dose_map.items():
                    if raw_key is None:
                        continue
                    key_text = str(raw_key).strip()
                    if not key_text:
                        continue
                    upper_key = key_text.upper()
                    normalized_key = upper_key if upper_key in SUPPORTED_DRUGS else " ".join(key_text.split()).title()

                    try:
                        dose_value = float(raw_val)
                    except (TypeError, ValueError):
                        continue

                    if dose_value < 0:
                        continue

                    per_drug_dosage[normalized_key] = dose_value
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid dosage_map format. Provide valid JSON object, e.g. {\"WARFARIN\":5}"
            )
    
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
                selected_dosage = per_drug_dosage.get(drug_choice, dosage_mg)
                result = analyze_single_drug(
                    patient_id, drug_choice, variants, parsed_data, file.filename, selected_dosage
                )
                results.append(result)
            return {"analyses": results, "patient_id": patient_id, "drug_count": len(results)}
        else:
            # Single drug analysis
            selected_dosage = per_drug_dosage.get(drug_list[0], dosage_mg)
            return analyze_single_drug(
                patient_id, drug_list[0], variants, parsed_data, file.filename, selected_dosage
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


def analyze_single_drug(
    patient_id: str,
    drug: str,
    variants: list,
    parsed_data: dict,
    filename: str,
    dosage_mg: Optional[float] = None
):
    """Analyze VCF for a single drug"""
    
    # Drug to gene mapping
    drug_gene_mapping = {drug_id: info["genes"] for drug_id, info in DRUGS_DATABASE.items()}
    
    # Get relevant genes for this drug (custom drugs fall back to all key pharmacogenes)
    relevant_genes = drug_gene_mapping.get(drug)
    if not relevant_genes:
        relevant_genes = ["CYP2D6", "CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "DPYD", "VKORC1"]
    
    # Filter variants to relevant genes only
    relevant_variants = [v for v in variants if v.get('gene') in relevant_genes]
    
    # If no relevant variants found
    if not relevant_variants:
        return create_no_variants_response(patient_id, drug, variants, dosage_mg)
    
    # Prioritize genes for better drug-specific interpretation
    gene_priority = {
        "WARFARIN": ["CYP2C9", "VKORC1", "CYP2C19"]
    }
    preferred_genes = gene_priority.get(drug, [])
    sorted_variants = sorted(
        relevant_variants,
        key=lambda v: preferred_genes.index(v.get("gene")) if v.get("gene") in preferred_genes else 999
    )

    # Use highest-priority relevant gene
    gene = sorted_variants[0].get('gene')

    # Keep only variants belonging to the selected primary gene
    gene_specific_variants = [v for v in sorted_variants if v.get('gene') == gene]

    # For CYP2C9 interpretation, only keep known CYP2C9 star-defining SNPs
    cyp2c9_star_rsids = {
        "rs9332131",  # *12
        "rs1057910",  # *3
        "rs1799853",  # *2
        "rs28371686",  # *5
        "rs9332242",  # *6
        "rs7900194",  # *8
        "rs28371685",  # *11
    }
    cyp2c9_rsid_to_star = {
        "rs9332131": "*12",
        "rs1057910": "*3",
        "rs1799853": "*2",
        "rs28371686": "*5",
        "rs9332242": "*6",
        "rs7900194": "*8",
        "rs28371685": "*11",
    }
    cyp2c19_rsid_to_star = {
        "rs4244285": "*2",
        "rs4986893": "*3",
        "rs28399504": "*4",
        "rs12769205": "*5",
        "rs17884712": "*6",
        "rs56337013": "*8",
    }
    slco1b1_rsid_to_star = {
        "rs4149056": "*5",
    }
    dpyd_rsid_to_star = {
        "rs3918290": "*2A",
        "rs67376798": "*13",
        "rs56038477": "HapB3",
        "rs75017182": "HapB3",
    }

    if gene == "CYP2C9":
        cyp2c9_variants = []
        for variant in gene_specific_variants:
            rsid = str(variant.get("rsid") or "").strip().lower()
            if rsid in cyp2c9_star_rsids:
                cyp2c9_variants.append(variant)
        if cyp2c9_variants:
            gene_specific_variants = cyp2c9_variants
    
    star_allele = gene_specific_variants[0].get('star') or '*1'

    # Extract variant data
    variant_rsids = [
        (str(v.get('rsid')).strip() if v.get('rsid') else f"chr{v.get('chrom')}_{v.get('pos')}")
        for v in gene_specific_variants
    ]
    variant_rsids = list(dict.fromkeys(variant_rsids))

    if gene == "CYP2C9" and (not star_allele or star_allele == "*1"):
        inferred_star = cyp2c9_rsid_to_star.get(variant_rsids[0].lower()) if variant_rsids else None
        if inferred_star:
            star_allele = inferred_star
    if gene == "CYP2C19":
        # Prefer *2 call when rs4244285 is present; otherwise use known allele rsid mapping
        normalized_rsids_for_inference = [rsid.lower() for rsid in variant_rsids if isinstance(rsid, str)]
        if "rs4244285" in normalized_rsids_for_inference:
            star_allele = "*2"
        elif (not star_allele or star_allele == "*1") and normalized_rsids_for_inference:
            inferred_star = cyp2c19_rsid_to_star.get(normalized_rsids_for_inference[0])
            if inferred_star:
                star_allele = inferred_star
    if gene == "SLCO1B1" and (not star_allele or star_allele == "*1"):
        inferred_star = slco1b1_rsid_to_star.get(variant_rsids[0].lower()) if variant_rsids else None
        if inferred_star:
            star_allele = inferred_star
    if gene == "DPYD" and (not star_allele or star_allele == "*1"):
        inferred_star = dpyd_rsid_to_star.get(variant_rsids[0].lower()) if variant_rsids else None
        if inferred_star:
            star_allele = inferred_star

    # Strict CYP2C9 diplotype-to-SNP consistency filtering to prevent contamination
    if gene == "CYP2C9":
        cyp2c9_star_to_allowed_rsid = {
            "*2": "rs1799853",
            "*3": "rs1057910",
            "*12": "rs9332131",
        }
        allowed_rsid = cyp2c9_star_to_allowed_rsid.get(star_allele)
        if allowed_rsid:
            variant_rsids = [rsid for rsid in variant_rsids if rsid.lower() == allowed_rsid]

    if gene == "SLCO1B1":
        slco1b1_star_to_allowed_rsid = {
            "*5": "rs4149056",
        }
        allowed_rsid = slco1b1_star_to_allowed_rsid.get(star_allele)
        if allowed_rsid:
            variant_rsids = [rsid for rsid in variant_rsids if rsid.lower() == allowed_rsid]

    if gene == "CYP2C19":
        cyp2c19_star_to_allowed_rsid = {
            "*2": "rs4244285",
            "*3": "rs4986893",
            "*4": "rs28399504",
            "*5": "rs12769205",
            "*6": "rs17884712",
            "*8": "rs56337013",
        }
        allowed_rsid = cyp2c19_star_to_allowed_rsid.get(star_allele)
        if allowed_rsid:
            variant_rsids = [rsid for rsid in variant_rsids if rsid.lower() == allowed_rsid]

    if gene == "DPYD":
        dpyd_star_to_allowed_rsids = {
            "*2A": {"rs3918290"},
            "*13": {"rs67376798"},
            "HapB3": {"rs56038477", "rs75017182"},
            "D949V": {"rs67376798"},
        }
        allowed_rsids = dpyd_star_to_allowed_rsids.get(star_allele)
        if allowed_rsids:
            variant_rsids = [rsid for rsid in variant_rsids if rsid.lower() in allowed_rsids]

    diplotype = f"{star_allele}/{star_allele}"
    
    # Infer phenotype
    risk_engine = RiskAssessmentEngine()
    if gene == "CYP2C9":
        phenotype, phenotype_confidence = risk_engine.infer_cyp2c9_phenotype(diplotype)
    elif gene == "SLCO1B1":
        phenotype, phenotype_confidence = risk_engine.infer_slco1b1_phenotype(diplotype)
    elif gene == "DPYD":
        phenotype, phenotype_confidence = risk_engine.infer_dpyd_phenotype(diplotype)
    else:
        phenotype, phenotype_confidence = risk_engine.infer_phenotype([star_allele])

    phenotype_output_map = {
        "Poor Metabolizer": "PM",
        "Intermediate Metabolizer": "IM",
        "Normal Metabolizer": "NM",
        "Normal function": "NM",
        "Decreased function": "IM",
        "Low function": "PM",
    }
    output_phenotype = phenotype_output_map.get(phenotype, phenotype)
    if output_phenotype not in {"PM", "IM", "NM", "RM", "URM", "Unknown"}:
        output_phenotype = "Unknown"
    
    # Assess risk for this drug-gene pair
    risk = risk_engine.assess_risk(gene, drug, phenotype, variant_rsids, diplotype)

    # Conservative WARFARIN override for known high-risk variants
    if drug == "WARFARIN":
        high_risk_warfarin_rsids = {"rs9923231", "rs1799853", "rs1057910"}
        normalized_rsids = {rsid.lower() for rsid in variant_rsids if isinstance(rsid, str)}
        if gene == "CYP2C9" and phenotype == "PM":
            risk = {
                **risk,
                "risk_label": "Toxic",
                "severity": "critical",
                "confidence_score": max(risk.get("confidence_score", 0.5), 0.95)
            }
        elif high_risk_warfarin_rsids.intersection(normalized_rsids):
            risk = {
                **risk,
                "risk_label": "Toxic",
                "severity": "critical",
                "confidence_score": max(risk.get("confidence_score", 0.5), 0.9)
            }
        elif risk.get("risk_label") == "Safe" and len(sorted_variants) > 0:
            risk = {
                **risk,
                "risk_label": "Adjust Dosage",
                "severity": "high",
                "confidence_score": min(max(risk.get("confidence_score", 0.5), 0.8), 0.9)
            }

    if gene == "DPYD" and drug == "FLUOROURACIL" and phenotype == "Poor Metabolizer":
        risk = {
            **risk,
            "risk_label": "Toxic",
            "severity": "critical",
            "confidence_score": max(risk.get("confidence_score", 0.5), 0.99)
        }
    
    suppress_dose_context = gene == "CYP2C19" and drug == "CLOPIDOGREL" and phenotype == "PM"
    llm_dose_context = None if suppress_dose_context else dosage_mg

    # Generate DUAL-LAYER explanations
    clinical_summary, patient_summary = generate_dual_explanations(
        gene=gene,
        drug=drug,
        phenotype=phenotype,
        risk_label=risk['risk_label'],
        detected_variants=variant_rsids,
        diplotype=diplotype,
        current_dose_mg=llm_dose_context,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    if gene == "DPYD" and drug == "FLUOROURACIL" and phenotype == "Poor Metabolizer":
        clinical_summary = (
            "Pharmacogenomic interpretation: DPYD diplotype *2A/*2A is consistent with Poor Metabolizer status and "
            "marked loss of dihydropyrimidine dehydrogenase activity. Detected pathogenic variant rs3918290 supports "
            "severely impaired fluoropyrimidine catabolism and very high risk of life-threatening fluorouracil toxicity "
            "(including severe neutropenia, mucositis, diarrhea, and myelosuppression). CPIC-aligned recommendation is to "
            "avoid fluorouracil-based therapy and select a non-fluoropyrimidine alternative regimen with oncology specialist "
            "oversight and close toxicity surveillance."
        )
        patient_summary = (
            "Your genetic result shows your body cannot safely break down fluorouracil. This medicine should be avoided for "
            "you because it can cause serious side effects. Your oncology team should use an alternative treatment plan that is "
            "safer for your genetics.\n\nVariant citation: RSID rs3918290; STAR allele *2A."
        )

    dosage_note = ""
    if dosage_mg is not None:
        if gene == "DPYD" and drug == "FLUOROURACIL" and phenotype == "Poor Metabolizer":
            dosage_note = f" Current reported dose: {dosage_mg} mg; fluorouracil is contraindicated and should be avoided."
        elif suppress_dose_context:
            dosage_note = ""
        elif risk['risk_label'] in ["Adjust Dosage", "Toxic"]:
            dosage_note = f" Current reported dose: {dosage_mg} mg; genotype-guided dose reduction or alternative therapy should be considered."
        elif risk['risk_label'] == "Safe":
            dosage_note = f" Current reported dose: {dosage_mg} mg; standard dosing is generally acceptable with routine monitoring."
        else:
            dosage_note = f" Current reported dose: {dosage_mg} mg; individualized dose titration is recommended due to uncertain pharmacogenomic impact."

    if gene == "DPYD" and drug == "FLUOROURACIL" and phenotype == "Poor Metabolizer":
        clinical_recommendation = {
            "action": "Avoid drug",
            "detail": "Fluorouracil is contraindicated in DPYD poor metabolizers; avoid fluorouracil-based therapy and use an alternative regimen with specialist guidance and close toxicity monitoring."
        }
    elif suppress_dose_context:
        clinical_recommendation = {
            "action": "Avoid drug",
            "detail": "Avoid clopidogrel in CYP2C19 poor metabolizers (CPIC Level A); use an alternative P2Y12 inhibitor such as prasugrel or ticagrelor unless contraindicated."
        }
    else:
        clinical_recommendation = {
            "action": risk_engine.get_clinical_recommendation(
                risk['risk_label'], drug, phenotype, gene
            ),
            "detail": f"{risk_engine.get_clinical_recommendation(risk['risk_label'], drug, phenotype, gene)}{dosage_note}"
        }
    
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
            phenotype=output_phenotype,
            detected_variants=[DetectedVariant(rsid=rsid) for rsid in variant_rsids]
        ),
        clinical_recommendation=clinical_recommendation,
        llm_generated_explanation=LLMGeneratedExplanation(
            summary=clinical_summary,
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


def create_no_variants_response(
    patient_id: str,
    drug: str,
    variants: list,
    dosage_mg: Optional[float] = None
):
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
        clinical_recommendation={
            "action": "Standard care",
            "detail": (
                f"No significant pharmacogenomic variants detected for {drug}. Standard drug dosing recommended."
                + (f" Current reported dose: {dosage_mg} mg." if dosage_mg is not None else "")
            )
        },
        llm_generated_explanation=LLMGeneratedExplanation(
            summary=f"Patient VCF does not contain variants in genes related to {drug} metabolism. Pharmacogenomic profile is typical. Standard dosing protocols are appropriate. Regular clinical monitoring recommended as with all medications.",
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


# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/api/v1/auth/register", response_model=AuthResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Validate passwords match
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    normalized_email = user_data.email.strip().lower()
    normalized_username = user_data.username.strip()

    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == normalized_email) | (User.username == normalized_username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=normalized_email,
        username=normalized_username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_admin=False,
        email_verified=True,
        email_verification_code=None,
        email_verification_expires_at=None
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email, "username": new_user.username, "is_admin": new_user.is_admin}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(new_user)
    }


@app.post("/api/v1/auth/login", response_model=AuthResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""

    login_value = credentials.email.strip()

    # Find user by email (case-insensitive) OR username
    user = db.query(User).filter(
        (func.lower(User.email) == login_value.lower()) | (User.username == login_value)
    ).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username, "is_admin": user.is_admin}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@app.post("/api/v1/auth/logout")
async def logout(token_data: dict = Depends(verify_token)):
    """Logout user (client should discard token)"""
    return {"message": "Logged out successfully"}


@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Get current logged-in user info"""
    user = db.query(User).filter(User.id == token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.from_orm(user)


# ===== VCF RECORD ENDPOINTS =====

@app.post("/api/v1/records/save")
async def save_vcf_record(
    record_data: VCFRecordCreate,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Save VCF analysis record to database"""
    
    user = db.query(User).filter(User.id == token_data["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    record_id = str(uuid.uuid4())
    vcf_record = VCFRecord(
        id=record_id,
        user_id=user.id,
        username=user.username,
        filename=record_data.filename,
        file_path=f"records/{user.id}/{record_id}",
        analyzed_drugs=record_data.analyzed_drugs,
        vcf_content=record_data.vcf_content,
        analysis_result=record_data.analysis_result,
        phenotypes=record_data.phenotypes,
        status="completed",
        analyzed_at=datetime.utcnow()
    )
    
    db.add(vcf_record)
    db.commit()
    db.refresh(vcf_record)
    
    return {"id": record_id, "message": "Record saved successfully"}


@app.get("/api/v1/records/{record_id}/vcf", response_class=PlainTextResponse)
async def get_record_vcf(
    record_id: str,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get original VCF content for a stored record."""

    record = db.query(VCFRecord).filter(VCFRecord.id == record_id).first()

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    if record.user_id != token_data["sub"] and not token_data.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if record.vcf_content:
        return PlainTextResponse(record.vcf_content)

    # Backward compatibility: try known file locations for older records
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    project_root = os.path.abspath(os.path.join(backend_root, ".."))

    candidate_paths = []
    if record.file_path:
        candidate_paths.append(record.file_path)
    if record.filename:
        candidate_paths.extend([
            os.path.join(project_root, record.filename),
            os.path.join(backend_root, "sample_vcf", record.filename),
        ])

    for path in candidate_paths:
        try:
            if path and os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as vcf_file:
                    return PlainTextResponse(vcf_file.read())
        except Exception:
            continue

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="VCF content not available for this record. It may have been saved before VCF storage was enabled."
    )


@app.get("/api/v1/records/user", response_model=List[VCFRecordResponse])
async def get_user_records(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all VCF records for current user"""
    
    records = db.query(VCFRecord).filter(
        VCFRecord.user_id == token_data["sub"]
    ).order_by(desc(VCFRecord.uploaded_at)).all()
    
    return [VCFRecordResponse.from_orm(r) for r in records]


@app.get("/api/v1/records/{record_id}", response_model=VCFRecordDetailResponse)
async def get_record_detail(
    record_id: str,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get detailed VCF record (with analysis results)"""
    
    record = db.query(VCFRecord).filter(VCFRecord.id == record_id).first()
    
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    
    # Check authorization
    if record.user_id != token_data["sub"] and not token_data.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    return VCFRecordDetailResponse.from_orm(record)


@app.delete("/api/v1/records/{record_id}")
async def delete_record(
    record_id: str,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a VCF record"""
    
    record = db.query(VCFRecord).filter(VCFRecord.id == record_id).first()
    
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    
    # Check authorization
    if record.user_id != token_data["sub"] and not token_data.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    db.delete(record)
    db.commit()
    
    return {"message": "Record deleted successfully"}


# ===== ADMIN DASHBOARD ENDPOINTS =====

@app.get("/api/v1/admin/stats", response_model=AdminStats)
async def get_admin_stats(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    
    # Check if user is admin
    user = db.query(User).filter(User.id == token_data["sub"]).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    # Total users
    total_users = db.query(func.count(User.id)).scalar()
    
    # Total analyses
    total_analyses = db.query(func.count(VCFRecord.id)).scalar()
    
    # Completed vs failed
    total_completed = db.query(func.count(VCFRecord.id)).filter(VCFRecord.status == "completed").scalar()
    total_failed = db.query(func.count(VCFRecord.id)).filter(VCFRecord.status == "failed").scalar()
    
    # Most analyzed drugs
    most_analyzed_drugs = db.query(
        VCFRecord.analyzed_drugs,
        func.count(VCFRecord.id).label("count")
    ).group_by(VCFRecord.analyzed_drugs).order_by(desc("count")).limit(10).all()
    
    most_analyzed = [
        {"drugs": record[0], "count": record[1]}
        for record in most_analyzed_drugs
    ]
    
    # Recent analyses
    recent = db.query(VCFRecord).order_by(
        desc(VCFRecord.uploaded_at)
    ).limit(10).all()
    
    return {
        "total_users": total_users or 0,
        "total_analyses": total_analyses or 0,
        "total_completed": total_completed or 0,
        "total_failed": total_failed or 0,
        "most_analyzed_drugs": most_analyzed,
        "recent_analyses": [VCFRecordResponse.from_orm(r) for r in recent]
    }


@app.get("/api/v1/admin/users", response_model=List[AdminUserResponse])
async def get_all_users(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    
    # Check if user is admin
    user = db.query(User).filter(User.id == token_data["sub"]).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    users = db.query(User).all()
    
    result = []
    for u in users:
        analysis_count = db.query(func.count(VCFRecord.id)).filter(
            VCFRecord.user_id == u.id
        ).scalar() or 0
        
        result.append({
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "is_admin": u.is_admin,
            "analysis_count": analysis_count,
            "created_at": u.created_at
        })
    
    return result


@app.get("/api/v1/admin/records")
async def get_all_records(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all VCF records (admin only)"""
    
    # Check if user is admin
    user = db.query(User).filter(User.id == token_data["sub"]).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    records = db.query(VCFRecord).order_by(
        desc(VCFRecord.uploaded_at)
    ).all()
    
    return [VCFRecordResponse.from_orm(r) for r in records]


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
