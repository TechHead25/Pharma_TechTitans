from typing import Dict, List, Tuple
from enum import Enum


class Phenotype(str, Enum):
    PM = "PM"  # Poor Metabolizer
    IM = "IM"  # Intermediate Metabolizer
    NM = "NM"  # Normal Metabolizer
    RM = "RM"  # Rapid Metabolizer
    URM = "URM"  # Ultra-Rapid Metabolizer
    UNKNOWN = "Unknown"


class RiskLabel(str, Enum):
    SAFE = "Safe"
    ADJUST_DOSAGE = "Adjust Dosage"
    TOXIC = "Toxic"
    INEFFECTIVE = "Ineffective"
    UNKNOWN = "Unknown"


class Severity(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAssessmentEngine:
    """
    CPIC-aligned pharmacogenomic risk assessment engine
    Maps genotypes to phenotypes and clinical recommendations
    """
    
    # CPIC guidelines mapping: gene -> drug -> phenotype -> (risk_label, severity, confidence)
    CPIC_RISK_MAP = {
        "CYP2D6": {
            "CODEINE": {
                "PM": ("Ineffective", "high", 0.95),
                "IM": ("Adjust Dosage", "moderate", 0.85),
                "NM": ("Safe", "none", 0.98),
                "RM": ("Safe", "low", 0.90),
                "URM": ("Toxic", "critical", 0.92),
            }
        },
        "CYP2C19": {
            "WARFARIN": {
                "PM": ("Adjust Dosage", "high", 0.88),
                "IM": ("Adjust Dosage", "moderate", 0.85),
                "NM": ("Safe", "none", 0.95),
                "RM": ("Safe", "low", 0.90),
                "URM": ("Safe", "none", 0.92),
            },
            "CLOPIDOGREL": {
                "PM": ("Ineffective", "critical", 0.95),
                "IM": ("Adjust Dosage", "high", 0.88),
                "NM": ("Safe", "none", 0.96),
                "RM": ("Safe", "none", 0.93),
                "URM": ("Safe", "none", 0.91),
            }
        },
        "CYP2C9": {
            "WARFARIN": {
                "PM": ("Toxic", "critical", 0.90),
                "IM": ("Adjust Dosage", "high", 0.87),
                "NM": ("Safe", "none", 0.96),
                "RM": ("Safe", "none", 0.92),
                "URM": ("Safe", "none", 0.90),
            }
        },
        "SLCO1B1": {
            "SIMVASTATIN": {
                "PM": ("Toxic", "high", 0.88),
                "IM": ("Adjust Dosage", "moderate", 0.85),
                "NM": ("Safe", "none", 0.95),
                "RM": ("Safe", "none", 0.91),
                "URM": ("Safe", "none", 0.90),
            }
        },
        "TPMT": {
            "AZATHIOPRINE": {
                "PM": ("Toxic", "critical", 0.96),
                "IM": ("Adjust Dosage", "high", 0.90),
                "NM": ("Safe", "none", 0.97),
                "RM": ("Safe", "none", 0.93),
                "URM": ("Safe", "none", 0.92),
            }
        },
        "DPYD": {
            "FLUOROURACIL": {
                "PM": ("Toxic", "critical", 0.98),
                "IM": ("Adjust Dosage", "high", 0.92),
                "NM": ("Safe", "none", 0.98),
                "RM": ("Safe", "none", 0.94),
                "URM": ("Safe", "none", 0.93),
            }
        }
    }
    
    def __init__(self):
        self.valid_phenotypes = [p.value for p in Phenotype]
        self.valid_risk_labels = [r.value for r in RiskLabel]
        self.valid_severities = [s.value for s in Severity]
    
    def assess_risk(
        self,
        gene: str,
        drug: str,
        phenotype: str,
        detected_variants: List[str],
        diplotype: str = "*1/*1"
    ) -> Dict:
        """
        Assess pharmacogenomic risk
        
        Args:
            gene: Gene symbol (e.g., "CYP2D6")
            drug: Drug name
            phenotype: Metabolizer phenotype
            detected_variants: List of variant IDs
            diplotype: Star allele diplotype
            
        Returns:
            Dictionary with risk assessment details
        """
        
        # Validate inputs
        if phenotype not in self.valid_phenotypes:
            phenotype = "Unknown"
        
        # Get risk from CPIC map
        risk_data = self.CPIC_RISK_MAP.get(gene, {}).get(drug, {}).get(phenotype)
        
        if risk_data is None:
            risk_label = "Unknown"
            severity = "moderate"
            confidence = 0.5
        else:
            risk_label, severity, confidence = risk_data
        
        # Map to severity score
        severity_score = {
            "none": 0,
            "low": 1,
            "moderate": 2,
            "high": 3,
            "critical": 4
        }.get(severity, 2)
        
        return {
            "risk_label": risk_label,
            "severity": severity,
            "confidence_score": confidence,
            "severity_score": severity_score,
            "gene": gene,
            "drug": drug,
            "phenotype": phenotype,
            "detected_variants_count": len(detected_variants),
        }
    
    def infer_phenotype(self, star_alleles: List[str]) -> Tuple[str, float]:
        """
        Infer phenotype from star alleles
        
        Simplified mapping - in production would use more sophisticated logic
        
        Returns:
            Tuple of (phenotype, confidence_score)
        """
        if not star_alleles:
            return "Unknown", 0.3
        
        # Convert star alleles to phenotype
        # This is a simplified mapping
        if len(star_alleles) >= 2:
            sorted_alleles = sorted(star_alleles)
            star_str = f"{sorted_alleles[0]}/{sorted_alleles[1]}"
        else:
            star_str = f"{star_alleles[0]}/{star_alleles[0]}"
        
        phenotype_scores = {
            "*1/*1": ("NM", 0.98),
            "*1/*2": ("IM", 0.90),
            "*1/*3": ("IM", 0.88),
            "*2/*2": ("PM", 0.92),
            "*2/*3": ("PM", 0.88),
            "*3/*3": ("PM", 0.88),
            "*3/*4": ("PM", 0.86),
            "*4/*4": ("PM", 0.90),
            "*1/*1_*1/*1": ("URM", 0.85),  # Gene duplication
        }
        
        return phenotype_scores.get(star_str, ("Unknown", 0.5))
    
    def get_clinical_recommendation(
        self,
        risk_label: str,
        drug: str,
        phenotype: str
    ) -> str:
        """
        Generate clinical recommendation based on risk assessment
        """
        
        recommendations = {
            "Safe": f"Patient can take standard dosage of {drug}. No pharmacogenomic adjustment needed.",
            "Adjust Dosage": f"Recommend dose adjustment for {drug} based on {phenotype} phenotype. Consult clinical guidelines.",
            "Toxic": f"CAUTION: Patient is at high risk of toxicity with {drug}. Consider alternative therapy or significantly reduce dose.",
            "Ineffective": f"Patient may have reduced response to {drug}. Consider higher dose or alternative medication.",
            "Unknown": f"Insufficient pharmacogenomic data for {drug}. Baseline dosing recommended with monitoring.",
        }
        
        return recommendations.get(risk_label, f"Review {drug} dosing with clinical team.")


def assess_patient_risk(
    gene: str,
    drug: str,
    phenotype: str,
    detected_variants: List[str],
    diplotype: str = "*1/*1"
) -> Dict:
    """
    Convenience function for risk assessment
    """
    engine = RiskAssessmentEngine()
    return engine.assess_risk(gene, drug, phenotype, detected_variants, diplotype)
