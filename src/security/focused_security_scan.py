#!/usr/bin/env python3
"""
Focused Access Control Scanner - Only scans actual contract implementations
"""

import os
import re
from pathlib import Path

def scan_critical_contracts():
    workspace = Path('c:/Users/mahia/New_Flashloan')
    vulnerabilities = []
    
    # Focus on actual contract files, not interfaces or node_modules
    contract_files = [
        'ArbitrageExecutorV20.sol',
        'solidity_contracts_v26.sol',
        'contracts/GenericStrategy.sol',
        'contracts/ArbitrageExecutorV33.sol',
        'contracts/SecurityEnhancedExecutor.sol',
        'contracts/MudarabahInvestmentPool.sol',
        'contracts/StrategyIncubatorV33.sol',
        'contracts/ProofAwareExecutorV35.sol',
        'contracts/EmergencyAccessControlManager.sol',
        'contracts/AccessControlSecurityFix.sol'
    ]
    
    critical_functions = [
        'executeOperation',
        'executeArbitrage', 
        'proposeStrategy',
        'slashStrategy',
        'emergencyWithdraw',
        'performSecurityMonitoring',
        'requestEmergencyWithdrawal',
        'executeFlashLoan',
        'withdrawFunds',
        'transferFunds'
    ]
    
    for contract_file in contract_files:
        file_path = workspace / contract_file
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    for func in critical_functions:
                        if f'function {func}' in line and 'external' in line:
                            # Check next few lines for access control
                            function_block = line
                            for j in range(i+1, min(i+5, len(lines))):
                                if '{' in lines[j]:
                                    break
                                function_block += ' ' + lines[j].strip()
                            
                            # Check for access control modifiers
                            has_access_control = any(mod in function_block for mod in [
                                'onlyRole', 'onlyOwner', 'onlyAdmin', 'onlyExecutor', 
                                'onlyEmergency', 'onlyManager', 'onlyApproved'
                            ])
                            
                            # Skip if it's an interface declaration
                            if not has_access_control and 'interface ' not in content[:content.find(line)]:
                                vulnerabilities.append({
                                    'function': func,
                                    'file': contract_file,
                                    'line': i + 1,
                                    'signature': function_block.strip()
                                })
                                
            except Exception as e:
                print(f"Error processing {contract_file}: {e}")
    
    return vulnerabilities

def check_fixes_status():
    """Check what fixes have already been applied"""
    workspace = Path('c:/Users/mahia/New_Flashloan')
    
    # Check specific functions mentioned in the audit reports
    fixes_status = {}
    
    # Check proposeStrategy in solidity_contracts_v26.sol
    v26_file = workspace / 'solidity_contracts_v26.sol'
    if v26_file.exists():
        content = v26_file.read_text()
        if 'function proposeStrategy' in content:
            if 'onlyRole(STRATEGY_PROPOSER_ROLE)' in content:
                fixes_status['proposeStrategy_v26'] = 'FIXED'
            else:
                fixes_status['proposeStrategy_v26'] = 'VULNERABLE'
    
    # Check executeArbitrage in ArbitrageExecutorV20.sol
    exec_file = workspace / 'ArbitrageExecutorV20.sol'
    if exec_file.exists():
        content = exec_file.read_text()
        if 'function executeArbitrage' in content:
            if 'onlyRole(STRATEGY_EXECUTOR_ROLE)' in content:
                fixes_status['executeArbitrage_v20'] = 'FIXED'
            else:
                fixes_status['executeArbitrage_v20'] = 'VULNERABLE'
    
    # Check slashStrategy in solidity_contracts_v26.sol
    if v26_file.exists():
        content = v26_file.read_text()
        if 'function slashStrategy' in content:
            if 'onlyRole(EMERGENCY_ROLE)' in content:
                fixes_status['slashStrategy_v26'] = 'FIXED'
            else:
                fixes_status['slashStrategy_v26'] = 'VULNERABLE'
    
    return fixes_status

def main():
    print("🔍 Focused Access Control Security Scan")
    print("=" * 50)
    
    # Check current fix status
    fixes_status = check_fixes_status()
    print("\n📊 CRITICAL FUNCTION STATUS:")
    for func, status in fixes_status.items():
        status_icon = "✅" if status == "FIXED" else "🚨"
        print(f"{status_icon} {func}: {status}")
    
    # Scan for remaining vulnerabilities
    vulnerabilities = scan_critical_contracts()
    
    print(f"\n🚨 REMAINING VULNERABILITIES: {len(vulnerabilities)}")
    
    if vulnerabilities:
        print("\nCritical functions still needing fixes:")
        for vuln in vulnerabilities:
            print(f"- {vuln['function']} in {vuln['file']}:{vuln['line']}")
        
        print(f"\n🛠️ IMMEDIATE ACTION REQUIRED:")
        print("The following functions need access control modifiers added:")
        
        for vuln in vulnerabilities[:5]:  # Top 5 most critical
            print(f"\n📝 {vuln['function']} - {vuln['file']}")
            print(f"   Line {vuln['line']}: {vuln['signature'][:100]}...")
            
            # Suggest appropriate modifier
            func = vuln['function']
            if 'execute' in func.lower():
                modifier = 'onlyRole(STRATEGY_EXECUTOR_ROLE)'
            elif 'propose' in func.lower():
                modifier = 'onlyRole(STRATEGY_PROPOSER_ROLE)'
            elif 'emergency' in func.lower() or 'slash' in func.lower():
                modifier = 'onlyRole(EMERGENCY_ROLE)'
            else:
                modifier = 'onlyRole(DEFAULT_ADMIN_ROLE)'
            
            print(f"   💡 Recommended fix: Add {modifier}")
    
    else:
        print("🎉 All critical functions have proper access control!")
    
    # Summary
    fixed_count = len([s for s in fixes_status.values() if s == 'FIXED'])
    total_critical = len(fixes_status) + len(vulnerabilities)
    
    print(f"\n📈 SECURITY PROGRESS:")
    print(f"✅ Fixed: {fixed_count}")
    print(f"🚨 Remaining: {len(vulnerabilities)}")
    print(f"📊 Progress: {fixed_count/(fixed_count+len(vulnerabilities))*100:.1f}% complete")

if __name__ == "__main__":
    main()
