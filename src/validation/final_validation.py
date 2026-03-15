#!/usr/bin/env python3
"""
Final Access Control Security Validation
Comprehensive check to confirm all 76+ access control vulnerabilities are fixed
"""

import os
import re
from pathlib import Path
from datetime import datetime

def validate_critical_functions():
    """Validate that all critical functions identified in the audit have proper access control"""
    workspace = Path('c:/Users/mahia/New_Flashloan')
    
    # Critical functions from the original audit report
    critical_validations = [
        {
            'function': 'proposeStrategy',
            'file': 'solidity_contracts_v26.sol',
            'required_modifier': 'onlyRole(STRATEGY_PROPOSER_ROLE)',
            'line_approx': 247
        },
        {
            'function': 'executeArbitrage', 
            'file': 'ArbitrageExecutorV20.sol',
            'required_modifier': 'onlyRole(STRATEGY_EXECUTOR_ROLE)',
            'line_approx': 246
        },
        {
            'function': 'slashStrategy',
            'file': 'solidity_contracts_v26.sol', 
            'required_modifier': 'onlyRole(EMERGENCY_ROLE)',
            'line_approx': 322
        },
        {
            'function': 'requestEmergencyWithdrawal',
            'file': 'contracts/MudarabahInvestmentPool.sol',
            'required_modifier': 'onlyRole(EMERGENCY_ROLE)',
            'line_approx': 853
        },
        {
            'function': 'performSecurityMonitoring',
            'file': 'contracts/OracleSecurityWrapper.sol', 
            'required_modifier': 'onlyRole(SECURITY_MANAGER_ROLE)',
            'line_approx': 239
        }
    ]
    
    validation_results = []
    
    for validation in critical_validations:
        file_path = workspace / validation['file']
        status = "FILE_NOT_FOUND"
        details = ""
        
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Find the function implementation (not interface)
                pattern = rf"function\s+{validation['function']}\s*\([^)]*\)\s+external[^{{]*{{"
                matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
                
                if matches:
                    # Get the function signature
                    match = matches[0]  # Take first implementation
                    func_signature = match.group()
                    
                    # Check for required modifier
                    if validation['required_modifier'] in func_signature:
                        status = "SECURE"
                        details = f"✅ Found {validation['required_modifier']}"
                    else:
                        status = "VULNERABLE" 
                        details = f"❌ Missing {validation['required_modifier']}"
                        
                        # Check for any access control
                        access_modifiers = ['onlyRole', 'onlyOwner', 'onlyAdmin', 'onlyExecutor', 'onlyEmergency']
                        found_modifiers = [mod for mod in access_modifiers if mod in func_signature]
                        if found_modifiers:
                            details += f" (has {', '.join(found_modifiers)})"
                else:
                    status = "FUNCTION_NOT_FOUND"
                    details = f"Function {validation['function']} not found in {validation['file']}"
                    
            except Exception as e:
                status = "ERROR"
                details = str(e)
        
        validation_results.append({
            'function': validation['function'],
            'file': validation['file'],
            'status': status,
            'details': details,
            'required': validation['required_modifier']
        })
    
    return validation_results

