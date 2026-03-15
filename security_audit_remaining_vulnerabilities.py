#!/usr/bin/env python3
"""
Security Audit - Remaining Vulnerabilities Analysis
Target: Identify and fix remaining 25 vulnerable functions to reach 80%+ security
Current: 74.2% security score (72 secure, 25 vulnerable)
Goal: 80%+ security score (78+ secure functions)
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

class SecurityAuditAnalyzer:
    def __init__(self, workspace_path):
        self.workspace_path = Path(workspace_path)
        self.vulnerabilities = []
        self.secure_functions = []
        self.critical_patterns = [
            # Missing access control patterns
            r'function\s+(\w+)\([^)]*\)\s+external(?!\s+.*onlyRole|.*onlyOwner|.*onlyAdmin)',
            r'function\s+(\w+)\([^)]*\)\s+public(?!\s+.*onlyRole|.*onlyOwner|.*onlyAdmin)',
            
            # Unsafe external calls
            r'\.call\s*\{|\.delegatecall\s*\{|\.staticcall\s*\{',
            
            # Missing reentrancy protection
            r'function\s+(\w+).*external.*(?!.*nonReentrant)',
            
            # Missing input validation
            r'require\s*\(\s*\w+\s*[!=><]+\s*\w+\s*\)',
            
            # Oracle manipulation risks
            r'oracle\.|price.*feed|getPrice|latestRoundData'
        ]
        
    def analyze_remaining_vulnerabilities(self):
        """Analyze remaining 25 vulnerable functions"""
        print("🔍 ANALYZING REMAINING VULNERABILITIES...")
        print("=" * 60)
        
        # Search for Solidity files
        sol_files = list(self.workspace_path.glob("**/*.sol"))
        
        vulnerable_functions = []
        
        for sol_file in sol_files:
            try:
                with open(sol_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    vulnerabilities = self._analyze_file_vulnerabilities(sol_file, content)
                    vulnerable_functions.extend(vulnerabilities)
            except Exception as e:
                print(f"❌ Error analyzing {sol_file}: {e}")
        
        # Focus on most critical remaining vulnerabilities
        critical_vulnerabilities = self._prioritize_vulnerabilities(vulnerable_functions)
        
        # Generate remediation plan
        self._generate_remediation_plan(critical_vulnerabilities)
        
        return critical_vulnerabilities
    
    def _analyze_file_vulnerabilities(self, file_path, content):
        """Analyze individual file for vulnerabilities"""
        vulnerabilities = []
        lines = content.split('\n')
        
        # Check for missing access control on external/public functions
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Look for external/public functions without access control
            if re.search(r'function\s+\w+.*external', line, re.IGNORECASE):
                if not self._has_access_control(line, lines, i):
                    func_name = self._extract_function_name(line)
                    vulnerability = {
                        'type': 'Missing Access Control',
                        'severity': 'HIGH',
                        'file': str(file_path),
                        'line': line_num,
                        'function': func_name,
                        'code': line.strip(),
                        'risk': 'Unauthorized access to critical functions'
                    }
                    vulnerabilities.append(vulnerability)
            
            # Check for unsafe external calls
            if re.search(r'\.call\s*\{|\.delegatecall\s*\{', line):
                vulnerability = {
                    'type': 'Unsafe External Call',
                    'severity': 'HIGH',
                    'file': str(file_path),
                    'line': line_num,
                    'function': self._find_containing_function(lines, i),
                    'code': line.strip(),
                    'risk': 'Potential reentrancy or call injection'
                }
                vulnerabilities.append(vulnerability)
            
            # Check for missing input validation
            if 'require(' in line and not re.search(r'require\s*\([^)]*msg\.sender|require\s*\([^)]*hasRole', line):
                if self._is_critical_validation_missing(line):
                    vulnerability = {
                        'type': 'Weak Input Validation',
                        'severity': 'MEDIUM',
                        'file': str(file_path),
                        'line': line_num,
                        'function': self._find_containing_function(lines, i),
                        'code': line.strip(),
                        'risk': 'Insufficient parameter validation'
                    }
                    vulnerabilities.append(vulnerability)
        
        return vulnerabilities
    
    def _has_access_control(self, line, lines, line_index):
        """Check if function has proper access control"""
        # Check current line and next few lines for access control modifiers
        for i in range(max(0, line_index-2), min(len(lines), line_index+3)):
            check_line = lines[i].lower()
            if any(modifier in check_line for modifier in [
                'onlyrole', 'onlyowner', 'onlyadmin', 'requirerole', 'whennotpaused'
            ]):
                return True
        return False
    
    def _extract_function_name(self, line):
        """Extract function name from function declaration"""
        match = re.search(r'function\s+(\w+)', line)
        return match.group(1) if match else 'unknown'
    
    def _find_containing_function(self, lines, line_index):
        """Find the function that contains the given line"""
        for i in range(line_index, -1, -1):
            if re.search(r'function\s+(\w+)', lines[i]):
                return self._extract_function_name(lines[i])
        return 'unknown'
    
    def _is_critical_validation_missing(self, line):
        """Check if critical validation is missing"""
        # Look for basic validation patterns that might be insufficient
        if 'require(' in line and not any(pattern in line.lower() for pattern in [
            'length', 'balance', 'amount', 'value', 'address(0)', 'zero'
        ]):
            return True
        return False
    
    def _prioritize_vulnerabilities(self, vulnerabilities):
        """Prioritize vulnerabilities by severity and impact"""
        priority_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        
        # Sort by severity
        sorted_vulns = sorted(vulnerabilities, 
                            key=lambda x: priority_order.get(x['severity'], 0), 
                            reverse=True)
        
        # Group by type
        grouped = {}
        for vuln in sorted_vulns:
            vuln_type = vuln['type']
            if vuln_type not in grouped:
                grouped[vuln_type] = []
            grouped[vuln_type].append(vuln)
        
        return grouped
    
    def _generate_remediation_plan(self, vulnerabilities):
        """Generate specific remediation plan for remaining vulnerabilities"""
        
        print("\n🎯 REMAINING VULNERABILITIES TO REACH 80%+ SECURITY")
        print("=" * 60)
        print(f"📊 Current: 74.2% (72 secure, 25 vulnerable)")
        print(f"🎯 Target: 80%+ (Need to fix 6+ critical functions)")
        print()
        
        remediation_plan = {
            'current_score': 74.2,
            'target_score': 80.0,
            'functions_to_fix': 6,
            'priority_fixes': [],
            'timestamp': datetime.now().isoformat()
        }
        
        fix_count = 0
        
        for vuln_type, vulns in vulnerabilities.items():
            print(f"\n🚨 {vuln_type.upper()} ({len(vulns)} found)")
            print("-" * 40)
            
            for i, vuln in enumerate(vulns[:3]):  # Show top 3 per category
                fix_count += 1
                if fix_count <= 6:  # Focus on top 6 fixes needed
                    print(f"{fix_count}. 📄 {os.path.basename(vuln['file'])}:{vuln['line']}")
                    print(f"   Function: {vuln['function']}")
                    print(f"   Severity: {vuln['severity']}")
                    print(f"   Risk: {vuln['risk']}")
                    print(f"   Code: {vuln['code'][:80]}...")
                    print()
                    
                    fix_suggestion = self._generate_fix_suggestion(vuln)
                    print(f"   ✅ Fix: {fix_suggestion}")
                    print()
                    
                    remediation_plan['priority_fixes'].append({
                        'file': vuln['file'],
                        'function': vuln['function'],
                        'fix': fix_suggestion,
                        'priority': fix_count
                    })
        
        # Save remediation plan
        with open(self.workspace_path / 'security_remediation_plan.json', 'w') as f:
            json.dump(remediation_plan, f, indent=2)
        
        print("\n🛠️ QUICK FIXES TO REACH 80%+ SECURITY")
        print("=" * 60)
        
        quick_fixes = [
            "1. Add `onlyRole(ADMIN_ROLE)` to administrative functions",
            "2. Add `nonReentrant` modifier to external state-changing functions", 
            "3. Add `whenNotPaused` to critical financial operations",
            "4. Implement comprehensive input validation with bounds checking",
            "5. Add access control to oracle price update functions",
            "6. Secure cross-chain bridge execution functions"
        ]
        
        for fix in quick_fixes:
            print(f"✅ {fix}")
        
        print(f"\n📈 Expected Result: 80%+ security score (production ready)")
        print(f"⏱️ Estimated Time: 2-4 hours for critical fixes")
        
        return remediation_plan
    
    def _generate_fix_suggestion(self, vulnerability):
        """Generate specific fix suggestion for vulnerability"""
        vuln_type = vulnerability['type']
        function_name = vulnerability['function']
        
        if vuln_type == 'Missing Access Control':
            if 'emergency' in function_name.lower():
                return f"Add `onlyRole(EMERGENCY_ROLE)` modifier"
            elif 'execute' in function_name.lower():
                return f"Add `onlyRole(EXECUTOR_ROLE)` modifier"
            elif 'admin' in function_name.lower():
                return f"Add `onlyRole(ADMIN_ROLE)` modifier"
            else:
                return f"Add appropriate `onlyRole()` modifier"
        
        elif vuln_type == 'Unsafe External Call':
            return "Use reentrancy guard and validate call target"
        
        elif vuln_type == 'Weak Input Validation':
            return "Add comprehensive bounds checking and validation"
        
        else:
            return "Implement security best practices"

def main():
    """Main execution function"""
    workspace_path = Path(r"C:\Users\mahia\New_Flashloan")
    
    print("🛡️ SECURITY AUDIT - REMAINING VULNERABILITIES ANALYSIS")
    print("=" * 60)
    print(f"📂 Workspace: {workspace_path}")
    print(f"🎯 Goal: Reach 80%+ security score for production readiness")
    print()
    
    # Create analyzer
    analyzer = SecurityAuditAnalyzer(workspace_path)
    
    # Analyze remaining vulnerabilities
    vulnerabilities = analyzer.analyze_remaining_vulnerabilities()
    
    print("\n🚀 NEXT STEPS:")
    print("1. Review the priority fixes above")
    print("2. Implement the suggested access control fixes")
    print("3. Re-run security audit to verify improvements")
    print("4. Deploy to testnet for final validation")
    
    return vulnerabilities

if __name__ == "__main__":
    main()
