import pytest
from app.parsers.vcf_parser import VCFParser, parse_vcf_file


class TestVCFParser:
    """Test VCF parsing functionality"""
    
    def test_parse_valid_cyp2d6_vcf(self):
        """Test parsing CYP2D6 variant"""
        vcf_content = """##fileformat=VCFv4.2
##fileDate=20240219
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr22	42127941	rs1065852	G	A	60	PASS	GENE=CYP2D6;STAR=*4;RS=rs1065852"""
        
        result, success = parse_vcf_file(vcf_content)
        
        assert success is True
        assert result['total_variants'] == 1
        assert 'CYP2D6' in result['target_genes_found']
        assert result['variants'][0]['gene'] == 'CYP2D6'
        assert result['variants'][0]['rsid'] == 'rs1065852'
    
    def test_parse_multiple_genes(self):
        """Test parsing multiple gene variants"""
        vcf_content = """##fileformat=VCFv4.2
##fileDate=20240219
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr22	42127941	rs1065852	G	A	60	PASS	GENE=CYP2D6;STAR=*4;RS=rs1065852
chr10	96621094	rs2687119	G	C	60	PASS	GENE=CYP2C19;STAR=*2;RS=rs2687119"""
        
        result, success = parse_vcf_file(vcf_content)
        
        assert success is True
        assert result['total_variants'] == 2
        assert set(result['target_genes_found']) == {'CYP2D6', 'CYP2C19'}
    
    def test_invalid_vcf_missing_header(self):
        """Test error handling for invalid VCF"""
        vcf_content = """chr22	42127941	rs1065852	G	A	60	PASS	GENE=CYP2D6"""
        
        result, success = parse_vcf_file(vcf_content)
        
        assert success is False
        assert 'error' in result
    
    def test_empty_vcf(self):
        """Test handling empty VCF"""
        vcf_content = ""
        
        result, success = parse_vcf_file(vcf_content)
        
        assert success is False
    
    def test_vcf_filters_non_target_genes(self):
        """Test that non-target genes are filtered out"""
        vcf_content = """##fileformat=VCFv4.2
##fileDate=20240219
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr1	100	rs123	G	A	60	PASS	GENE=UNKNOWN;STAR=*1;RS=rs123
chr22	42127941	rs1065852	G	A	60	PASS	GENE=CYP2D6;STAR=*4;RS=rs1065852"""
        
        result, success = parse_vcf_file(vcf_content)
        
        assert success is True
        assert result['total_variants'] == 1
        assert 'CYP2D6' in result['target_genes_found']
