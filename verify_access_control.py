#!/usr/bin/env python3
"""
Access Control Security Verification Script
Check current access control implementation across smart contracts
"""

import os
import re
import json
from typing import Dict, List, Tuple

class AccessControlAuditor:
    def __init__(self, contracts_dir: str):
        self.contracts_dir = contracts_dir
        self.vulnerabilities = []
        self.secure_functions = []
        
    def scan_contracts(self) -> Dict:
        """Scan all Solidity contracts for access control issues"""
        
        results = {
            "total_files": 0,
            "vulnerable_functions": [],
            "secure_functions": [],
            "missing_modifiers": [],
            "recommendations": []
        }
        
        # Find all .sol files
        for root, dirs, files in os.walk(self.contracts_dir):
            for file in files:
                if file.endswith('.sol'):
                    file_path = os.path.join(root, file)
                    results["total_files"] += 1
                    
                    file_results = self._scan_file(file_path)
                    
                    results["vulnerable_functions"].extend(file_results["vulnerable"])
                    results["secure_functions"].extend(file_results["secure"])
                    results["missing_modifiers"].extend(file_results["missing_modifiers"])
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)
        
        return results
    
    def _scan_file(self, file_path: str) -> Dict:
        """Scan a single Solidity file for access control patterns"""
        
        results = {
            "vulnerable": [],
            "secure": [],
            "missing_modifiers": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract function definitions
            functions = self._extract_functions(content, file_path)
            
            for func in functions:
                # Check if function has proper access control
                if self._is_vulnerable_function(func):
                    results["vulnerable"].append(func)
                elif self._has_access_control(func):
                    results["secure"].append(func)
                else:
                    results["missing_modifiers"].append(func)
                    
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
        
        return results
    
    def _extract_functions(self, content: str, file_path: str) -> List[Dict]:
        """Extract function definitions from Solidity code"""
        
        functions = []
        
        # Pattern to match function definitions
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*(external|public|internal|private)?\s*([^{]*)\{'
        
        matches = re.finditer(function_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            func_name = match.group(1)
            visibility = match.group(2) or "public"  # default to public if not specified
            modifiers = match.group(3) or ""
            
            # Get line number
            line_num = content[:match.start()].count('\n') + 1
            
            functions.append({
                "name": func_name,
                "visibility": visibility,
                "modifiers": modifiers.strip(),
                "file": file_path,
                "line": line_num,
                "full_signature": match.group(0)
            })
        
        return functions
    
    def _is_vulnerable_function(self, func: Dict) -> bool:
        """Check if a function is vulnerable (has external/public visibility but no access control)"""
        
        # Critical function patterns that should always have access control
        critical_patterns = [
            'propose', 'execute', 'withdraw', 'transfer', 'approve', 'mint', 'burn',
            'pause', 'unpause', 'emergency', 'admin', 'owner', 'upgrade', 'migrate',
            'slash', 'reward', 'distribute', 'update', 'set', 'grant', 'revoke'
        ]
        
        # Access control modifiers
        access_modifiers = [
            'onlyOwner', 'onlyAdmin', 'onlyRole', 'onlyAuthorized', 'onlyManager',
            'onlyEmergency', 'onlySecurity', 'onlyExecutor', 'onlyProposer'
        ]
        
        # Check if function name contains critical patterns
        func_name_lower = func["name"].lower()
        is_critical = any(pattern in func_name_lower for pattern in critical_patterns)
        
        # Check if function is external or public
        is_public_facing = func["visibility"] in ["external", "public"]
        
        # Check if function has access control modifiers
        has_access_control = any(modifier in func["modifiers"] for modifier in access_modifiers)
        
        # Function is vulnerable if it's critical, public-facing, but lacks access control
        return is_critical and is_public_facing and not has_access_control
    
    def _has_access_control(self, func: Dict) -> bool:
        """Check if function has proper access control"""
        
        access_modifiers = [
            'onlyOwner', 'onlyAdmin', 'onlyRole', 'onlyAuthorized', 'onlyManager',
            'onlyEmergency', 'onlySecurity', 'onlyExecutor', 'onlyProposer',
            'whenNotPaused', 'nonReentrant'
        ]
        
        return any(modifier in func["modifiers"] for modifier in access_modifiers)
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate security recommendations based on scan results"""
        
        recommendations = []
        
        if results["vulnerable_functions"]:
            recommendations.append(
                f"🚨 CRITICAL: {len(results['vulnerable_functions'])} vulnerable functions detected! "
                "Add proper access control modifiers immediately."
            )
        
        if results["missing_modifiers"]:
            recommendations.append(
                f"⚠️  WARNING: {len(results['missing_modifiers'])} functions lack access control modifiers. "
                "Review and add appropriate restrictions."
            )
        
        if len(results["secure_functions"]) > 0:
            recommendations.append(
                f"✅ GOOD: {len(results['secure_functions'])} functions have proper access control."
            )
        
        # Specific recommendations
        recommendations.extend([
            "1. Implement role-based access control using OpenZeppelin's AccessControl",
            "2. Add reentrancy protection using OpenZeppelin's ReentrancyGuard",
            "3. Implement pause mechanisms for emergency situations",
            "4. Use time-locks for critical administrative functions",
            "5. Regularly audit access control patterns",
            "6. Test access control enforcement in unit tests"
        ])
        
        return recommendations
    
    def generate_report(self, output_file: str = "access_control_audit_report.json"):
        """Generate a comprehensive audit report"""
        
        print("🔍 Starting access control security scan...")
        
        results = self.scan_contracts()
        
        # Create detailed report
        report = {
            "scan_timestamp": "2025-06-14T13:19:25Z",
            "summary": {
                "total_files_scanned": results["total_files"],
                "vulnerable_functions": len(results["vulnerable_functions"]),
                "secure_functions": len(results["secure_functions"]),
                "functions_missing_modifiers": len(results["missing_modifiers"]),
                "security_score": self._calculate_security_score(results)
            },
            "vulnerabilities": results["vulnerable_functions"],
            "secure_functions": results["secure_functions"][:10],  # Top 10 for brevity
            "missing_modifiers": results["missing_modifiers"][:20],  # Top 20 for brevity
            "recommendations": results["recommendations"]
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _calculate_security_score(self, results: Dict) -> int:
        """Calculate security score out of 100"""
        
        total_functions = (
            len(results["vulnerable_functions"]) + 
            len(results["secure_functions"]) + 
            len(results["missing_modifiers"])
        )
        
        if total_functions == 0:
            return 100
        
        secure_functions = len(results["secure_functions"])
        vulnerable_functions = len(results["vulnerable_functions"])
        
        # Score calculation: 
        # - Secure functions: +1 point each
        # - Vulnerable functions: -3 points each
        # - Missing modifiers: -1 point each
        
        score = (
            (secure_functions * 100) - 
            (vulnerable_functions * 300) - 
            (len(results["missing_modifiers"]) * 50)
        ) / total_functions
        
        return max(0, min(100, int(score)))
    
    def _print_summary(self, report: Dict):
        """Print audit summary to console"""
        
        print("\n" + "="*60)
        print("🛡️  ACCESS CONTROL SECURITY AUDIT REPORT")
        print("="*60)
        
        summary = report["summary"]
        
        print(f"📊 SCAN SUMMARY:")
        print(f"   Files Scanned: {summary['total_files_scanned']}")
        print(f"   Security Score: {summary['security_score']}/100")
        
        if summary['vulnerable_functions'] > 0:
            print(f"\n🚨 CRITICAL ISSUES:")
            print(f"   Vulnerable Functions: {summary['vulnerable_functions']}")
        
        if summary['functions_missing_modifiers'] > 0:
            print(f"\n⚠️  WARNINGS:")
            print(f"   Functions Missing Modifiers: {summary['functions_missing_modifiers']}")
        
        if summary['secure_functions'] > 0:
            print(f"\n✅ SECURE:")
            print(f"   Functions with Access Control: {summary['secure_functions']}")
        
        print(f"\n📝 TOP VULNERABILITIES:")
        for i, vuln in enumerate(report["vulnerabilities"][:5], 1):
            print(f"   {i}. {vuln['name']} in {vuln['file']}:{vuln['line']}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report["recommendations"][:5], 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "="*60)
        print(f"📄 Full report saved to: access_control_audit_report.json")
        print("="*60)

def main():
    """Main execution function"""
    
    # Define contracts directory
    contracts_dir = "."  # Current directory and subdirectories
    
    # Initialize auditor
    auditor = AccessControlAuditor(contracts_dir)
    
    # Generate report
    report = auditor.generate_report()
    
    # Return exit code based on vulnerabilities
    if report["summary"]["vulnerable_functions"] > 0:
        print("\n🚨 SECURITY ALERT: Critical vulnerabilities detected!")
        return 1
    elif report["summary"]["functions_missing_modifiers"] > 0:
        print("\n⚠️ WARNING: Access control improvements needed.")
        return 2
    else:
        print("\n✅ SUCCESS: No critical access control issues detected.")
        return 0

if __name__ == "__main__":
    exit(main())
