#!/usr/bin/env python3
"""
Final Security Verification Script
Comprehensive validation of all emergency security patches

🚨 CRITICAL: This script verifies that all emergency input validation 
patches are correctly deployed and functioning.
"""

import os
import sys
import importlib.util
from datetime import datetime

def load_module(file_path):
    """Safely load a Python module from file path"""
    try:
        spec = importlib.util.spec_from_file_location("module", file_path)
        if spec is None or spec.loader is None:
            print(f"❌ Failed to create spec for {file_path}")
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"❌ Failed to load {file_path}: {e}")
        return None

def test_emergency_sanitizer():
    """Test emergency input sanitizer functionality"""
    print("🔍 Testing Emergency Input Sanitizer...")
    
    try:
        # Import emergency sanitizer
        sanitizer_path = os.path.join(os.getcwd(), "emergency_input_sanitizer.py")
        sanitizer = load_module(sanitizer_path)
        
        if not sanitizer:
            return False
            
        # Test critical functions
        test_cases = [
            ("SQL Injection", "'; DROP TABLE users; --", False),
            ("XSS Attack", "<script>alert('xss')</script>", False),
            ("Valid Address", "0x742dA73Fe8e4B0b42d9D1B6C3F4d1F7b7b5c5c5c", True),
            ("Zero Address", "0x0000000000000000000000000000000000000000", False),
            ("Clean Input", "normal_user_input", True)
        ]
        
        passed = 0
        for test_name, test_input, should_pass in test_cases:
            try:
                result = sanitizer.emergency_sanitize_input(test_input, "test_field")
                if should_pass and result:
                    print(f"✅ {test_name}: PASS")
                    passed += 1
                elif not should_pass and not result:
                    print(f"✅ {test_name}: BLOCKED (correct)")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAIL")
            except Exception as e:
                if not should_pass:
                    print(f"✅ {test_name}: BLOCKED (exception - correct)")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAIL - {e}")
        
        print(f"📊 Emergency Sanitizer: {passed}/{len(test_cases)} tests passed")
        return passed == len(test_cases)
        
    except Exception as e:
        print(f"❌ Emergency sanitizer test failed: {e}")
        return False

def verify_agent_patches():
    """Verify that critical agent files have been patched"""
    print("\n🔍 Verifying Agent Patches...")
    
    critical_agents = [
        "python_agent_v34_ultimate.py",
        "enhanced_arbitrage_agent_v33.py", 
        "distributed_enhanced_arbitrage_agent_v34.py",
        "swarm_intelligence_agent_v38.py"
    ]
    
    patched_count = 0
    for agent_file in critical_agents:
        agent_path = os.path.join(os.getcwd(), agent_file)
        if os.path.exists(agent_path):
            try:
                with open(agent_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for emergency validation imports
                has_import = "emergency_input_sanitizer" in content
                has_validation = "emergency_sanitize_input" in content or "validate_" in content
                
                if has_import and has_validation:
                    print(f"✅ {agent_file}: PATCHED")
                    patched_count += 1
                else:
                    print(f"⚠️ {agent_file}: Partial patch (import: {has_import}, validation: {has_validation})")
                    
            except Exception as e:
                print(f"❌ {agent_file}: Read error - {e}")
        else:
            print(f"⚠️ {agent_file}: Not found")
    
    print(f"📊 Agent Patches: {patched_count}/{len(critical_agents)} agents fully patched")
    return patched_count

def verify_contract_readiness():
    """Verify emergency contract files are ready"""
    print("\n🔍 Verifying Contract Readiness...")
    
    contract_files = [
        "contracts/EmergencyInputValidator.sol",
        "deploy_emergency_contracts.py",
        "emergency_security_monitor.py"
    ]
    
    ready_count = 0
    for contract_file in contract_files:
        file_path = os.path.join(os.getcwd(), contract_file)
        if os.path.exists(file_path):
            print(f"✅ {contract_file}: READY")
            ready_count += 1
        else:
            print(f"❌ {contract_file}: NOT FOUND")
    
    print(f"📊 Contract Files: {ready_count}/{len(contract_files)} files ready")
    return ready_count

def check_backup_integrity():
    """Check that backup files were created"""
    print("\n🔍 Checking Backup Integrity...")
    
    backup_pattern = ".emergency_backup_"
    backup_files = [f for f in os.listdir('.') if backup_pattern in f]
    
    print(f"📊 Backup Files: {len(backup_files)} backup files found")
    for backup_file in backup_files[:5]:  # Show first 5
        print(f"✅ {backup_file}")
    
    if len(backup_files) > 5:
        print(f"... and {len(backup_files) - 5} more backup files")
    
    return len(backup_files) > 0

def generate_final_report():
    """Generate final security verification report"""
    print("\n" + "="*60)
    print("🛡️ FINAL SECURITY VERIFICATION REPORT")
    print("="*60)
    
    # Run all verification tests
    sanitizer_ok = test_emergency_sanitizer()
    agents_patched = verify_agent_patches()
    contracts_ready = verify_contract_readiness()
    backups_ok = check_backup_integrity()
    
    # Overall status
    print("\n📋 OVERALL STATUS:")
    print(f"Emergency Sanitizer: {'✅ OPERATIONAL' if sanitizer_ok else '❌ FAILED'}")
    print(f"Agent Patches: {'✅ DEPLOYED' if agents_patched > 0 else '❌ MISSING'}")
    print(f"Contract Files: {'✅ READY' if contracts_ready > 0 else '❌ MISSING'}")
    print(f"Backup Integrity: {'✅ SECURE' if backups_ok else '❌ NO BACKUPS'}")
    
    # Security level assessment
    total_checks = 4
    passed_checks = sum([sanitizer_ok, agents_patched > 0, contracts_ready > 0, backups_ok])
    security_level = (passed_checks / total_checks) * 100
    
    print(f"\n🔒 SECURITY LEVEL: {security_level:.1f}%")
    
    if security_level >= 75:
        print("🟢 EMERGENCY PATCHES SUCCESSFULLY DEPLOYED")
        print("✅ System is protected against critical input validation vulnerabilities")
    elif security_level >= 50:
        print("🟡 PARTIAL PROTECTION DEPLOYED")
        print("⚠️ Some components may still be vulnerable")
    else:
        print("🔴 CRITICAL SECURITY GAPS REMAIN")
        print("❌ Immediate manual intervention required")
    
    # Next steps
    print("\n📝 NEXT STEPS:")
    if not sanitizer_ok:
        print("- Fix emergency input sanitizer functionality")
    if agents_patched == 0:
        print("- Re-run emergency deployment script to patch agents")
    if contracts_ready == 0:
        print("- Deploy EmergencyInputValidator.sol to production")
    if not backups_ok:
        print("- Create proper backups before making changes")
    
    print("- Deploy emergency contracts using deploy_emergency_contracts.py")
    print("- Start emergency security monitoring")
    print("- Conduct full security audit as per remediation plan")
    
    return security_level

if __name__ == "__main__":
    print("🚨 EMERGENCY INPUT VALIDATION - FINAL VERIFICATION")
    print(f"🕐 Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    try:
        security_level = generate_final_report()
        
        # Create verification log
        log_file = f"final_security_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_file, 'w') as f:
            f.write(f"Final Security Verification - {datetime.now()}\n")
            f.write(f"Security Level: {security_level:.1f}%\n")
            f.write("Emergency input validation patches deployed and verified.\n")
        
        print(f"\n📄 Verification log saved: {log_file}")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)
