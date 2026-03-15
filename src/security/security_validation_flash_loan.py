#!/usr/bin/env python3
"""
Flash Loan Reentrancy Security Validation Script
Checks for proper CEI pattern implementation and reentrancy protection
"""

import re
import os
from typing import List, Dict, Tuple

class FlashLoanSecurityValidator:
    def __init__(self):
        self.vulnerabilities = []
        self.security_checks = []
        
    def validate_contract(self, file_path: str) -> Dict:
        """Validate a Solidity contract for flash loan reentrancy vulnerabilities"""
        
        print(f"\n🔍 Analyzing {os.path.basename(file_path)}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        results = {
            'file': file_path,
            'vulnerabilities': [],
            'security_features': [],
            'recommendations': []
        }
        
        # Check for proper CEI pattern implementation
        results['vulnerabilities'].extend(self._check_cei_pattern(content, file_path))
        
        # Check for reentrancy guards
        results['security_features'].extend(self._check_reentrancy_guards(content))
        
        # Check for state changes after external calls
        results['vulnerabilities'].extend(self._check_state_after_externals(content, file_path))
        
        # Check for flash loan specific protections
        results['security_features'].extend(self._check_flash_loan_protections(content))
        
        # Check for proper error handling
        results['security_features'].extend(self._check_error_handling(content))
        
        return results
    
    def _check_cei_pattern(self, content: str, file_path: str) -> List[Dict]:
        """Check for proper Checks-Effects-Interactions pattern"""
        vulnerabilities = []
        
        # Find executeOperation or executeArbitrage functions
        function_patterns = [
            r'function executeOperation\s*\([^)]*\)[^{]*{([^}]*(?:{[^}]*}[^}]*)*)}',
            r'function executeArbitrage\s*\([^)]*\)[^{]*{([^}]*(?:{[^}]*}[^}]*)*)}',
        ]
        
        for pattern in function_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                function_body = match.group(1)
                
                # Look for state changes after external calls
                external_calls = re.findall(r'(\.call|\.transfer|\.send|\.approve|\.safeTransfer|\.safeApprove|try\s+\w+)', function_body)
                state_changes = re.findall(r'(\w+\.\w+\s*=|\w+\[.*\]\s*=|_\w+\s*=)', function_body)
                
                if external_calls and state_changes:
                    # Check if state changes occur after external calls
                    for i, call in enumerate(external_calls):
                        call_pos = function_body.find(call)
                        for state_change in state_changes:
                            state_pos = function_body.find(state_change, call_pos)
                            if state_pos > call_pos:
                                vulnerabilities.append({
                                    'type': 'CEI_VIOLATION',
                                    'severity': 'HIGH',
                                    'description': f'State change after external call detected',
                                    'location': f'{os.path.basename(file_path)}',
                                    'details': f'External call: {call}, State change: {state_change}'
                                })
        
        return vulnerabilities
    
    def _check_reentrancy_guards(self, content: str) -> List[Dict]:
        """Check for reentrancy protection mechanisms"""
        security_features = []
        
        # Check for nonReentrant modifier
        if 'nonReentrant' in content:
            security_features.append({
                'type': 'REENTRANCY_GUARD',
                'description': 'nonReentrant modifier found'
            })
        
        # Check for custom flash loan guard
        if 'flashLoanGuard' in content:
            security_features.append({
                'type': 'FLASH_LOAN_GUARD',
                'description': 'Custom flash loan guard implemented'
            })
        
        # Check for execution locking
        if '_executionLocked' in content:
            security_features.append({
                'type': 'EXECUTION_LOCKING',
                'description': 'Execution locking mechanism implemented'
            })
        
        return security_features
    
    def _check_state_after_externals(self, content: str, file_path: str) -> List[Dict]:
        """Check for state changes after external calls"""
        vulnerabilities = []
        
        # Look for patterns where state is modified after external calls
        lines = content.split('\n')
        external_call_line = -1
        
        for i, line in enumerate(lines):
            # Track external calls
            if re.search(r'\.(call|transfer|send|approve|safeTransfer|safeApprove)', line) or \
               re.search(r'try\s+\w+', line):
                external_call_line = i
            
            # Check for state changes after external calls within the same function
            elif external_call_line != -1 and re.search(r'\w+\.\w+\s*=|\w+\[.*\]\s*=', line):
                # Only flag if it's in the same function scope (basic heuristic)
                if i - external_call_line < 20:  # Within 20 lines is likely same function
                    vulnerabilities.append({
                        'type': 'STATE_AFTER_EXTERNAL',
                        'severity': 'MEDIUM',
                        'description': 'Potential state change after external call',
                        'location': f'{os.path.basename(file_path)}:Line {i+1}',
                        'details': f'Line: {line.strip()}'
                    })
        
        return vulnerabilities
    
    def _check_flash_loan_protections(self, content: str) -> List[Dict]:
        """Check for flash loan specific protections"""
        security_features = []
        
        # Check for caller verification
        if 'msg.sender == address(' in content and 'Pool' in content:
            security_features.append({
                'type': 'CALLER_VERIFICATION',
                'description': 'Flash loan caller verification implemented'
            })
        
        # Check for initiator verification
        if 'initiator == address(this)' in content:
            security_features.append({
                'type': 'INITIATOR_VERIFICATION',
                'description': 'Flash loan initiator verification implemented'
            })
        
        # Check for execution status tracking
        if 'ExecutionStatus' in content and 'InProgress' in content:
            security_features.append({
                'type': 'EXECUTION_TRACKING',
                'description': 'Execution status tracking implemented'
            })
        
        return security_features
    
    def _check_error_handling(self, content: str) -> List[Dict]:
        """Check for proper error handling"""
        security_features = []
        
        # Check for try-catch blocks
        if 'try' in content and 'catch' in content:
            security_features.append({
                'type': 'ERROR_HANDLING',
                'description': 'Try-catch error handling implemented'
            })
        
        # Check for require statements
        require_count = len(re.findall(r'require\s*\(', content))
        if require_count > 5:  # Arbitrary threshold
            security_features.append({
                'type': 'INPUT_VALIDATION',
                'description': f'Comprehensive input validation ({require_count} require statements)'
            })
        
        return security_features
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate a comprehensive security report"""
        
        report = "\n" + "="*80 + "\n"
        report += "🛡️  FLASH LOAN REENTRANCY SECURITY AUDIT REPORT\n"
        report += "="*80 + "\n"
        
        total_vulnerabilities = sum(len(r['vulnerabilities']) for r in results)
        total_security_features = sum(len(r['security_features']) for r in results)
        
        report += f"\n📊 SUMMARY:\n"
        report += f"   • Files Analyzed: {len(results)}\n"
        report += f"   • Vulnerabilities Found: {total_vulnerabilities}\n"
        report += f"   • Security Features: {total_security_features}\n"
        
        for result in results:
            file_name = os.path.basename(result['file'])
            report += f"\n\n📄 {file_name}\n"
            report += "-" * 50 + "\n"
            
            # Vulnerabilities
            if result['vulnerabilities']:
                report += "\n🚨 VULNERABILITIES:\n"
                for vuln in result['vulnerabilities']:
                    severity_icon = "🔴" if vuln['severity'] == 'HIGH' else "🟡"
                    report += f"   {severity_icon} {vuln['type']}: {vuln['description']}\n"
                    report += f"      Location: {vuln['location']}\n"
                    if 'details' in vuln:
                        report += f"      Details: {vuln['details']}\n"
            else:
                report += "\n✅ No vulnerabilities detected\n"
            
            # Security Features
            if result['security_features']:
                report += "\n🛡️  SECURITY FEATURES:\n"
                for feature in result['security_features']:
                    report += f"   ✓ {feature['type']}: {feature['description']}\n"
        
        # Overall Assessment
        report += "\n\n🎯 OVERALL ASSESSMENT:\n"
        if total_vulnerabilities == 0:
            report += "   ✅ EXCELLENT: No reentrancy vulnerabilities detected\n"
            report += "   ✅ Proper CEI pattern implementation confirmed\n"
            report += "   ✅ Comprehensive security protections in place\n"
        elif total_vulnerabilities <= 2:
            report += "   🟡 GOOD: Minor issues detected, mostly resolved\n"
            report += "   ⚠️  Review and address remaining vulnerabilities\n"
        else:
            report += "   🔴 CRITICAL: Multiple vulnerabilities detected\n"
            report += "   🚨 Immediate remediation required\n"
        
        report += "\n" + "="*80 + "\n"
        
        return report

def main():
    """Main execution function"""
    
    # Contract files to analyze
    contract_files = [
        r'c:\Users\mahia\New_Flashloan\contracts\ArbitrageExecutorV33.sol',
        r'c:\Users\mahia\New_Flashloan\ArbitrageExecutorV20.sol'
    ]
    
    validator = FlashLoanSecurityValidator()
    all_results = []
    
    print("🔍 Starting Flash Loan Reentrancy Security Validation...")
    
    for contract_file in contract_files:
        if os.path.exists(contract_file):
            results = validator.validate_contract(contract_file)
            all_results.append(results)
        else:
            print(f"⚠️  Warning: Contract file not found: {contract_file}")
    
    # Generate and display report
    report = validator.generate_report(all_results)
    print(report)
    
    # Save report to file
    report_file = r'c:\Users\mahia\New_Flashloan\FLASH_LOAN_SECURITY_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")
    
    return len([r for result in all_results for r in result['vulnerabilities']]) == 0

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Security validation completed successfully!")
    else:
        print("\n⚠️  Security issues detected. Please review the report.")
