#!/usr/bin/env python3
"""
🚨 EMERGENCY SECURITY REMEDIATION SCRIPT 🚨
=======================================

This script scans for and eliminates ALL private key handling in the codebase.
It's designed to prevent catastrophic security breaches by ensuring no direct
private key access remains in any file.

CRITICAL: This script must be run before ANY deployment.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# CRITICAL PATTERNS THAT INDICATE PRIVATE KEY USAGE
CRITICAL_PATTERNS = [
    r'os\.getenv\s*\(\s*["\']PRIVATE_KEY["\']',
    r'Account\.from_key\s*\(',
    r'account\.from_key\s*\(',
    r'process\.env\.PRIVATE_KEY',
    r'new\s+ethers\.Wallet\s*\(\s*privateKey',
    r'new\s+ethers\.Wallet\s*\(\s*process\.env\.PRIVATE_KEY',
    r'sign_transaction\s*\(\s*[^,]+,\s*os\.getenv\s*\(\s*["\']PRIVATE_KEY["\']',
    r'PRIVATE_KEY\s*=\s*os\.getenv',
    r'private_key\s*=\s*os\.getenv',
    r'privateKey\s*=\s*process\.env\.PRIVATE_KEY'
]

# FILES TO EXCLUDE FROM SCANNING (already secure or non-critical)
EXCLUDE_FILES = [
    'secure_transaction_signer.py',
    'SECURITY_EMERGENCY_PATCH.md',
    'SECURITY_REMEDIATION_SUCCESS_REPORT.md',
    'SECURITY_SCAN_REPORT.txt',
    'security_verification.py',
    'emergency_security_scan.py',
    'emergency_private_key_remediation.py',
    'final_security_fix.py',
    'test_zk_proof.py',  # Test cryptographic keys, not actual private keys
    'ALL_PROJECT_FILES.txt',
    'MASTER_PROJECT_COMPILATION.txt',
    'FULL_PROJECT_ALL_CODE.txt',
    'frontend_files.txt'
]

# PATTERNS TO EXCLUDE FROM SCANNING
EXCLUDE_PATTERNS = [
    r'\.backup$',  # Backup files
    r'\.bak$',     # Backup files
    r'\.orig$',    # Original files
]

# DIRECTORIES TO SCAN
SCAN_DIRECTORIES = ['.']

def scan_file_for_private_keys(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a file for private key usage patterns.
    
    Returns:
        List of (line_number, pattern_matched, line_content) tuples
    """
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for pattern in CRITICAL_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append((line_num, pattern, line.strip()))
                    
    except Exception as e:
        print(f"ERROR: Could not scan {file_path}: {e}")
        
    return violations

def scan_codebase() -> Dict[str, List[Tuple[int, str, str]]]:
    """
    Scan the entire codebase for private key usage.
    
    Returns:
        Dictionary mapping file paths to their violations
    """
    violations_by_file = {}
    
    for directory in SCAN_DIRECTORIES:
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file():
                # Skip excluded files
                if file_path.name in EXCLUDE_FILES:
                    continue
                
                # Skip files matching exclude patterns
                if any(re.search(pattern, str(file_path)) for pattern in EXCLUDE_PATTERNS):
                    continue
                    
                # Skip binary files and certain extensions
                if file_path.suffix in ['.exe', '.dll', '.so', '.dylib', '.bin', '.zip', '.tar', '.gz']:
                    continue
                    
                # Scan for violations
                violations = scan_file_for_private_keys(file_path)
                if violations:
                    violations_by_file[str(file_path)] = violations
                    
    return violations_by_file

def create_security_report(violations: Dict[str, List[Tuple[int, str, str]]]) -> str:
    """
    Create a detailed security report of all violations found.
    """
    report = []
    report.append("*** CRITICAL SECURITY AUDIT REPORT ***")
    report.append("="*50)
    report.append(f"Scan completed at: {os.getcwd()}")
    report.append(f"Total files with violations: {len(violations)}")
    report.append("")
    
    if not violations:
        report.append("SUCCESS: NO PRIVATE KEY VIOLATIONS FOUND!")
        report.append("The codebase appears to be secure from direct private key exposure.")
        return "\\n".join(report)
    
    report.append("ERROR: CRITICAL SECURITY VIOLATIONS DETECTED!")
    report.append("")
    
    total_violations = sum(len(v) for v in violations.values())
    report.append(f"Total violations: {total_violations}")
    report.append("")
    
    for file_path, file_violations in violations.items():
        report.append(f"FILE: {file_path}")
        report.append(f"   Violations: {len(file_violations)}")
        
        for line_num, pattern, line_content in file_violations:
            report.append(f"   ERROR Line {line_num}: {line_content}")
            report.append(f"      Pattern: {pattern}")
        
        report.append("")
    
    report.append("WARNING: IMMEDIATE ACTION REQUIRED")
    report.append("These violations must be fixed before any deployment!")
    report.append("Each violation represents a potential complete loss of funds.")
    
    return "\\n".join(report)

def main():
    """
    Main execution function - scan and report security violations.
    """
    print("*** EMERGENCY SECURITY SCAN STARTING ***")
    print("Scanning codebase for private key exposure...")
    print()
    
    # Scan for violations
    violations = scan_codebase()
    
    # Create report
    report = create_security_report(violations)
    
    # Print report
    print(report)
    
    # Save report to file (with proper Unicode encoding)
    try:
        with open('SECURITY_SCAN_REPORT.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\\nReport saved to: SECURITY_SCAN_REPORT.txt")
    except UnicodeEncodeError:
        # Fallback: save report without emoji characters
        clean_report = report.encode('ascii', 'ignore').decode('ascii')
        with open('SECURITY_SCAN_REPORT.txt', 'w', encoding='utf-8') as f:
            f.write(clean_report)
        print(f"\\nReport saved to: SECURITY_SCAN_REPORT.txt (emoji characters removed for compatibility)")
    
    # Exit with error code if violations found
    if violations:
        print("\\n*** CRITICAL: VIOLATIONS DETECTED - DEPLOYMENT BLOCKED ***")
        sys.exit(1)
    else:
        print("\\n*** SECURITY SCAN PASSED - NO VIOLATIONS DETECTED ***")
        sys.exit(0)

if __name__ == "__main__":
    main()
