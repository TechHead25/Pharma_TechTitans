from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DetectedVariant(BaseModel):
    rsid: str


class PharmacogenomicProfile(BaseModel):
    primary_gene: str
    diplotype: str
    phenotype: str = Field(pattern="^(PM|IM|NM|RM|URM|Unknown)$")
    detected_variants: List[DetectedVariant]


class RiskAssessment(BaseModel):
    risk_label: str = Field(
        pattern="^(Safe|Adjust Dosage|Toxic|Ineffective|Unknown)$"
    )
    confidence_score: float = Field(ge=0.0, le=1.0)
    severity: str = Field(pattern="^(none|low|moderate|high|critical)$")


class LLMGeneratedExplanation(BaseModel):
    clinical_summary: str = Field(description="Technical explanation for healthcare professionals")
    patient_summary: str = Field(description="Jargon-free explanation for patients")


class QualityMetrics(BaseModel):
    vcf_parsing_success: bool


class PharmaGuardResponse(BaseModel):
    patient_id: str
    drug: str
    timestamp: str  # ISO8601
    risk_assessment: RiskAssessment
    pharmacogenomic_profile: PharmacogenomicProfile
    clinical_recommendation: str
    llm_generated_explanation: LLMGeneratedExplanation
    quality_metrics: QualityMetrics


class VCFUpload(BaseModel):
    file_name: str
    file_size: int
