import os
from typing import Dict, Optional, Tuple
from openai import OpenAI


class LLMExplainer:
    """Generate dual-layer clinical explanations using LLM (OpenAI GPT)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def generate_explanations(
        self,
        gene: str,
        drug: str,
        phenotype: str,
        risk_label: str,
        detected_variants: list,
        diplotype: str
    ) -> Tuple[str, str]:
        """
        Generate dual-layer explanations for pharmacogenomic findings
        
        Returns:
            Tuple of (clinical_summary, patient_summary)
        """
        
        if not self.client:
            clinical, patient = self._fallback_explanations(
                gene, drug, phenotype, risk_label, detected_variants, diplotype
            )
            return clinical, patient
        
        try:
            clinical = self._generate_clinical_summary(
                gene, drug, phenotype, risk_label, detected_variants, diplotype
            )
            
            patient = self._generate_patient_summary(
                gene, drug, phenotype, risk_label, detected_variants, diplotype
            )
            
            return clinical, patient
        except Exception as e:
            print(f"LLM error: {e}")
            clinical, patient = self._fallback_explanations(
                gene, drug, phenotype, risk_label, detected_variants, diplotype
            )
            return clinical, patient
    
    def _generate_clinical_summary(
        self,
        gene: str,
        drug: str,
        phenotype: str,
        risk_label: str,
        detected_variants: list,
        diplotype: str
    ) -> str:
        """Generate technical clinical summary for healthcare professionals"""
        
        variants_str = ", ".join([f"rs{v}" if not v.startswith("rs") else v for v in detected_variants])
        
        prompt = f"""You are a clinical pharmacogenomics expert. Generate a concise technical explanation (200-250 words) for healthcare professionals about the following pharmacogenomic finding:

Gene: {gene}
Drug: {drug}
Phenotype: {phenotype}
Diplotype: {diplotype}
Risk Assessment: {risk_label}
Detected Variants: {variants_str}

