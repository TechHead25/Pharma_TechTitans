import os
from typing import Dict, Optional, Tuple
import google.generativeai as genai


class LLMExplainer:
    """Generate dual-layer clinical explanations using LLM (Google Gemini)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
    
    def generate_explanations(
        self,
        gene: str,
        drug: str,
        phenotype: str,
        risk_label: str,
        detected_variants: list,
        diplotype: str,
        current_dose_mg: Optional[float] = None
    ) -> Tuple[str, str]:
        """
        Generate dual-layer explanations for pharmacogenomic findings
        
        Returns:
            Tuple of (clinical_summary, patient_summary)
        """
        
        if not self.model:
            clinical, patient = self._fallback_explanations(
                gene, drug, phenotype, risk_label, detected_variants, diplotype, current_dose_mg
            )
            return clinical, patient
        
        try:
            clinical = self._generate_clinical_summary(
                gene, drug, phenotype, risk_label, detected_variants, diplotype, current_dose_mg
            )
            
            patient = self._generate_patient_summary(
                gene, drug, phenotype, risk_label, detected_variants, diplotype
            )
            
            return clinical, patient
        except Exception as e:
            print(f"LLM error: {e}")
            clinical, patient = self._fallback_explanations(
                gene, drug, phenotype, risk_label, detected_variants, diplotype, current_dose_mg
            )
            return clinical, patient
    
    def _generate_clinical_summary(
        self,
        gene: str,
        drug: str,
        phenotype: str,
        risk_label: str,
        detected_variants: list,
        diplotype: str,
        current_dose_mg: Optional[float] = None
    ) -> str:
        """Generate technical clinical summary for healthcare professionals"""
        
        normalized_variants = [f"rs{v}" if not str(v).startswith("rs") else str(v) for v in detected_variants]
        variants_str = ", ".join(normalized_variants) if normalized_variants else "none detected"
        star_allele = diplotype.split("/")[0] if "/" in diplotype else diplotype
        
        system_instruction = "You are a board-certified clinical pharmacologist and pharmacogenomics specialist writing for physicians and clinical pharmacists. Use advanced medical terminology, CPIC-oriented reasoning, and mechanistic pharmacology language."
        
        prompt = f"""{system_instruction}

Generate a high-detail technical explanation (320-420 words) for healthcare professionals about the following pharmacogenomic finding:

Gene: {gene}
Drug: {drug}
Phenotype: {phenotype}
Diplotype: {diplotype}
Risk Assessment: {risk_label}
Detected Variants: {variants_str}
Current Dose: {f'{current_dose_mg} mg' if current_dose_mg is not None else 'Not provided'}

Required structure (use clear paragraphing and clinician-facing language):
1. Pharmacokinetic/pharmacodynamic mechanism: enzyme/transporter activity, prodrug activation or inactivation pathway, and expected exposure changes (AUC/Cmax/clearance directionality when relevant).
2. Genotype-to-phenotype interpretation: explain how STAR allele {star_allele} and diplotype {diplotype} produce phenotype {phenotype}, including functional status (normal, decreased, no function, increased function).
3. Variant-level interpretation: explicitly discuss RSIDs from [{variants_str}] and their functional consequence (loss-of-function, reduced-function, splice/frameshift/missense effect, where applicable).
4. CPIC-aligned management: recommend therapy adjustment, alternative agents, and monitoring strategy (e.g., INR, platelet reactivity, CBC, LFTs, CK, toxicity surveillance) based on risk level {risk_label}.
5. Safety and outcome implications: short-term and long-term adverse event risk if genotype-guided therapy is not applied.
6. Clinical actionability statement: concise recommendation suitable for chart documentation.
7. Dose decision statement: explicitly state whether the CURRENT DOSE should be maintained, reduced, increased, or avoided, and why.

