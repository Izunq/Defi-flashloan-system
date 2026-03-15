#!/usr/bin/env python3
"""
Critical Security Vulnerability Fixer
Addresses the most critical security issues found in the audit
"""

import os
import sys
import json
import re
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CriticalSecurityFixer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.fixes_applied = []
        self.errors_encountered = []
        
    def fix_tx_origin_usage(self):
        """Fix tx.origin usage in smart contracts"""
        logger.info("🔧 Fixing tx.origin usage...")
        
        contract_files = list(self.base_path.glob("**/*.sol"))
        for contract_file in contract_files:
            try:
                content = contract_file.read_text(encoding='utf-8')
                original_content = content
                
                # Replace tx.origin with msg.sender and add comment
                content = re.sub(
                    r'\btx\.origin\b',
                    'msg.sender /* SECURITY FIX: Changed from tx.origin to prevent phishing attacks */',
                    content
                )
                
                if content != original_content:
                    contract_file.write_text(content, encoding='utf-8')
                    self.fixes_applied.append(f"Fixed tx.origin usage in {contract_file}")
                    logger.info(f"✅ Fixed tx.origin in {contract_file.name}")
                    
            except Exception as e:
                error_msg = f"Error fixing tx.origin in {contract_file}: {e}"
                self.errors_encountered.append(error_msg)
                logger.error(error_msg)
    
    def add_reentrancy_guards(self):
        """Add reentrancy guards to smart contracts"""
        logger.info("🔧 Adding reentrancy guards...")
        
        contract_files = list(self.base_path.glob("**/*.sol"))
        for contract_file in contract_files:
            try:
                content = contract_file.read_text(encoding='utf-8')
                original_content = content
                
                # Add ReentrancyGuard import if not present
                if 'ReentrancyGuard' not in content and 'pragma solidity' in content:
                    # Find the import section
                    import_pattern = r'(pragma solidity[^;]+;)'
                    imports_to_add = '\nimport "@openzeppelin/contracts/security/ReentrancyGuard.sol";'
                    
                    content = re.sub(
                        import_pattern,
                        r'\1' + imports_to_add,
                        content,
                        count=1
                    )
                
                # Add nonReentrant modifier to external/public functions
                if 'external' in content or 'public' in content:
                    # Pattern to match function declarations
                    func_pattern = r'(\bfunction\s+\w+\s*\([^)]*\)\s+(?:external|public)(?:\s+\w+)*)(.*?)(\{)'
                    
                    def add_nonreentrant(match):
                        func_decl = match.group(1)
                        modifiers = match.group(2)
                        opening_brace = match.group(3)
                        
                        # Only add if nonReentrant not already present
                        if 'nonReentrant' not in modifiers:
                            if modifiers.strip():
                                modifiers += ' nonReentrant'
                            else:
                                modifiers = ' nonReentrant'
                        
                        return func_decl + modifiers + opening_brace
                    
                    content = re.sub(func_pattern, add_nonreentrant, content)
                
                # Add ReentrancyGuard inheritance if not present
                if ('contract ' in content and 
                    'ReentrancyGuard' not in content and 
                    'pragma solidity' in content):
                    
                    contract_pattern = r'(\bcontract\s+\w+)(\s+is\s+[^{]+)?(\s*\{)'
                    
                    def add_inheritance(match):
                        contract_name = match.group(1)
                        existing_inheritance = match.group(2) or ''
                        opening_brace = match.group(3)
                        
                        if existing_inheritance:
                            new_inheritance = existing_inheritance + ', ReentrancyGuard'
                        else:
                            new_inheritance = ' is ReentrancyGuard'
                        
                        return contract_name + new_inheritance + opening_brace
                    
                    content = re.sub(contract_pattern, add_inheritance, content, count=1)
                
                if content != original_content:
                    contract_file.write_text(content, encoding='utf-8')
                    self.fixes_applied.append(f"Added reentrancy protection to {contract_file}")
                    logger.info(f"✅ Added reentrancy guards to {contract_file.name}")
                    
            except Exception as e:
                error_msg = f"Error adding reentrancy guards to {contract_file}: {e}"
                self.errors_encountered.append(error_msg)
                logger.error(error_msg)
    
    def fix_external_calls(self):
        """Add proper error handling to external calls"""
        logger.info("🔧 Fixing external call security...")
        
        contract_files = list(self.base_path.glob("**/*.sol"))
        for contract_file in contract_files:
            try:
                content = contract_file.read_text(encoding='utf-8')
                original_content = content
                
                # Pattern to find .call() without proper error handling
                call_pattern = r'(\w+\.call\([^)]+\))(?!\s*;?\s*require\()'
                
                def add_error_check(match):
                    call_expr = match.group(1)
                    return f'(bool success, ) = {call_expr};\n        require(success, "External call failed");'
                
                content = re.sub(call_pattern, add_error_check, content)
                
                # Pattern to find .transfer() and .send() and suggest alternatives
                transfer_pattern = r'(\w+\.(transfer|send)\([^)]+\))'
                
                def fix_transfer(match):
                    transfer_expr = match.group(1)
                    return f'/* SECURITY NOTE: Consider using call instead of {match.group(2)} */ {transfer_expr}'
                
                content = re.sub(transfer_pattern, fix_transfer, content)
                
                if content != original_content:
                    contract_file.write_text(content, encoding='utf-8')
                    self.fixes_applied.append(f"Fixed external calls in {contract_file}")
                    logger.info(f"✅ Fixed external calls in {contract_file.name}")
                    
            except Exception as e:
                error_msg = f"Error fixing external calls in {contract_file}: {e}"
                self.errors_encountered.append(error_msg)
                logger.error(error_msg)
    
    def remove_hardcoded_secrets(self):
        """Remove hardcoded secrets and move to environment variables"""
        logger.info("🔧 Removing hardcoded secrets...")
        
        # Patterns for common secrets
        secret_patterns = [
            (r'(API_KEY\s*=\s*["\'])[^"\']+(["\'])', r'\1${API_KEY}\2'),
            (r'(PRIVATE_KEY\s*=\s*["\'])[^"\']+(["\'])', r'\1${PRIVATE_KEY}\2'),
            (r'(SECRET_KEY\s*=\s*["\'])[^"\']+(["\'])', r'\1${SECRET_KEY}\2'),
            (r'(PASSWORD\s*=\s*["\'])[^"\']+(["\'])', r'\1${PASSWORD}\2'),
            (r'(0x[a-fA-F0-9]{40})', '${CONTRACT_ADDRESS}'),  # Ethereum addresses
        ]
        
        # Check Python files
        python_files = list(self.base_path.glob("**/*.py"))
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                for pattern, replacement in secret_patterns:
                    content = re.sub(pattern, replacement, content)
                
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')
                    self.fixes_applied.append(f"Removed hardcoded secrets from {py_file}")
                    logger.info(f"✅ Cleaned secrets in {py_file.name}")
                    
            except Exception as e:
                error_msg = f"Error cleaning secrets in {py_file}: {e}"
                self.errors_encountered.append(error_msg)
                logger.error(error_msg)
        
        # Check JavaScript/TypeScript files
        js_files = list(self.base_path.glob("**/*.js")) + list(self.base_path.glob("**/*.ts"))
        for js_file in js_files:
            try:
                content = js_file.read_text(encoding='utf-8')
                original_content = content
                
                for pattern, replacement in secret_patterns:
                    content = re.sub(pattern, replacement, content)
                
                if content != original_content:
                    js_file.write_text(content, encoding='utf-8')
                    self.fixes_applied.append(f"Removed hardcoded secrets from {js_file}")
                    logger.info(f"✅ Cleaned secrets in {js_file.name}")
                    
            except Exception as e:
                error_msg = f"Error cleaning secrets in {js_file}: {e}"
                self.errors_encountered.append(error_msg)
                logger.error(error_msg)
    
    def add_access_control_modifiers(self):
        """Add access control modifiers to functions"""
        logger.info("🔧 Adding access control modifiers...")
        
        contract_files = list(self.base_path.glob("**/*.sol"))
        for contract_file in contract_files:
            try:
                content = contract_file.read_text(encoding='utf-8')
                original_content = content
                
                # Add Ownable import if not present
                if 'Ownable' not in content and 'pragma solidity' in content:
                    import_pattern = r'(pragma solidity[^;]+;)'
                    imports_to_add = '\nimport "@openzeppelin/contracts/access/Ownable.sol";'
                    
                    content = re.sub(
                        import_pattern,
                        r'\1' + imports_to_add,
                        content,
                        count=1
                    )
                
                # Add onlyOwner modifier to admin functions
                admin_function_patterns = [
                    r'(\bfunction\s+(withdraw|emergencyStop|pause|unpause|setFee|updateConfig)\s*\([^)]*\)\s+(?:external|public))(\s+[^{]*)?(\{)',
                ]
                
                for pattern in admin_function_patterns:
                    def add_only_owner(match):
                        func_decl = match.group(1)
                        modifiers = match.group(3) or ''
                        opening_brace = match.group(4)
                        
                        if 'onlyOwner' not in modifiers:
                            modifiers += ' onlyOwner'
                        
                        return func_decl + modifiers + opening_brace
                    
                    content = re.sub(pattern, add_only_owner, content)
                
                # Add Ownable inheritance if not present
                if ('contract ' in content and 
                    'Ownable' not in content and 
                    'pragma solidity' in content):
                    
                    contract_pattern = r'(\bcontract\s+\w+)(\s+is\s+[^{]+)?(\s*\{)'
                    
                    def add_ownable_inheritance(match):
                        contract_name = match.group(1)
                        existing_inheritance = match.group(2) or ''
                        opening_brace = match.group(3)
                        
                        if existing_inheritance:
                            new_inheritance = existing_inheritance + ', Ownable'
                        else:
                            new_inheritance = ' is Ownable'
                        
                        return contract_name + new_inheritance + opening_brace
                    
                    content = re.sub(contract_pattern, add_ownable_inheritance, content, count=1)
                
                if content != original_content:
                    contract_file.write_text(content, encoding='utf-8')
                    self.fixes_applied.append(f"Added access control to {contract_file}")
                    logger.info(f"✅ Added access control to {contract_file.name}")
                    
            except Exception as e:
                error_msg = f"Error adding access control to {contract_file}: {e}"
                self.errors_encountered.append(error_msg)
                logger.error(error_msg)
    
    def create_env_template(self):
        """Create environment variable template"""
        logger.info("🔧 Creating environment variable template...")
        
        env_content = """# Flash Loan Arbitrage System - Environment Variables
# Copy this file to .env and fill in your actual values

# API Keys
API_KEY=your_api_key_here
INFURA_PROJECT_ID=your_infura_project_id
ALCHEMY_API_KEY=your_alchemy_api_key

# Private Keys (NEVER commit actual private keys)
PRIVATE_KEY=your_private_key_here
DEPLOYER_PRIVATE_KEY=your_deployer_private_key

# Contract Addresses
CONTRACT_ADDRESS=${CONTRACT_ADDRESS}
USDC_ADDRESS=${CONTRACT_ADDRESS}
WETH_ADDRESS=${CONTRACT_ADDRESS}

# RPC URLs
MAINNET_RPC_URL=https://mainnet.infura.io/v3/${INFURA_PROJECT_ID}
POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/${INFURA_PROJECT_ID}

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/flashloan_db
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
LOG_LEVEL=INFO

# Trading Parameters
MAX_SLIPPAGE=0.01
GAS_PRICE_GWEI=20
MIN_PROFIT_THRESHOLD=0.001
"""
        
        env_file = self.base_path / '.env.template'
        env_file.write_text(env_content)
        self.fixes_applied.append("Created .env.template file")
        logger.info("✅ Created environment variable template")
    
    def generate_security_report(self):
        """Generate report of all fixes applied"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": len(self.fixes_applied),
            "errors_encountered": len(self.errors_encountered),
            "details": {
                "fixes": self.fixes_applied,
                "errors": self.errors_encountered
            },
            "next_steps": [
                "Review all automated fixes manually",
                "Test all modified contracts thoroughly",
                "Update contract tests for new security features",
                "Implement comprehensive input validation",
                "Add proper error handling to all functions",
                "Set up monitoring and alerting",
                "Conduct professional security audit"
            ]
        }
        
        report_file = self.base_path / f"critical_security_fixes_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Security fixes report saved: {report_file}")
        return report

def main():
    base_path = os.getcwd()
    logger.info(f"🔍 Starting critical security fixes in: {base_path}")
    
    fixer = CriticalSecurityFixer(base_path)
    
    # Apply critical fixes
    logger.info("=" * 60)
    logger.info("CRITICAL SECURITY VULNERABILITY FIXES")
    logger.info("=" * 60)
    
    try:
        fixer.fix_tx_origin_usage()
        fixer.add_reentrancy_guards()
        fixer.fix_external_calls()
        fixer.remove_hardcoded_secrets()
        fixer.add_access_control_modifiers()
        fixer.create_env_template()
        
        # Generate report
        report = fixer.generate_security_report()
        
        logger.info("=" * 60)
        logger.info("SECURITY FIXES SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Fixes Applied: {report['fixes_applied']}")
        logger.info(f"❌ Errors Encountered: {report['errors_encountered']}")
        
        if report['fixes_applied'] > 0:
            logger.info("\n🎯 IMPORTANT NEXT STEPS:")
            for step in report['next_steps']:
                logger.info(f"   • {step}")
        
        logger.info("\n⚠️  MANUAL REVIEW REQUIRED:")
        logger.info("   • Verify all automated fixes are correct")
        logger.info("   • Test modified contracts thoroughly")
        logger.info("   • Update configuration files with environment variables")
        logger.info("   • Run comprehensive test suite")
        
    except Exception as e:
        logger.error(f"Critical error during security fixes: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
