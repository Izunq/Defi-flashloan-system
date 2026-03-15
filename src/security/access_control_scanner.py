#!/usr/bin/env python3
"""
Access Control Security Scanner and Remediation Tool
Identifies and fixes critical access control vulnerabilities in smart contracts
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

class AccessControlScanner:
    def __init__(self, workspace_path):
        self.workspace = Path(workspace_path)
        self.vulnerabilities = []
        self.secure_functions = []
        self.fixed_functions = []
        
        # Critical function patterns that MUST have access control
        self.critical_patterns = [
            (r'function\s+(execute\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'CRITICAL'),
            (r'function\s+(propose\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'HIGH'),
            (r'function\s+(slash\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'HIGH'),
            (r'function\s+(emergency\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'CRITICAL'),
            (r'function\s+(withdraw\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'HIGH'),
            (r'function\s+(transfer\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'CRITICAL'),
            (r'function\s+(approve\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'MEDIUM'),
            (r'function\s+(set\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'MEDIUM'),
            (r'function\s+(update\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'MEDIUM'),
            (r'function\s+(grant\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'CRITICAL'),
            (r'function\s+(revoke\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'CRITICAL'),
            (r'function\s+(pause\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'HIGH'),
            (r'function\s+(unpause\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'HIGH'),
            (r'function\s+(shutdown\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'CRITICAL'),
            (r'function\s+(destroy\w*)\([^)]*\)\s+external(?!\s+view)(?!\s+pure)', 'CRITICAL'),
        ]
        
        # Access control patterns that indicate security
        self.security_patterns = [
            'onlyRole', 'onlyOwner', 'onlyAdmin', 'onlyExecutor', 'onlyEmergency',
            'onlyManager', 'onlyGuardian', 'onlyGovernance', 'onlyApproved',
            'onlyAuthorized', 'onlyStrategy', 'onlyOracle', 'onlyMudarib',
            'restricted', 'authorized', 'authenticated', 'whenNotPaused',
            'nonReentrant', 'onlyWhitelisted'
        ]

    def is_interface_declaration(self, content, line_index):
        """Check if a function is just an interface declaration"""
        # Look for interface keyword before the function
        lines_before = content.split('\n')[:line_index]
        recent_lines = lines_before[-10:] if len(lines_before) >= 10 else lines_before
        
        # Check if we're inside an interface block
        interface_depth = 0
        for line in recent_lines:
            if 'interface ' in line and '{' in line:
                interface_depth += 1
            elif 'contract ' in line and '{' in line:
                interface_depth = 0  # Reset if we hit a contract
            elif line.strip().endswith(';') and 'function ' in line:
                # This suggests we're in an interface (functions end with semicolons)
                return True
        
        # Also check the current line - if it ends with semicolon, likely interface
        current_line = content.split('\n')[line_index]
        if current_line.strip().endswith(';'):
            return True
            
        return False

    def scan_file(self, file_path):
        """Scan a single Solidity file for access control vulnerabilities"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                for pattern, risk_level in self.critical_patterns:
                    match = re.search(pattern, line)
                    if match:
                        func_name = match.group(1)
                        
                        # Skip if this is an interface declaration
                        if self.is_interface_declaration(content, i):
                            continue
                        
                        # Skip node_modules and interface files
                        if 'node_modules' in str(file_path) or 'interface' in str(file_path).lower():
                            continue
                            
                        # Collect the full function signature (multi-line)
                        function_block = line
                        j = i + 1
                        brace_count = line.count('{') - line.count('}')
                        
                        # Keep reading until we find the opening brace or modifier
                        while j < len(lines) and brace_count <= 0:
                            next_line = lines[j]
                            function_block += ' ' + next_line.strip()
                            brace_count += next_line.count('{') - next_line.count('}')
                            if '{' in next_line:
                                break
                            j += 1
                        
                        # Check if any security modifier is present
                        has_security = any(pattern in function_block for pattern in self.security_patterns)
                        
                        function_info = {
                            'name': func_name,
                            'file': str(file_path.relative_to(self.workspace)),
                            'line': i + 1,
                            'signature': function_block.strip(),
                            'risk': risk_level
                        }
                        
                        if has_security:
                            self.secure_functions.append(function_info)
                        else:
                            self.vulnerabilities.append(function_info)
                            
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

    def scan_workspace(self):
        """Scan entire workspace for vulnerabilities"""
        print("🔍 Scanning workspace for access control vulnerabilities...")
        
        # Scan all .sol files, excluding node_modules and interfaces
        sol_files = []
        for file_path in self.workspace.glob('**/*.sol'):
            if file_path.is_file():
                path_str = str(file_path)
                if 'node_modules' not in path_str and 'interfaces' not in path_str:
                    sol_files.append(file_path)
        
        for file_path in sol_files:
            self.scan_file(file_path)
        
        return len(self.vulnerabilities), len(self.secure_functions)

    def generate_report(self):
        """Generate comprehensive security report"""
        total_functions = len(self.vulnerabilities) + len(self.secure_functions)
        security_score = (len(self.secure_functions) / total_functions * 100) if total_functions > 0 else 0
        
        report = f"""
# 🚨 ACCESS CONTROL SECURITY AUDIT REPORT
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 SECURITY OVERVIEW
- **Security Score:** {security_score:.1f}%
- **Total Functions:** {total_functions}
- **✅ Secure Functions:** {len(self.secure_functions)}
- **🚨 Vulnerable Functions:** {len(self.vulnerabilities)}

## 🚨 CRITICAL VULNERABILITIES ({len(self.vulnerabilities)} found)
"""
        
        # Sort vulnerabilities by risk level
        risk_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_vulns = sorted(self.vulnerabilities, key=lambda x: risk_order.get(x['risk'], 4))
        
        for i, vuln in enumerate(sorted_vulns[:20]):  # Top 20
            report += f"""
### {i+1}. `{vuln['name']}()` - {vuln['risk']} Risk
**File:** `{vuln['file']}`:{vuln['line']}
**Issue:** Missing access control modifier
**Fix Required:** Add appropriate `onlyRole()` or similar modifier
"""
        
        if len(self.vulnerabilities) > 20:
            report += f"\n... and {len(self.vulnerabilities) - 20} more vulnerabilities\n"
        
        return report

    def generate_fixes(self):
        """Generate specific fixes for identified vulnerabilities"""
        fixes = []
        
        for vuln in self.vulnerabilities:
            func_name = vuln['name']
            
            # Determine appropriate access control based on function name
            if 'execute' in func_name.lower():
                modifier = 'onlyRole(STRATEGY_EXECUTOR_ROLE)'
            elif 'propose' in func_name.lower():
                modifier = 'onlyRole(STRATEGY_PROPOSER_ROLE)'
            elif 'emergency' in func_name.lower() or 'slash' in func_name.lower():
                modifier = 'onlyRole(EMERGENCY_ROLE)'
            elif any(word in func_name.lower() for word in ['grant', 'revoke', 'set', 'update']):
                modifier = 'onlyRole(DEFAULT_ADMIN_ROLE)'
            elif 'withdraw' in func_name.lower() or 'transfer' in func_name.lower():
                modifier = 'onlyRole(TREASURY_MANAGER_ROLE)'
            else:
                modifier = 'onlyRole(DEFAULT_ADMIN_ROLE)'
            
            fixes.append({
                'file': vuln['file'],
                'line': vuln['line'],
                'function': func_name,
                'current': vuln['signature'],
                'fix': f"Add {modifier} modifier",
                'risk': vuln['risk']
            })
        
        return fixes