MANDATORY citation rule: You MUST explicitly include at least one RSID from [{variants_str}] and explicitly include the STAR allele {star_allele} verbatim in the response text.
Tone requirement: Use professional medical terminology (e.g., biotransformation, bioactivation, therapeutic index, myelosuppression, hemorrhagic risk, platelet inhibition, genotype-guided dosing). Avoid lay simplifications."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=520,
                    temperature=0.45,
                )
            )
            summary = response.text.strip()
            return self._ensure_variant_citation(summary, normalized_variants, star_allele)
        except Exception as e:
            print(f"Clinical summary generation error: {e}")
            raise
    
    def _generate_patient_summary(
        self,
        gene: str,
        drug: str,
        phenotype: str,
        risk_label: str,
        detected_variants: list,
        diplotype: str
    ) -> str:
        """Generate simple, jargon-free summary for patients"""
        
        normalized_variants = [f"rs{v}" if not str(v).startswith("rs") else str(v) for v in detected_variants]
        variants_str = ", ".join(normalized_variants) if normalized_variants else "none detected"
        star_allele = diplotype.split("/")[0] if "/" in diplotype else diplotype

        system_instruction = "You are a patient educator. Explain complex medical concepts in simple, friendly language using analogies. Make patients feel empowered, not scared."

        prompt = f"""{system_instruction}

Generate a simple, friendly explanation (150-200 words) about their pharmacogenomic result:

Gene: {gene}
Drug: {drug}
Phenotype: {phenotype}
Risk Level: {risk_label}
Detected RSIDs: {variants_str}
Star Allele: {star_allele}

Use simple analogies and everyday language. Explain:
1. What this gene does (simple analogy for the enzyme role)
2. How their body type ({phenotype}) affects {drug} processing
3. What the risk means in simple terms
4. What they might expect or what their doctor might recommend
5. A reassuring statement about modern medicine

Avoid: Medical jargon, technical terms, overly complex sentences
Use: Analogies, simple explanations, empathetic tone

MANDATORY citation rule: Include at least one RSID (for example {normalized_variants[0] if normalized_variants else 'N/A'}) and include the STAR allele {star_allele} explicitly in plain language."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=250,
                    temperature=0.7,
                )
            )
            summary = response.text.strip()
            return self._ensure_variant_citation(summary, normalized_variants, star_allele)
        except Exception as e:
            print(f"Patient summary generation error: {e}")
            raise

    def _ensure_variant_citation(self, summary: str, rsids: list, star_allele: str) -> str:
        """Guarantee explicit RSID and STAR allele citation in generated summary."""
        first_rsid = rsids[0] if rsids else "rsN/A"
        citation_snippet = f"Variant citation: RSID {first_rsid}; STAR allele {star_allele}."

        has_rsid = any(rsid in summary for rsid in rsids) if rsids else False
        has_star = star_allele in summary

        if has_rsid and has_star:
            return summary

        if summary.endswith("\n"):
            return f"{summary}{citation_snippet}"
        return f"{summary}\n\n{citation_snippet}"
    
    def _fallback_explanations(
        self,
        gene: str,
        drug: str,
        phenotype: str,
        risk_label: str,
        detected_variants: list,
        diplotype: str,
        current_dose_mg: Optional[float] = None
    ) -> Tuple[str, str]:
        """Generate explanations without LLM (fallback)"""
        
        normalized_variants = [f"rs{v}" if not str(v).startswith("rs") else str(v) for v in detected_variants]
        star_allele = diplotype.split("/")[0] if "/" in diplotype else diplotype

        # Clinical summaries
        clinical_map = {
            ("CYP2D6", "CODEINE", "PM"): (
                f"Patient carries {diplotype} genotype resulting in poor metabolizer (PM) phenotype for {gene}. CYP2D6 encodes the enzyme responsible for O-demethylation of codeine to morphine. PM individuals (frequency ~7%) have absent or severely reduced enzyme activity. Detected variants {', '.join(normalized_variants)} are loss-of-function alleles. CPIC recommends avoiding codeine due to reduced efficacy and unpredictable opioid response. Consider alternative opioids dependent on different metabolic pathways.",
                
                f"Your body has difficulty converting {drug} into its active form. This means the medicine may not work as intended. Your doctor will likely suggest a different pain reliever that your body can process more easily. This is actually a helpful discovery that prevents unnecessary suffering!"
            ),
            
            ("CYP2C19", "CLOPIDOGREL", "PM"): (
                f"{gene} poor metabolizer phenotype (from {diplotype} genotype) impairs conversion of clopidogrel (a prodrug) to its active metabolite. Variants {', '.join(normalized_variants)} reduce enzyme function. CPIC evidence level A: PM phenotype is associated with significantly reduced platelet inhibition and increased risk of stent thrombosis and acute coronary events. Recommend alternative P2Y12 inhibitors (prasugrel, ticagrelor) with independent activation pathways.",
                
                f"Your genes make it harder for your body to activate {drug}. This medicine needs to be converted to work properly, and your body struggles with that step. The good news? There are other equally effective medicines your body can process perfectly. Your doctor will switch you to one of those instead."
            ),
            
            ("CYP2C9", "WARFARIN", "IM"): (
                f"Intermediate metabolizer phenotype for {gene} (from {diplotype}) predicts higher warfarin levels and increased bleeding risk. Variants {', '.join(normalized_variants)} reduce CYP2C9 activity. CPIC recommends loading dose reduction (suggest 5mg instead of 10mg). Requires more frequent INR monitoring (weekly for first 2-4 weeks). Consider pharmacogenetic-guided dosing algorithm.",
                
                f"Your body processes {drug} more slowly than average. This means the medicine can build up in your system more easily. Your doctor will start you on a lower dose and check your blood more often to keep you safe. Think of it like a slower drain in your bathtub—we just adjust the water flow accordingly!"
            ),
            
            ("TPMT", "AZATHIOPRINE", "PM"): (
                f"TPMT poor metabolizer genotype ({diplotype}) with variants {', '.join(normalized_variants)} confers severe thiopurine methyltransferase deficiency. CPIC recommends AVOIDING azathioprine due to critical risk of life-threatening bone marrow toxicity from 6-thioguanine nucleotide accumulation. Risk of severe myelosuppression, infections, and malignancy. Alternative immunosuppressants needed.",
                
                f"Your body cannot safely process {drug}. The medicine could build up to dangerous levels in your system, potentially harming your bone marrow. This is serious—do not take this medicine. Your doctor will prescribe a different immunosuppressant that's safe for you."
            ),
            
            ("DPYD", "FLUOROURACIL", "PM"): (
                f"DPYD deficiency from {diplotype} genotype (variants: {', '.join(normalized_variants)}) causes profound impairment of dihydropyrimidine dehydrogenase. CPIC strongly recommends CONTRAINDICATION to fluorouracil-based chemotherapy due to unacceptable risk of severe, life-threatening toxicity (grade 3-5 diarrhea, neutropenia, thrombocytopenia). Patient requires alternative cancer therapy.",
                
                f"{drug} is CONTRAINDICATED for you. This is a cancer medicine your body cannot safely handle—it would cause severe side effects. Do not take this without discussing alternatives with your oncology team. Safe alternatives exist for your specific cancer."
            ),
        }
        
        # Try to find a matching explanation
        key = (gene, drug, phenotype)
        if key in clinical_map:
            return clinical_map[key]
        
        # Generic fallback
        variants_str = ", ".join(normalized_variants) if normalized_variants else "multiple variants"
        
        dose_text = ""
        if current_dose_mg is not None:
            if risk_label in ["Adjust Dosage", "Toxic"]:
                dose_text = f" Current dose is {current_dose_mg} mg; dose reduction or therapeutic substitution is advised."
            elif risk_label == "Safe":
                dose_text = f" Current dose is {current_dose_mg} mg; this may be maintained with routine clinical monitoring."
            else:
                dose_text = f" Current dose is {current_dose_mg} mg; dose should be titrated cautiously due to uncertain genotype-drug effect."

        phenotype_label = "functional status" if gene == "SLCO1B1" else "metabolizer status"

        clinical_fb = (
            f"Pharmacogenomic interpretation: {gene} diplotype {diplotype} (STAR allele {star_allele}) is consistent with "
            f"{phenotype} {phenotype_label}. Variant evidence includes {variants_str}, supporting altered enzyme/transporter "
            f"function with expected modification in {drug} disposition and/or bioactivation. Clinical risk category is {risk_label}. "
            f"From a CPIC-aligned perspective, implement genotype-guided prescribing with attention to exposure-response dynamics, "
            f"narrow therapeutic index considerations, and phenotype-concordant dose selection or alternative therapy when indicated. "
            f"Recommend structured monitoring tailored to drug class (e.g., coagulation indices, hematologic toxicity surveillance, "
            f"drug response endpoints, and adverse event monitoring) and document pharmacogenomic rationale in the treatment plan."
            f"{dose_text}"
        )
        
        patient_fb = f"Your genetic test shows your body processes {drug} differently. Your result ({phenotype} type) means: {risk_label.lower()}. Talk to your doctor about what this means for your treatment. Modern medicine has solutions for every genetic type!"
        
        clinical_fb = self._ensure_variant_citation(clinical_fb, normalized_variants, star_allele)
        patient_fb = self._ensure_variant_citation(patient_fb, normalized_variants, star_allele)
        return clinical_fb, patient_fb


def generate_dual_explanations(
    gene: str,
    drug: str,
    phenotype: str,
    risk_label: str,
    detected_variants: list,
    diplotype: str,
    current_dose_mg: Optional[float] = None,
    api_key: Optional[str] = None
) -> Tuple[str, str]:
    """
    Convenience function to generate dual-layer explanations
    
    Returns:
        Tuple of (clinical_summary, patient_summary)
    """
    explainer = LLMExplainer(api_key=api_key)
    return explainer.generate_explanations(
        gene, drug, phenotype, risk_label, detected_variants, diplotype, current_dose_mg
    )
