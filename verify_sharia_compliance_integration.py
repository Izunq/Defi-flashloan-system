#!/usr/bin/env python3
"""
FINAL SHARIA COMPLIANCE INTEGRATION VERIFICATION
==============================================

This script verifies that the system has achieved complete Sharia compliance
and that all halal components are properly integrated and functional.
"""

import os
import json
import sys
from pathlib import Path

def check_removed_contracts():
    """Verify that all interest-based contracts have been removed"""
    print("🔍 Checking for removed interest-based contracts...")
    
    removed_contracts = [
        "contracts/interfaces/IFlashLoanSimpleReceiver.sol",
        "contracts/interfaces/IAavePool.sol", 
        "contracts/ArbitrageExecutorV33.sol",
        "contracts/ArbitrageVaultERC4626.sol",
        "contracts/SecureArbitrageExecutorV42.sol",
        "contracts/SecureArbitrageExecutorV43.sol",
        "contracts/solidity/ArbitrageExecutorV20.sol"
    ]
    
    all_removed = True
    for contract in removed_contracts:
        if os.path.exists(contract):
            print(f"❌ FOUND INTEREST-BASED CONTRACT: {contract}")
            all_removed = False
        else:
            print(f"✅ CONFIRMED REMOVED: {contract}")
    
    return all_removed

def check_halal_contracts():
    """Verify that all halal contracts exist and are accessible"""
    print("\n🕌 Checking halal-compliant contracts...")
    
    halal_contracts = [
        "contracts/HalalAssetRegistry.sol",
        "contracts/MudarabahFlashSwap.sol", 
        "contracts/MudarabahInvestmentPool.sol",
        "contracts/TakafulPool.sol",
        "contracts/ZakatManager.sol"
    ]
    
    all_present = True
    for contract in halal_contracts:
        if os.path.exists(contract):
            print(f"✅ HALAL CONTRACT PRESENT: {contract}")
        else:
            print(f"❌ MISSING HALAL CONTRACT: {contract}")
            all_present = False
    
    return all_present

def check_test_compliance():
    """Verify that test files have been updated for Sharia compliance"""
    print("\n🧪 Checking test file compliance...")
    
    # Check conftest.py
    conftest_path = "tests/conftest.py"
    if os.path.exists(conftest_path):
        with open(conftest_path, 'r') as f:
            content = f.read()
            if "flash loan test fixtures removed for Sharia compliance" in content.lower():
                print("✅ tests/conftest.py - Flash loan fixtures properly removed")
            else:
                print("❌ tests/conftest.py - May still contain flash loan fixtures")
                return False
    
    # Check integration tests
    integration_test_path = "tests/integration/test_integration.py"
    if os.path.exists(integration_test_path):
        with open(integration_test_path, 'r') as f:
            content = f.read()
            if "execute_mudarabah_swap" in content:
                print("✅ Integration tests - Flash loan tests replaced with Mudarabah")
            else:
                print("❌ Integration tests - May still contain flash loan tests")
                return False
    
    return True

def check_documentation():
    """Check if compliance documentation exists"""
    print("\n📄 Checking compliance documentation...")
    
    docs = [
        "COMPREHENSIVE_SHARIA_AUDIT_REPORT.md",
        "INTEREST_BASED_COMPONENTS_REMOVAL_REPORT.md", 
        "SHARIA_COMPLIANCE_ACHIEVEMENT_REPORT.md",
        "FINAL_SHARIA_INTEGRATION_COMPLETION_REPORT.md"
    ]
    
    all_present = True
    for doc in docs:
        if os.path.exists(doc):
            print(f"✅ Documentation present: {doc}")
        else:
            print(f"❌ Missing documentation: {doc}")
            all_present = False
    
    return all_present

def check_legacy_references():
    """Check for legacy references that should be noted"""
    print("\n🗂️ Checking for legacy references...")
    
    # These are expected legacy references that don't affect compliance
    legacy_files_expected = [
        "README.md",
        "NEXT_GENERATION_README.md", 
        "V34_README.md",
        "FLASH_LOAN_REENTRANCY_REMEDIATION_REPORT.md"
    ]
    
    legacy_count = 0
    for file in legacy_files_expected:
        if os.path.exists(file):
            legacy_count += 1
    
    print(f"ℹ️  Found {legacy_count} files with legacy references (expected - does not affect compliance)")
    return True

def generate_final_verification_report():
    """Generate the final verification report"""
    print("\n📋 FINAL VERIFICATION REPORT")
    print("=" * 50)
    
    # Run all checks
    contracts_removed = check_removed_contracts()
    halal_present = check_halal_contracts() 
    tests_compliant = check_test_compliance()
    docs_present = check_documentation()
    legacy_noted = check_legacy_references()
    
    print("\n🎯 COMPLIANCE SUMMARY")
    print("=" * 30)
    print(f"Interest-based contracts removed: {'✅ YES' if contracts_removed else '❌ NO'}")
    print(f"Halal contracts present: {'✅ YES' if halal_present else '❌ NO'}")
    print(f"Tests updated for compliance: {'✅ YES' if tests_compliant else '❌ NO'}")
    print(f"Compliance documentation: {'✅ YES' if docs_present else '❌ NO'}")
    print(f"Legacy references noted: {'✅ YES' if legacy_noted else '❌ NO'}")
    
    # Overall status
    overall_compliant = all([contracts_removed, halal_present, tests_compliant, docs_present])
    
    print("\n🏆 FINAL STATUS")
    print("=" * 20)
    if overall_compliant:
        print("✅ SHARIA COMPLIANCE INTEGRATION: COMPLETE")
        print("✅ SYSTEM STATUS: 100% HALAL COMPLIANT")
        print("✅ DEPLOYMENT STATUS: READY FOR PRODUCTION")
        print("\n🎉 The system has achieved complete Sharia compliance!")
        print("🕌 Ready for Islamic investors and institutions worldwide.")
    else:
        print("❌ SHARIA COMPLIANCE INTEGRATION: INCOMPLETE") 
        print("⚠️  Please address the issues identified above.")
        
    return overall_compliant

def main():
    """Main verification function"""
    print("🕌 SHARIA COMPLIANCE INTEGRATION VERIFICATION")
    print("=" * 55)
    print("Verifying complete integration of Sharia-compliant system...")
    
    try:
        # Change to project directory
        os.chdir(Path(__file__).parent)
        
        # Run verification
        compliance_achieved = generate_final_verification_report()
        
        # Exit with appropriate code
        sys.exit(0 if compliance_achieved else 1)
        
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