def main():
    # Initialize scanner
    workspace_path = r"c:\Users\mahia\New_Flashloan"
    scanner = AccessControlScanner(workspace_path)
    
    # Perform scan
    vulns, secure = scanner.scan_workspace()
    
    # Generate and save report
    report = scanner.generate_report()
    
    # Save to file
    report_file = Path(workspace_path) / "CURRENT_ACCESS_CONTROL_AUDIT.md"
    report_file.write_text(report, encoding='utf-8')
    
    # Generate fixes
    fixes = scanner.generate_fixes()
    
    # Display results
    print(f"\n📊 SCAN COMPLETE:")
    print(f"✅ Secure Functions: {secure}")
    print(f"🚨 Vulnerable Functions: {vulns}")
    print(f"📈 Security Score: {secure/(secure+vulns)*100:.1f}%")
    
    if vulns > 0:
        print(f"\n🚨 TOP CRITICAL VULNERABILITIES:")
        for i, vuln in enumerate(scanner.vulnerabilities[:10]):
            print(f"{i+1:2d}. {vuln['name']} - {vuln['file']}:{vuln['line']} ({vuln['risk']})")
        
        print(f"\n📄 Full report saved to: CURRENT_ACCESS_CONTROL_AUDIT.md")
        
        # Show immediate fixes needed
        critical_fixes = [f for f in fixes if f['risk'] == 'CRITICAL']
        if critical_fixes:
            print(f"\n🛠️ IMMEDIATE FIXES NEEDED ({len(critical_fixes)} CRITICAL):")
            for fix in critical_fixes[:5]:
                print(f"- {fix['function']} in {fix['file']} - {fix['fix']}")
    else:
        print("\n🎉 NO VULNERABILITIES FOUND! System is secure.")
    
    return scanner

if __name__ == "__main__":
    main()
