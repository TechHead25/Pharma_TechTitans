#!/usr/bin/env python3
"""
End-to-end test for PharmaGuard 2.0 redesign with selection-first workflow
Tests:
  1. Drugs endpoint returns correct list
  2. Drug-specific VCF analysis works
  3. Dual-layer LLM explanations are generated
  4. Results include JSON export capability
"""

import asyncio
import httpx
import json
from pathlib import Path

API_URL = "http://localhost:8000/api/v1"
TEST_VCF_PATH = Path("tests/fixtures/sample_cyp2d6_pm.vcf")

async def test_drugs_endpoint():
    """Test /api/v1/drugs endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/drugs")
        assert response.status_code == 200
        data = response.json()
        assert "drugs" in data
        drugs = data["drugs"]
        assert "CODEINE" in drugs
        assert "WARFARIN" in drugs
        assert len(drugs) == 6
        print("✓ Drugs endpoint works correctly")
        return drugs

async def test_health():
    """Test health endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint OK")

async def test_analyze_with_drug_selection():
    """Test analysis with pre-selected drug"""
    if not TEST_VCF_PATH.exists():
        print("⚠ Test VCF file not found, skipping analysis test")
        return
    
    vcf_content = TEST_VCF_PATH.read_text()
    
    async with httpx.AsyncClient() as client:
        # Create test file
        files = {
            "file": ("test.vcf", vcf_content, "text/plain"),
            "drug": (None, "CODEINE")
        }
        
        response = await client.post(
            f"{API_URL}/analyze-vcf",
            files=files
        )
        
        assert response.status_code == 200
        results = response.json()
        
        # Verify response structure
        assert "patient_id" in results
        assert "drug" in results
        assert results["drug"] == "CODEINE"
        assert "llm_generated_explanation" in results
        
        # Verify dual-layer LLM explanations
        llm_exp = results["llm_generated_explanation"]
        assert "clinical_summary" in llm_exp
        assert "patient_summary" in llm_exp
        assert len(llm_exp["clinical_summary"]) > 0
        assert len(llm_exp["patient_summary"]) > 0
        
        # Verify clinical summary is different from patient summary
        assert llm_exp["clinical_summary"] != llm_exp["patient_summary"]
        
        print("✓ Analysis with drug selection works")
        print(f"  - Patient ID: {results['patient_id']}")
        print(f"  - Drug: {results['drug']}")
        print(f"  - Risk: {results['risk_assessment']['risk_label']}")
        print(f"  - Clinical summary (first 80 chars): {llm_exp['clinical_summary'][:80]}...")
        print(f"  - Patient summary (first 80 chars): {llm_exp['patient_summary'][:80]}...")
        
        # Verify results can be serialized as JSON
        json_str = json.dumps(results)
        assert len(json_str) > 0
        print("✓ Results can be exported as JSON")
        
        return results

async def test_invalid_drug():
    """Test that invalid drugs are rejected"""
    if not TEST_VCF_PATH.exists():
        print("⚠ Test VCF file not found, skipping invalid drug test")
        return
    
    vcf_content = TEST_VCF_PATH.read_text()
    
    async with httpx.AsyncClient() as client:
        files = {
            "file": ("test.vcf", vcf_content, "text/plain"),
            "drug": (None, "INVALID_DRUG")
        }
        
        response = await client.post(
            f"{API_URL}/analyze-vcf",
            files=files
        )
        
        assert response.status_code == 400
        print("✓ Invalid drug rejection works")

async def main():
    print("\n" + "="*60)
    print("PharmaGuard 2.0 - End-to-End Test Suite")
    print("="*60 + "\n")
    
    try:
        # Test health
        await test_health()
        
        # Test drugs endpoint
        drugs = await test_drugs_endpoint()
        print(f"  Available drugs: {', '.join(drugs)}\n")
        
        # Test selection-first workflow
        await test_analyze_with_drug_selection()
        
        # Test invalid drug rejection
        await test_invalid_drug()
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
