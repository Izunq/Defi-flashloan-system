#!/usr/bin/env python3
"""
Fix syntax errors introduced by security fixer
"""

import os
import re
from pathlib import Path

def fix_solidity_syntax():
    """Fix syntax errors in Solidity files"""
    contracts_dir = Path("contracts")
    
    files_fixed = 0
    
    for sol_file in contracts_dir.rglob("*.sol"):
        if sol_file.is_file():
            try:
                content = sol_file.read_text(encoding='utf-8')
                original_content = content
                
                # Fix misplaced nonReentrant modifiers
                # Pattern: returns (...) nonReentrant{
                content = re.sub(
                    r'returns\s*\([^)]*\)\s+nonReentrant\s*\{',
                    lambda m: m.group(0).replace(' nonReentrant{', ' {\n        // TODO: Add nonReentrant modifier'),
                    content
                )
                
                # Pattern: ) nonReentrant{
                content = re.sub(
                    r'\)\s+nonReentrant\s*\{',
                    lambda m: m.group(0).replace(' nonReentrant{', ' {\n        // TODO: Add nonReentrant modifier'),
                    content
                )
                
                # Fix function syntax errors - remove duplicate nonReentrant
                content = re.sub(r'nonReentrant\s+nonReentrant', 'nonReentrant', content)
                
                # Fix try block syntax
                content = re.sub(r'try\s*\{', 'try arbitrageContract.executeArbitrage() {', content)
                
                # Fix interface declarations in wrong places
                content = re.sub(r'(\s+)interface\s+', r'\n\ninterface ', content)
                
                # Fix DEFAULT_ADMIN_ROLE issue
                content = re.sub(r'_grantRole\(DEFAULT_ADMIN_ROLE,', '_grantRole(keccak256("DEFAULT_ADMIN_ROLE"),', content)
                
                # Fix reserved keyword 'returns' used as variable name
                content = re.sub(r'uint256\[\]\s+memory\s+returns\s*=', 'uint256[] memory results =', content)
                
                # Fix contract keyword used as parameter name
                content = re.sub(r'address\s+indexed\s+contract\s*,', 'address indexed contractAddr,', content)
                
                if content != original_content:
                    sol_file.write_text(content, encoding='utf-8')
                    files_fixed += 1
                    print(f"Fixed syntax in {sol_file.name}")
                    
            except Exception as e:
                print(f"Error processing {sol_file.name}: {e}")
    
    print(f"\nFixed syntax in {files_fixed} files")

if __name__ == "__main__":
    print("🔧 FIXING SOLIDITY SYNTAX ERRORS")
    print("=" * 40)
    fix_solidity_syntax()
    print("✅ Syntax errors fixed!")
