#!/usr/bin/env python3
"""
Fix OpenZeppelin import paths for compatibility with newer versions
"""

import os
import re
from pathlib import Path

def fix_oz_imports():
    """Fix OpenZeppelin import paths"""
    contracts_dir = Path("contracts")
    
    # Mapping of old to new import paths
    import_fixes = {
        "@openzeppelin/contracts/security/Pausable.sol": "@openzeppelin/contracts/utils/Pausable.sol",
        "@openzeppelin/contracts/security/ReentrancyGuard.sol": "@openzeppelin/contracts/utils/ReentrancyGuard.sol"
    }
    
    files_fixed = 0
    total_replacements = 0
    
    for sol_file in contracts_dir.glob("*.sol"):
        if sol_file.is_file():
            content = sol_file.read_text(encoding='utf-8')
            original_content = content
            
            for old_import, new_import in import_fixes.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    total_replacements += 1
                    print(f"Fixed import in {sol_file.name}: {old_import} -> {new_import}")
            
            if content != original_content:
                sol_file.write_text(content, encoding='utf-8')
                files_fixed += 1
    
    print(f"\nFixed {total_replacements} imports in {files_fixed} files")

if __name__ == "__main__":
    print("🔧 FIXING OPENZEPPELIN IMPORT PATHS")
    print("=" * 40)
    fix_oz_imports()
    print("✅ Import paths fixed!")