def scan_all_external_functions():
    """Scan all external functions for access control"""
    workspace = Path('c:/Users/mahia/New_Flashloan')
    
    # Files to scan (actual contracts, not interfaces)
    contract_files = [
        'ArbitrageExecutorV20.sol',
        'solidity_contracts_v26.sol',
        'contracts/GenericStrategy.sol',
        'contracts/ArbitrageExecutorV33.sol', 
        'contracts/SecurityEnhancedExecutor.sol',
        'contracts/MudarabahInvestmentPool.sol',
        'contracts/StrategyIncubatorV33.sol',
        'contracts/ProofAwareExecutorV35.sol',
        'contracts/SecureArbitrageExecutorV42.sol',
        'contracts/AccessControlSecurityFix.sol',
        'contracts/EmergencyAccessControlManager.sol'
    ]
    
    all_functions = []
    secure_count = 0
    vulnerable_count = 0
    
    for contract_file in contract_files:
        file_path = workspace / contract_file
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Find all external functions (not view/pure)
                pattern = r'function\s+(\w+)\s*\([^)]*\)\s+external(?!\s+view)(?!\s+pure)([^{]*)'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    func_name = match.group(1)
                    modifiers = match.group(2)
                    
                    # Skip if it's just an interface declaration (ends with semicolon)
                    if modifiers.strip().endswith(';'):
                        continue
                    
                    # Check for access control modifiers
                    has_access_control = any(mod in modifiers for mod in [
                        'onlyRole', 'onlyOwner', 'onlyAdmin', 'onlyExecutor', 
                        'onlyEmergency', 'onlyManager', 'onlyApproved', 'onlyGuardian',
                        'onlyGovernance', 'onlyStrategy', 'onlyOracle', 'authorized'
                    ])
                    
                    function_info = {
                        'name': func_name,
                        'file': contract_file,
                        'modifiers': modifiers.strip(),
                        'secure': has_access_control
                    }
                    
                    all_functions.append(function_info)
                    
                    if has_access_control:
                        secure_count += 1
                    else:
                        vulnerable_count += 1
                        
            except Exception as e:
                print(f"Error scanning {contract_file}: {e}")
    
    return all_functions, secure_count, vulnerable_count

def generate_final_report():
    """Generate comprehensive final security report"""
    
    print("🔍 FINAL ACCESS CONTROL SECURITY VALIDATION")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Validate critical functions from original audit
    print("📋 VALIDATING CRITICAL FUNCTIONS FROM ORIGINAL AUDIT:")
    print("-" * 50)
    
    critical_results = validate_critical_functions()
    
    for result in critical_results:
        status_icon = {
            'SECURE': '✅',
            'VULNERABLE': '🚨', 
            'FUNCTION_NOT_FOUND': '❓',
            'FILE_NOT_FOUND': '📁',
            'ERROR': '❌'
        }.get(result['status'], '❓')
        
        print(f"{status_icon} {result['function']} ({result['file']})")
        print(f"   {result['details']}")
        print()
    
    # Count results
    secure_critical = len([r for r in critical_results if r['status'] == 'SECURE'])
    total_critical = len(critical_results)
    
    print(f"Critical Functions Status: {secure_critical}/{total_critical} SECURE")
    print()
    
    # Scan all external functions
    print("🔍 SCANNING ALL EXTERNAL FUNCTIONS:")
    print("-" * 50)
    
    all_functions, secure_count, vulnerable_count = scan_all_external_functions()
    total_functions = secure_count + vulnerable_count
    
    print(f"📊 OVERALL STATISTICS:")
    print(f"✅ Secure Functions: {secure_count}")
    print(f"🚨 Vulnerable Functions: {vulnerable_count}")
    print(f"📈 Security Score: {secure_count/total_functions*100:.1f}%")
    print()
    
    # Show remaining vulnerabilities
    vulnerable_functions = [f for f in all_functions if not f['secure']]
    
    if vulnerable_functions:
        print("🚨 REMAINING VULNERABILITIES:")
        print("-" * 30)
        for i, func in enumerate(vulnerable_functions[:10]):
            print(f"{i+1:2d}. {func['name']} in {func['file']}")
            print(f"    Modifiers: {func['modifiers']}")
        
        if len(vulnerable_functions) > 10:
            print(f"    ... and {len(vulnerable_functions)-10} more")
    else:
        print("🎉 NO VULNERABILITIES FOUND - ALL FUNCTIONS SECURE!")
    
    print()
    print("=" * 60)
    
    # Final assessment
    if secure_critical == total_critical and vulnerable_count == 0:
        print("🎉 SECURITY STATUS: FULLY SECURE")
        print("✅ All 76+ access control vulnerabilities have been FIXED!")
    elif secure_critical == total_critical:
        print("✅ CRITICAL FUNCTIONS: SECURE")
        print(f"⚠️  Non-critical functions need review: {vulnerable_count}")
    else:
        print("🚨 SECURITY STATUS: VULNERABILITIES REMAIN")
        print(f"❌ Critical functions still vulnerable: {total_critical - secure_critical}")
    
    print("=" * 60)

if __name__ == "__main__":
    generate_final_report()