Include:
1. Specific mechanism of how {gene} affects {drug} metabolism
2. Citation of detected variant RSIDs and their known effects
3. How {diplotype} genotype results in {phenotype} phenotype
4. CPIC guideline recommendation
5. Specific dosage or monitoring adjustments needed
6. Clinical significance and outcomes if not considered"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a clinical pharmacogenomics expert. Provide precise, citation-accurate explanations suitable for medical professionals. Use technical terminology."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=350,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
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
        
        prompt = f"""You are a patient educator writing for someone with no medical background. Generate a simple, friendly explanation (150-200 words) about their pharmacogenomic result:

Gene: {gene}
Drug: {drug}
Phenotype: {phenotype}
Risk Level: {risk_label}

Use simple analogies and everyday language. Explain:
1. What this gene does (simple analogy for the enzyme role)
2. How their body type ({phenotype}) affects {drug} processing
3. What the risk means in simple terms
4. What they might expect or what their doctor might recommend
5. A reassuring statement about modern medicine

Avoid: Medical jargon, technical terms, overly complex sentences
Use: Analogies, simple explanations, empathetic tone"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a patient educator. Explain complex medical concepts in simple, friendly language using analogies. Make patients feel empowered, not scared."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Patient summary generation error: {e}")
            raise
    
    def _fallback_explanations(
        self,
        gene: str,
        drug: str,
        phenotype: str,
        risk_label: str,
        detected_variants: list,
        diplotype: str
    ) -> Tuple[str, str]:
        """Generate explanations without LLM (fallback)"""
        
        # Clinical summaries
        clinical_map = {
            ("CYP2D6", "CODEINE", "PM"): (
                f"Patient carries {diplotype} genotype resulting in poor metabolizer (PM) phenotype for {gene}. CYP2D6 encodes the enzyme responsible for O-demethylation of codeine to morphine. PM individuals (frequency ~7%) have absent or severely reduced enzyme activity. Detected variants {', '.join(detected_variants)} are loss-of-function alleles. CPIC recommends avoiding codeine due to reduced efficacy and unpredictable opioid response. Consider alternative opioids dependent on different metabolic pathways.",
                
                f"Your body has difficulty converting {drug} into its active form. This means the medicine may not work as intended. Your doctor will likely suggest a different pain reliever that your body can process more easily. This is actually a helpful discovery that prevents unnecessary suffering!"
            ),
            
            ("CYP2C19", "CLOPIDOGREL", "PM"): (
                f"{gene} poor metabolizer phenotype (from {diplotype} genotype) impairs conversion of clopidogrel (a prodrug) to its active metabolite. Variants {', '.join(detected_variants)} reduce enzyme function. CPIC evidence level A: PM phenotype is associated with significantly reduced platelet inhibition and increased risk of stent thrombosis and acute coronary events. Recommend alternative P2Y12 inhibitors (prasugrel, ticagrelor) with independent activation pathways.",
                
                f"Your genes make it harder for your body to activate {drug}. This medicine needs to be converted to work properly, and your body struggles with that step. The good news? There are other equally effective medicines your body can process perfectly. Your doctor will switch you to one of those instead."
            ),
            
            ("CYP2C9", "WARFARIN", "IM"): (
                f"Intermediate metabolizer phenotype for {gene} (from {diplotype}) predicts higher warfarin levels and increased bleeding risk. Variants {', '.join(detected_variants)} reduce CYP2C9 activity. CPIC recommends loading dose reduction (suggest 5mg instead of 10mg). Requires more frequent INR monitoring (weekly for first 2-4 weeks). Consider pharmacogenetic-guided dosing algorithm.",
                
                f"Your body processes {drug} more slowly than average. This means the medicine can build up in your system more easily. Your doctor will start you on a lower dose and check your blood more often to keep you safe. Think of it like a slower drain in your bathtub—we just adjust the water flow accordingly!"
            ),
            
            ("TPMT", "AZATHIOPRINE", "PM"): (
                f"TPMT poor metabolizer genotype ({diplotype}) with variants {', '.join(detected_variants)} confers severe thiopurine methyltransferase deficiency. CPIC recommends AVOIDING azathioprine due to critical risk of life-threatening bone marrow toxicity from 6-thioguanine nucleotide accumulation. Risk of severe myelosuppression, infections, and malignancy. Alternative immunosuppressants needed.",
                
                f"Your body cannot safely process {drug}. The medicine could build up to dangerous levels in your system, potentially harming your bone marrow. This is serious—do not take this medicine. Your doctor will prescribe a different immunosuppressant that's safe for you."
            ),
            
            ("DPYD", "FLUOROURACIL", "PM"): (
                f"DPYD deficiency from {diplotype} genotype (variants: {', '.join(detected_variants)}) causes profound impairment of dihydropyrimidine dehydrogenase. CPIC strongly recommends CONTRAINDICATION to fluorouracil-based chemotherapy due to unacceptable risk of severe, life-threatening toxicity (grade 3-5 diarrhea, neutropenia, thrombocytopenia). Patient requires alternative cancer therapy.",
                
                f"{drug} is CONTRAINDICATED for you. This is a cancer medicine your body cannot safely handle—it would cause severe side effects. Do not take this without discussing alternatives with your oncology team. Safe alternatives exist for your specific cancer."
            ),
        }
        
        # Try to find a matching explanation
        key = (gene, drug, phenotype)
        if key in clinical_map:
            return clinical_map[key]
        
        # Generic fallback
        variants_str = ", ".join(detected_variants) if detected_variants else "multiple variants"
        
        clinical_fb = f"Patient pharmacogenomic profile: {phenotype} phenotype for {gene} ({diplotype}). Detected variants: {variants_str}. This phenotype affects {drug} metabolism. Risk assessment: {risk_label}. Consult CPIC guidelines and clinical pharmacist for personalized dosing recommendations and monitoring requirements."
        
        patient_fb = f"Your genetic test shows your body processes {drug} differently. Your result ({phenotype} type) means: {risk_label.lower()}. Talk to your doctor about what this means for your treatment. Modern medicine has solutions for every genetic type!"
        
        return clinical_fb, patient_fb


def generate_dual_explanations(
    gene: str,
    drug: str,
    phenotype: str,
    risk_label: str,
    detected_variants: list,
    diplotype: str,
    api_key: Optional[str] = None
) -> Tuple[str, str]:
    """
    Convenience function to generate dual-layer explanations
    
    Returns:
        Tuple of (clinical_summary, patient_summary)
    """
    explainer = LLMExplainer(api_key=api_key)
    return explainer.generate_explanations(
        gene, drug, phenotype, risk_label, detected_variants, diplotype
    )
