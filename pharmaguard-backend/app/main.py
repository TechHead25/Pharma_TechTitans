from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
import os
import random
from dotenv import load_dotenv
import json
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models import PharmaGuardResponse, RiskAssessment, PharmacogenomicProfile, DetectedVariant, LLMGeneratedExplanation, QualityMetrics
from app.parsers.vcf_parser import parse_vcf_file, VCFParser
from app.engines.risk_engine import RiskAssessmentEngine
from app.llm_integration import generate_dual_explanations
from app.database import engine, Base, SessionLocal, get_db, User, VCFRecord
from app.auth import hash_password, verify_password, create_access_token, verify_token, TokenData
from app.schemas import UserRegister, UserLogin, AuthResponse, RegisterResponse, VerifyEmailRequest, ResendVerificationRequest, UserResponse, VCFRecordCreate, VCFRecordResponse, VCFRecordDetailResponse, AdminStats, AdminUserResponse
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


def generate_verification_code() -> str:
    return f"{random.randint(100000, 999999)}"


# Email configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@pharmaguard.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "PharmaGuard")

# Check if SMTP is configured
SMTP_ENABLED = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


async def send_verification_email(email: str, code: str) -> bool:
    """Send verification code via email. Returns True if sent successfully, False if SMTP not configured."""
    if not SMTP_ENABLED:
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "PharmaGuard Email Verification"
        message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        message["To"] = email
        
        # Email body
        text = f"""
Hello,

Your PharmaGuard verification code is: {code}

This code will expire in 24 hours.

If you didn't request this verification code, please ignore this email.

Best regards,
PharmaGuard Team
        """
        
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #4F46E5;">Email Verification</h2>
      <p>Hello,</p>
      <p>Your PharmaGuard verification code is:</p>
      <div style="background-color: #F3F4F6; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
        <span style="font-size: 32px; font-weight: bold; color: #4F46E5; letter-spacing: 8px;">{code}</span>
      </div>
      <p>This code will expire in 24 hours.</p>
      <p style="color: #6B7280; font-size: 14px; margin-top: 30px;">
        If you didn't request this verification code, please ignore this email.
      </p>
      <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 30px 0;">
      <p style="color: #6B7280; font-size: 12px;">
        Best regards,<br>
        PharmaGuard Team
      </p>
    </div>
  </body>
</html>
        """
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

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
    
    # Prioritize genes for better drug-specific interpretation
    gene_priority = {
        "WARFARIN": ["VKORC1", "CYP2C9", "CYP2C19"]
    }
    preferred_genes = gene_priority.get(drug, [])
    sorted_variants = sorted(
        relevant_variants,
        key=lambda v: preferred_genes.index(v.get("gene")) if v.get("gene") in preferred_genes else 999
    )

    # Use highest-priority relevant gene
    gene = sorted_variants[0].get('gene')
    
    # Extract variant data
    variant_rsids = [v.get('rsid') or f"chr{v.get('chrom')}_{v.get('pos')}" for v in sorted_variants]
    star_allele = sorted_variants[0].get('star') or '*1'
    diplotype = f"{star_allele}/{star_allele}"
    
    # Infer phenotype
    risk_engine = RiskAssessmentEngine()
    phenotype, phenotype_confidence = risk_engine.infer_phenotype([star_allele])
    
    # Assess risk for this drug-gene pair
    risk = risk_engine.assess_risk(gene, drug, phenotype, variant_rsids, diplotype)

    # Conservative WARFARIN override for known high-risk variants
    if drug == "WARFARIN":
        high_risk_warfarin_rsids = {"rs9923231", "rs1799853", "rs1057910"}
        normalized_rsids = {rsid.lower() for rsid in variant_rsids if isinstance(rsid, str)}
        if high_risk_warfarin_rsids.intersection(normalized_rsids):
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


# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/api/v1/auth/register", response_model=RegisterResponse)
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
    verification_code = generate_verification_code()
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=normalized_email,
        username=normalized_username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_admin=False,
        email_verified=False,
        email_verification_code=verification_code,
        email_verification_expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send verification email if SMTP is configured
    email_sent = await send_verification_email(new_user.email, verification_code)
    
    return {
        "message": "Please check your email for the verification code." if email_sent else "Registration successful. Please verify your email with the 6-digit code.",
        "requires_verification": True,
        "email": new_user.email,
        "dev_verification_code": None if email_sent else verification_code
    }


@app.post("/api/v1/auth/verify-email", response_model=AuthResponse)
async def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email using one-time code and return login token."""
    user = db.query(User).filter(func.lower(User.email) == payload.email.strip().lower()).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.email_verified:
        # Already verified: issue token directly
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "username": user.username, "is_admin": user.is_admin}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }

    if not user.email_verification_code or user.email_verification_code != payload.code.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    if not user.email_verification_expires_at or user.email_verification_expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code has expired")

    user.email_verified = True
    user.email_verification_code = None
    user.email_verification_expires_at = None
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username, "is_admin": user.is_admin}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@app.post("/api/v1/auth/resend-verification", response_model=RegisterResponse)
async def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend verification code for unverified accounts."""
    user = db.query(User).filter(func.lower(User.email) == payload.email.strip().lower()).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.email_verified:
        return {
            "message": "Email already verified.",
            "requires_verification": False,
            "email": user.email,
            "dev_verification_code": None
        }

    verification_code = generate_verification_code()
    user.email_verification_code = verification_code
    user.email_verification_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    # Send verification email if SMTP is configured
    email_sent = await send_verification_email(user.email, verification_code)

    return {
        "message": "Verification code sent to your email." if email_sent else "Verification code resent.",
        "requires_verification": True,
        "email": user.email,
        "dev_verification_code": None if email_sent else verification_code
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

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before logging in."
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
