from typing import Dict, List, Tuple
from enum import Enum


class Phenotype(str, Enum):
    PM = "PM"  # Poor Metabolizer
    IM = "IM"  # Intermediate Metabolizer
    NM = "NM"  # Normal Metabolizer
    RM = "RM"  # Rapid Metabolizer
    URM = "URM"  # Ultra-Rapid Metabolizer
    POOR_METABOLIZER = "Poor Metabolizer"
    INTERMEDIATE_METABOLIZER = "Intermediate Metabolizer"
    NORMAL_METABOLIZER = "Normal Metabolizer"
    NORMAL_FUNCTION = "Normal function"
    DECREASED_FUNCTION = "Decreased function"
    LOW_FUNCTION = "Low function"
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
                "Low function": ("Toxic", "high", 0.88),
                "Decreased function": ("Adjust Dosage", "moderate", 0.85),
                "Normal function": ("Safe", "none", 0.95),
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
                "Poor Metabolizer": ("Toxic", "critical", 0.99),
                "Intermediate Metabolizer": ("Adjust Dosage", "high", 0.92),
                "Normal Metabolizer": ("Safe", "none", 0.98),
            }
        }
    }

    CYP2C9_ALLELE_ACTIVITY = {
        "*1": 1.0,
        "*2": 0.5,
        "*3": 0.0,
        "*5": 0.0,
        "*6": 0.0,
        "*8": 0.5,
        "*11": 0.5,
        "*12": 0.0,
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

        normalized_alleles = []
        for allele in star_alleles:
            if allele is None:
                continue
            allele_text = str(allele).strip()
            if not allele_text:
                continue
            if "/" in allele_text:
                for part in allele_text.split("/"):
                    part = part.strip()
                    if part:
                        normalized_alleles.append(part)
            else:
                normalized_alleles.append(allele_text)

        if not normalized_alleles:
            return "Unknown", 0.3
        
        # Convert star alleles to phenotype
        # This is a simplified mapping
        if len(normalized_alleles) >= 2:
            sorted_alleles = sorted(normalized_alleles)
            star_str = f"{sorted_alleles[0]}/{sorted_alleles[1]}"
        else:
            star_str = f"{normalized_alleles[0]}/{normalized_alleles[0]}"
        
        phenotype_scores = {
            "*1/*1": ("NM", 0.98),
            "*1/*2": ("IM", 0.90),
            "*1/*3": ("IM", 0.88),
            "*2/*2": ("PM", 0.92),
            "*2/*3": ("PM", 0.88),
            "*3/*3": ("PM", 0.88),
            "*3/*4": ("PM", 0.86),
            "*4/*4": ("PM", 0.90),
            "*1/*41": ("IM", 0.90),
            "*2/*41": ("IM", 0.88),
            "*41/*41": ("IM", 0.90),
            "*4/*41": ("PM", 0.88),
            "*1/*5": ("IM", 0.92),
            "*5/*5": ("PM", 0.95),
            "*1/*15": ("IM", 0.90),
            "*5/*15": ("PM", 0.93),
            "*15/*15": ("PM", 0.94),
            "*1/*2A": ("IM", 0.94),
            "*2A/*2A": ("PM", 0.97),
            "*1/*13": ("IM", 0.92),
            "*13/*13": ("PM", 0.96),
            "*2A/*13": ("PM", 0.97),
            "*1/*2": ("IM", 0.92),
            "*2/*2": ("PM", 0.95),
            "*1/*3A": ("IM", 0.93),
            "*3A/*3A": ("PM", 0.97),
            "*1/*3B": ("IM", 0.90),
            "*3B/*3B": ("PM", 0.95),
            "*1/*3C": ("IM", 0.93),
            "*3C/*3C": ("PM", 0.97),
            "*3A/*3C": ("PM", 0.96),
            "*1/*1_*1/*1": ("URM", 0.85),  # Gene duplication
        }
        
        return phenotype_scores.get(star_str, ("Unknown", 0.5))

    def infer_cyp2c9_phenotype(self, diplotype: str) -> Tuple[str, float]:
        """Infer CYP2C9 phenotype from diplotype using activity score model."""
        if not diplotype or "/" not in diplotype:
            return "Unknown", 0.3

        left_allele, right_allele = [part.strip() for part in diplotype.split("/", 1)]
        left_score = self.CYP2C9_ALLELE_ACTIVITY.get(left_allele)
        right_score = self.CYP2C9_ALLELE_ACTIVITY.get(right_allele)

        if left_score is None or right_score is None:
            return "Unknown", 0.5

        activity_score = left_score + right_score

        if activity_score >= 1.5:
            return "NM", 0.95
        if activity_score in (1.0, 0.5):
            return "IM", 0.93
        if activity_score == 0.0:
            return "PM", 0.97

        return "Unknown", 0.5

    def infer_slco1b1_phenotype(self, diplotype: str) -> Tuple[str, float]:
        """Infer SLCO1B1 transporter function phenotype from diplotype."""
        if not diplotype or "/" not in diplotype:
            return "Unknown", 0.3

        left_allele, right_allele = [part.strip() for part in diplotype.split("/", 1)]
        normalized = "/".join(sorted([left_allele, right_allele]))

        phenotype_map = {
            "*1/*1": ("Normal function", 0.96),
            "*1/*5": ("Decreased function", 0.95),
            "*5/*5": ("Low function", 0.97),
            "*1/*15": ("Decreased function", 0.93),
            "*5/*15": ("Low function", 0.94),
            "*15/*15": ("Low function", 0.95),
        }

        return phenotype_map.get(normalized, ("Unknown", 0.5))

    def infer_dpyd_phenotype(self, diplotype: str) -> Tuple[str, float]:
        """Infer DPYD phenotype using CPIC-aligned no/decreased function rules."""
        if not diplotype or "/" not in diplotype:
            return "Unknown", 0.3

        left_allele, right_allele = [part.strip() for part in diplotype.split("/", 1)]
        no_function = {"*2A", "*13", "D949V"}
        decreased_function = {"HapB3"}

        function_score = 0
        for allele in (left_allele, right_allele):
            if allele == "*1":
                function_score += 2
            elif allele in decreased_function:
                function_score += 1
            elif allele in no_function:
                function_score += 0
            else:
                return "Unknown", 0.5

        if function_score == 4:
            return "Normal Metabolizer", 0.97
        if function_score in (3, 2, 1):
            return "Intermediate Metabolizer", 0.94
        if function_score == 0:
            return "Poor Metabolizer", 0.99
        return "Unknown", 0.5
    
    def get_clinical_recommendation(
        self,
        risk_label: str,
        drug: str,
        phenotype: str,
        gene: str = ""
    ) -> str:
        """
        Generate clinical recommendation based on risk assessment
        """
        
        if gene == "CYP2C9" and drug == "WARFARIN" and phenotype == "PM":
            return "Substantially reduce dose (80–90%) and use genotype-guided dosing with close INR monitoring"

        if gene == "CYP2C19" and drug == "CLOPIDOGREL" and phenotype == "PM":
            return "Avoid clopidogrel and use an alternative P2Y12 inhibitor (prasugrel or ticagrelor) unless contraindicated"

        if gene == "SLCO1B1" and drug == "SIMVASTATIN" and phenotype == "Low function":
            return "Avoid simvastatin or limit to a maximum of 20 mg/day; consider alternative statins such as pravastatin or rosuvastatin with close monitoring for myopathy"

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
