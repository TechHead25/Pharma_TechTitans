import re
from typing import Dict, List, Optional, Tuple


class VCFParser:
    """Parse VCF v4.2 files for pharmacogenomic analysis"""
    
    def __init__(self, max_size_mb: int = 5):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.target_genes = {
            "CYP2D6", "CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "DPYD"
        }
        self.gene_drug_mapping = {
            "CYP2D6": ["CODEINE"],
            "CYP2C19": ["WARFARIN", "CLOPIDOGREL"],
            "CYP2C9": ["WARFARIN"],
            "SLCO1B1": ["SIMVASTATIN"],
            "TPMT": ["AZATHIOPRINE"],
            "DPYD": ["FLUOROURACIL"],
        }
    
    def parse_vcf(self, content: str) -> Dict:
        """
        Parse VCF v4.2 file content
        
        Args:
            content: Raw VCF file content
            
        Returns:
            Dictionary with parsed variants and metadata
        """
        lines = content.strip().split('\n')
        metadata = {}
        variants = []
        header_line_idx = -1
        
        # Parse header and extract metadata
        for idx, line in enumerate(lines):
            if line.startswith('##fileformat'):
                metadata['fileformat'] = line.split('=')[1]
            elif line.startswith('##'):
                continue
            elif line.startswith('#CHROM'):
                header_line_idx = idx
                break
        
        if header_line_idx == -1:
            raise ValueError("Invalid VCF: Missing header line")
        
        # Parse variants
        for line in lines[header_line_idx + 1:]:
            if not line.strip() or line.startswith('#'):
                continue
            
            variant = self._parse_variant_line(line)
            if variant:
                variants.append(variant)
        
        return {
            "metadata": metadata,
            "variants": variants,
            "total_variants": len(variants),
            "target_genes_found": list(set([v.get("gene") for v in variants if v.get("gene")])),
        }
    
    def _parse_variant_line(self, line: str) -> Optional[Dict]:
        """
        Parse a single VCF variant line
        
        VCF format: CHROM POS ID REF ALT QUAL FILTER INFO [FORMAT SAMPLE_DATA...]
        """
        fields = line.split('\t')
        if len(fields) < 8:
            return None
        
        chrom, pos, vid, ref, alt, qual, filt, info = fields[:8]
        
        # Parse INFO field for GENE, STAR, RS
        info_dict = self._parse_info(info)
        
        # Only keep variants for target genes
        gene = info_dict.get("GENE")
        if gene not in self.target_genes:
            return None
        
        return {
            "chrom": chrom,
            "pos": pos,
            "id": vid if vid != "." else None,
            "ref": ref,
            "alt": alt,
            "qual": qual,
            "filter": filt,
            "gene": gene,
            "star": info_dict.get("STAR"),
            "rsid": info_dict.get("RS"),
            "info": info_dict,
        }
    
    def _parse_info(self, info_string: str) -> Dict:
        """
        Parse INFO field following VCF specification
        Returns dict with key=value pairs
        """
        info_dict = {}
        if not info_string or info_string == ".":
            return info_dict
        
        for item in info_string.split(';'):
            if '=' in item:
                key, value = item.split('=', 1)
                info_dict[key] = value
            else:
                info_dict[item] = True
        
        return info_dict
    
    def validate_vcf_structure(self, content: str) -> Tuple[bool, str]:
        """Validate basic VCF structure"""
        if not content:
            return False, "Empty file"
        
        lines = content.strip().split('\n')
        if not any(line.startswith('##fileformat=VCF') for line in lines[:5]):
            return False, "Missing VCF format declaration"
        
        if not any(line.startswith('#CHROM') for line in lines):
            return False, "Missing header line"
        
        return True, "Valid VCF structure"


def parse_vcf_file(file_content: str) -> Tuple[Dict, bool]:
    """
    Main function to parse VCF file
    
    Returns:
        Tuple of (parsed_data, success_flag)
    """
    parser = VCFParser()
    
    # Validate structure
    is_valid, msg = parser.validate_vcf_structure(file_content)
    if not is_valid:
        return {"error": msg}, False
    
    try:
        result = parser.parse_vcf(file_content)
        return result, True
    except Exception as e:
        return {"error": str(e)}, False
