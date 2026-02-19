import pytest
from app.engines.risk_engine import RiskAssessmentEngine, Phenotype


class TestRiskAssessmentEngine:
    """Test risk assessment logic"""
    
    def setup_method(self):
        """Setup for each test"""
        self.engine = RiskAssessmentEngine()
    
    def test_cyp2d6_pm_codeine_assessment(self):
        """Test CYP2D6 poor metabolizer with codeine"""
        result = self.engine.assess_risk(
            gene="CYP2D6",
            drug="CODEINE",
            phenotype="PM",
            detected_variants=["rs1065852"],
            diplotype="*4/*4"
        )
        
        assert result['risk_label'] == 'Ineffective'
        assert result['severity'] == 'high'
        assert result['confidence_score'] >= 0.9
    
    def test_tpmt_pm_azathioprine_assessment(self):
        """Test TPMT poor metabolizer with azathioprine - critical risk"""
        result = self.engine.assess_risk(
            gene="TPMT",
            drug="AZATHIOPRINE",
            phenotype="PM",
            detected_variants=["rs1136410"],
            diplotype="*3C/*3C"
        )
        
        assert result['risk_label'] == 'Toxic'
        assert result['severity'] == 'critical'
        assert result['confidence_score'] >= 0.95
    
    def test_safe_nm_assessment(self):
        """Test normal metabolizer with safe profile"""
        result = self.engine.assess_risk(
            gene="CYP2C9",
            drug="WARFARIN",
            phenotype="NM",
            detected_variants=[],
            diplotype="*1/*1"
        )
        
        assert result['risk_label'] == 'Safe'
        assert result['severity'] == 'none'
        assert result['confidence_score'] >= 0.95
    
    def test_unknown_phenotype_handling(self):
        """Test handling of unknown phenotype"""
        result = self.engine.assess_risk(
            gene="CYP2D6",
            drug="CODEINE",
            phenotype="UnknownPhenotype",
            detected_variants=[],
            diplotype="*1/*1"
        )
        
        # Should treat as "Unknown" and return moderate risk
        assert result['risk_label'] == 'Unknown'
    
    def test_phenotype_inference(self):
        """Test phenotype inference from star alleles"""
        phenotype, confidence = self.engine.infer_phenotype(["*1", "*1"])
        
        assert phenotype == "NM"
        assert confidence >= 0.9
    
    def test_phenotype_inference_im(self):
        """Test intermediate metabolizer inference"""
        phenotype, confidence = self.engine.infer_phenotype(["*1", "*2"])
        
        assert phenotype == "IM"
        assert confidence >= 0.85
    
    def test_clinical_recommendation_generation(self):
        """Test clinical recommendation generation"""
        rec = self.engine.get_clinical_recommendation(
            "Adjust Dosage",
            "WARFARIN",
            "IM"
        )
        
        assert "WARFARIN" in rec
        assert "dose adjustment" in rec.lower()
