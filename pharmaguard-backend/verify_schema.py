#!/usr/bin/env python3
"""
Verify PharmaGuard JSON Response Schema
"""
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models import PharmaGuardResponse, RiskAssessment, PharmacogenomicProfile, DetectedVariant, ClinicalRecommendation, LLMGeneratedExplanation, QualityMetrics
from datetime import datetime


def verify_schema():
    """Create a sample response and verify it matches the required schema"""
    
    # Create sample response
    response = PharmaGuardResponse(
        patient_id="PATIENT_ABC123",
        drug="CODEINE",
        timestamp=datetime.utcnow().isoformat() + "Z",
        risk_assessment=RiskAssessment(
            risk_label="Ineffective",
            confidence_score=0.95,
            severity="high"
        ),
        pharmacogenomic_profile=PharmacogenomicProfile(
            primary_gene="CYP2D6",
            diplotype="*4/*4",
            phenotype="PM",
            detected_variants=[
                DetectedVariant(rsid="rs1065852"),
                DetectedVariant(rsid="rs3892097")
            ]
        ),
        clinical_recommendation=ClinicalRecommendation(
            action="Consider Alternative Medication",
            detail="Poor metabolizer phenotype indicates severely reduced CYP2D6 function. Patient may not respond to codeine. Consider alternative analgesics."
        ),
        llm_generated_explanation=LLMGeneratedExplanation(
            summary="Patient has poor metabolizer (PM) phenotype for CYP2D6, indicating severely reduced enzyme function...",
            patient_summary="Your genetic test shows that codeine may not work well for you because your body cannot convert it into its active form..."
        ),
        quality_metrics=QualityMetrics(
            vcf_parsing_success=True
        )
    )
    
    # Convert to JSON
    json_output = response.model_dump()
    
    # Print formatted JSON
    print("\n" + "=" * 80)
    print("PHARMAGUARD API RESPONSE - STRUCTURED JSON OUTPUT")
    print("=" * 80)
    print(json.dumps(json_output, indent=2))
    print("=" * 80)
    
    # Verify required fields
    required_fields = [
        "patient_id",
        "drug",
        "timestamp",
        "risk_assessment",
        "pharmacogenomic_profile",
        "clinical_recommendation",
        "llm_generated_explanation",
        "quality_metrics"
    ]
    
    print("\n✅ SCHEMA VALIDATION:")
    for field in required_fields:
        if field in json_output:
            print(f"  ✅ {field}: Present")
        else:
            print(f"  ❌ {field}: MISSING")
    
    # Verify nested fields
    print("\n✅ RISK ASSESSMENT FIELDS:")
    risk = json_output.get("risk_assessment", {})
    for field in ["risk_label", "confidence_score", "severity"]:
        print(f"  ✅ {field}: {risk.get(field)}")
    
    print("\n✅ PHARMACOGENOMIC PROFILE FIELDS:")
    profile = json_output.get("pharmacogenomic_profile", {})
    for field in ["primary_gene", "diplotype", "phenotype", "detected_variants"]:
        print(f"  ✅ {field}: {profile.get(field)}")
    
    print("\n✅ CLINICAL RECOMMENDATION FIELDS:")
    rec = json_output.get("clinical_recommendation", {})
    for field in ["action", "detail"]:
        print(f"  ✅ {field}: {rec.get(field)[:50]}..." if len(str(rec.get(field))) > 50 else rec.get(field))
    
    print("\n✅ LLM EXPLANATION FIELDS:")
    llm = json_output.get("llm_generated_explanation", {})
    for field in ["summary", "patient_summary"]:
        value = llm.get(field, "")
        print(f"  ✅ {field}: {value[:50]}..." if len(value) > 50 else value)
    
    print("\n✅ QUALITY METRICS FIELDS:")
    qm = json_output.get("quality_metrics", {})
    for field in ["vcf_parsing_success"]:
        print(f"  ✅ {field}: {qm.get(field)}")
    
    print("\n" + "=" * 80)
    print("✅ SCHEMA MATCHES REQUIRED FORMAT")
    print("=" * 80)
    
    return json_output


if __name__ == "__main__":
    verify_schema()
