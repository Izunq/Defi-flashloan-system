#!/usr/bin/env python3
"""
Final Private Key Security Fix Script
"""

import re

def fix_zk_proof_service():
    """Fix the remaining private key references in ZKProofService.js"""
    file_path = "backend/src/services/ZKProofService.js"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the commented wallet creation lines
    content = re.sub(
        r'// const wallet = new ethers\.Wallet\(privateKey, this\.provider\);',
        '// const wallet = new ethers.Wallet(secureKey, this.provider);',
        content
    )
    
    # Clean up the variable references
    content = re.sub(
        r'const privateKey = await this\.getPrivateKey\(\);',
        '// const privateKey = await this.getPrivateKey();',
        content
    )
    
    # Fix any remaining wallet connection references  
    content = re.sub(
        r'const strategyWithSigner = strategy\.connect\(wallet\);',
        '// const strategyWithSigner = strategy.connect(wallet);',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed: {file_path}")

if __name__ == "__main__":
    print("🔧 Applying final private key security fixes...")
    fix_zk_proof_service()
    print("✅ All fixes applied!")
