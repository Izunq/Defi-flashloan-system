#!/usr/bin/env python3
"""
Comprehensive Security and Bug Audit Script
==========================================

This script performs a complete security and bug audit of the entire flashloan system.
It includes automated vulnerability scanning, code analysis, and security verification.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SecurityAudit')

@dataclass
class SecurityIssue:
    """Data structure for security issues."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str  # Access Control, Reentrancy, Input Validation, etc.
    file_path: str
    line_number: int
    description: str
    recommendation: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None

@dataclass
class AuditResult:
    """Audit result data structure."""
    total_files_scanned: int
    total_issues_found: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    info_issues: int
    security_score: float
    scan_duration: float
    timestamp: str

class ComprehensiveSecurityAuditor:
    """Main security auditor class."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[SecurityIssue] = []
        self.files_scanned = 0
        self.start_time = time.time()
        
        # Security patterns to detect vulnerabilities
        self.vulnerability_patterns = {
            'sql_injection': [
                r'exec\s*\(',
                r'eval\s*\(',
                r'query\s*\+',
                r'SELECT.*\+',
                r'INSERT.*\+',
                r'UPDATE.*\+',
                r'DELETE.*\+'
            ],
            'xss': [
                r'innerHTML\s*=',
                r'document\.write\s*\(',
                r'eval\s*\(',
                r'setTimeout\s*\([^,]*["\']',
                r'setInterval\s*\([^,]*["\']'
            ],
            'command_injection': [
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(',
                r'shell=True',
                r'exec\s*\(',
                r'eval\s*\('
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
                r'private_key\s*=\s*["\'][^"\']+["\']'
            ],
            'weak_crypto': [
                r'md5\s*\(',
                r'sha1\s*\(',
                r'des\s*\(',
                r'rc4\s*\(',
                r'random\.random\s*\('
            ],
            'solidity_vulnerabilities': [
                r'tx\.origin',
                r'block\.timestamp',
                r'block\.number',
                r'selfdestruct\s*\(',
                r'suicide\s*\(',
                r'call\.value\s*\(',
                r'send\s*\(',
                r'transfer\s*\('
            ],
            'access_control': [
                r'onlyOwner',
                r'require\s*\(\s*msg\.sender',
                r'modifier\s+only',
                r'_checkRole\s*\(',
                r'hasRole\s*\('
            ],
            'reentrancy': [
                r'external.*payable',
                r'call\.value',
                r'send\s*\(',
                r'transfer\s*\(',
                r'nonReentrant'
            ]
        }
        
        # File extensions to scan
        self.scan_extensions = {'.py', '.js', '.ts', '.sol', '.json', '.yml', '.yaml'}
        
    async def run_comprehensive_audit(self) -> AuditResult:
        """Run the complete security audit."""
        logger.info("🔍 Starting Comprehensive Security Audit")
        logger.info("=" * 60)
        
        # Phase 1: Static Code Analysis
        await self._run_static_analysis()
        
        # Phase 2: Dependency Vulnerability Scan
        await self._scan_dependencies()
        
        # Phase 3: Configuration Security Check
        await self._check_configurations()
        
        # Phase 4: Smart Contract Security Analysis
        await self._analyze_smart_contracts()
        
        # Phase 5: API Security Analysis
        await self._analyze_api_security()
        
        # Phase 6: Infrastructure Security Check
        await self._check_infrastructure_security()
        
        # Generate audit report
        audit_result = await self._generate_audit_report()
        
        logger.info("✅ Security audit completed")
        return audit_result
        
    async def _run_static_analysis(self):
        """Run static code analysis on all source files."""
        logger.info("🔎 Phase 1: Static Code Analysis")
        
        source_files = []
        for ext in self.scan_extensions:
            source_files.extend(list(self.project_root.rglob(f"*{ext}")))
        
        for file_path in source_files:
            if self._should_skip_file(file_path):
                continue
                
            await self._scan_file_for_vulnerabilities(file_path)
            self.files_scanned += 1
            
        logger.info(f"📊 Scanned {self.files_scanned} files")
        
    async def _scan_file_for_vulnerabilities(self, file_path: Path):
        """Scan a single file for security vulnerabilities."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            for line_num, line in enumerate(lines, 1):
                await self._check_line_for_patterns(file_path, line_num, line)
                
        except Exception as e:
            logger.warning(f"Could not scan {file_path}: {e}")
            
    async def _check_line_for_patterns(self, file_path: Path, line_num: int, line: str):
        """Check a line for vulnerability patterns."""
        line_lower = line.lower().strip()
        
        for category, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    severity = self._determine_severity(category, pattern, line)
                    
                    issue = SecurityIssue(
                        severity=severity,
                        category=category.replace('_', ' ').title(),
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        description=f"Potential {category.replace('_', ' ')} vulnerability detected",
                        recommendation=self._get_recommendation(category, pattern),
                        cwe_id=self._get_cwe_id(category)
                    )
                    
                    self.issues.append(issue)
                    
    def _determine_severity(self, category: str, pattern: str, line: str) -> str:
        """Determine the severity of a security issue."""
        critical_patterns = ['exec', 'eval', 'tx.origin', 'selfdestruct']
        high_patterns = ['sql_injection', 'command_injection', 'hardcoded_secrets']
        
        if any(p in pattern.lower() for p in critical_patterns):
            return 'CRITICAL'
        elif category in high_patterns:
            return 'HIGH'
        elif 'test' in line.lower() or 'mock' in line.lower():
            return 'LOW'
        else:
            return 'MEDIUM'
            
    def _get_recommendation(self, category: str, pattern: str) -> str:
        """Get security recommendation for a vulnerability type."""
        recommendations = {
            'sql_injection': 'Use parameterized queries or prepared statements',
            'xss': 'Sanitize user input and use content security policy',
            'command_injection': 'Avoid dynamic command execution, use safe alternatives',
            'hardcoded_secrets': 'Use environment variables or secure key management',
            'weak_crypto': 'Use strong cryptographic algorithms (AES, SHA-256+)',
            'solidity_vulnerabilities': 'Follow Solidity security best practices',
            'access_control': 'Implement proper access control mechanisms',
            'reentrancy': 'Use reentrancy guards and checks-effects-interactions pattern'
        }
        return recommendations.get(category, 'Review code for security implications')
        
    def _get_cwe_id(self, category: str) -> Optional[str]:
        """Get CWE ID for vulnerability category."""
        cwe_mapping = {
            'sql_injection': 'CWE-89',
            'xss': 'CWE-79',
            'command_injection': 'CWE-78',
            'hardcoded_secrets': 'CWE-798',
            'weak_crypto': 'CWE-327',
            'access_control': 'CWE-284',
            'reentrancy': 'CWE-841'
        }
        return cwe_mapping.get(category)
        
    async def _scan_dependencies(self):
        """Scan project dependencies for known vulnerabilities."""
        logger.info("📦 Phase 2: Dependency Vulnerability Scan")
        
        # Check package.json for npm vulnerabilities
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            await self._check_npm_vulnerabilities()
            
        # Check requirements.txt for Python vulnerabilities
        requirements_txt = self.project_root / 'requirements.txt'
        if requirements_txt.exists():
            await self._check_python_vulnerabilities()
            
    async def _check_npm_vulnerabilities(self):
        """Check npm dependencies for vulnerabilities."""
        try:
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                audit_data = json.loads(result.stdout)
                if 'vulnerabilities' in audit_data:
                    for vuln_id, vuln_data in audit_data['vulnerabilities'].items():
                        issue = SecurityIssue(
                            severity=vuln_data.get('severity', 'MEDIUM').upper(),
                            category='Dependency Vulnerability',
                            file_path='package.json',
                            line_number=1,
                            description=f"Vulnerable dependency: {vuln_id}",
                            recommendation=f"Update to version {vuln_data.get('fixAvailable', 'latest')}"
                        )
                        self.issues.append(issue)
                        
        except Exception as e:
            logger.warning(f"Could not run npm audit: {e}")
            
    async def _check_python_vulnerabilities(self):
        """Check Python dependencies for vulnerabilities."""
        try:
            # Try to run safety check
            result = subprocess.run(
                ['python', '-m', 'pip', 'list', '--format=json'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                packages = json.loads(result.stdout)
                # Known vulnerable packages (simplified check)
                vulnerable_packages = {
                    'flask': ['1.0.0', '1.0.1', '1.0.2'],
                    'django': ['2.0.0', '2.0.1', '2.0.2'],
                    'requests': ['2.19.0', '2.19.1']
                }
                
                for package in packages:
                    name = package['name'].lower()
                    version = package['version']
                    
                    if name in vulnerable_packages and version in vulnerable_packages[name]:
                        issue = SecurityIssue(
                            severity='HIGH',
                            category='Dependency Vulnerability',
                            file_path='requirements.txt',
                            line_number=1,
                            description=f"Vulnerable Python package: {name} {version}",
                            recommendation=f"Update {name} to latest version"
                        )
                        self.issues.append(issue)
                        
        except Exception as e:
            logger.warning(f"Could not check Python vulnerabilities: {e}")
            
    async def _check_configurations(self):
        """Check configuration files for security issues."""
        logger.info("⚙️ Phase 3: Configuration Security Check")
        
        config_files = [
            'hardhat.config.js',
            'hardhat.config.cjs',
            '.env',
            '.env.example',
            'docker-compose.yml',
            'nginx.conf'
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                await self._scan_config_file(config_path)
                
    async def _scan_config_file(self, config_path: Path):
        """Scan a configuration file for security issues."""
        try:
            with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check for common configuration issues
            issues_found = []
            
            if 'password' in content.lower() and '=' in content:
                issues_found.append("Potential hardcoded password in configuration")
                
            if 'debug' in content.lower() and 'true' in content.lower():
                issues_found.append("Debug mode enabled - should be disabled in production")
                
            if 'cors' in content.lower() and '*' in content:
                issues_found.append("Overly permissive CORS configuration")
                
            for issue_desc in issues_found:
                issue = SecurityIssue(
                    severity='MEDIUM',
                    category='Configuration Security',
                    file_path=str(config_path.relative_to(self.project_root)),
                    line_number=1,
                    description=issue_desc,
                    recommendation="Review and secure configuration settings"
                )
                self.issues.append(issue)
                
        except Exception as e:
            logger.warning(f"Could not scan config file {config_path}: {e}")
            
    async def _analyze_smart_contracts(self):
        """Analyze Solidity smart contracts for security issues."""
        logger.info("📜 Phase 4: Smart Contract Security Analysis")
        
        sol_files = list(self.project_root.glob('contracts/**/*.sol'))
        
        for sol_file in sol_files:
            await self._analyze_solidity_file(sol_file)
            
    async def _analyze_solidity_file(self, sol_file: Path):
        """Analyze a Solidity file for security vulnerabilities."""
        try:
            with open(sol_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            # Specific Solidity security checks
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for tx.origin usage
                if 'tx.origin' in line_stripped:
                    issue = SecurityIssue(
                        severity='HIGH',
                        category='Smart Contract Security',
                        file_path=str(sol_file.relative_to(self.project_root)),
                        line_number=line_num,
                        description='Use of tx.origin for authorization',
                        recommendation='Use msg.sender instead of tx.origin',
                        cwe_id='CWE-345'
                    )
                    self.issues.append(issue)
                    
                # Check for unchecked external calls
                if re.search(r'\.call\s*\(', line_stripped) and 'require' not in line_stripped:
                    issue = SecurityIssue(
                        severity='HIGH',
                        category='Smart Contract Security',
                        file_path=str(sol_file.relative_to(self.project_root)),
                        line_number=line_num,
                        description='Unchecked external call',
                        recommendation='Check return value of external calls',
                        cwe_id='CWE-252'
                    )
                    self.issues.append(issue)
                    
        except Exception as e:
            logger.warning(f"Could not analyze Solidity file {sol_file}: {e}")
            
    async def _analyze_api_security(self):
        """Analyze API endpoints for security issues."""
        logger.info("🌐 Phase 5: API Security Analysis")
        
        # Look for API route definitions
        api_files = []
        api_files.extend(list(self.project_root.rglob('*routes*.py')))
        api_files.extend(list(self.project_root.rglob('*api*.py')))
        api_files.extend(list(self.project_root.rglob('*server*.js')))
        api_files.extend(list(self.project_root.rglob('*app*.py')))
        
        for api_file in api_files:
            await self._scan_api_file(api_file)
            
    async def _scan_api_file(self, api_file: Path):
        """Scan an API file for security issues."""
        try:
            with open(api_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower().strip()
                
                # Check for missing authentication
                if ('@app.route' in line_lower or 'app.get' in line_lower or 'app.post' in line_lower):
                    # Look for authentication in next few lines
                    auth_found = False
                    for i in range(line_num, min(line_num + 5, len(lines))):
                        if i < len(lines):
                            next_line = lines[i].lower()
                            if any(auth_keyword in next_line for auth_keyword in ['auth', 'login', 'token', 'jwt']):
                                auth_found = True
                                break
                                
                    if not auth_found and 'public' not in line_lower:
                        issue = SecurityIssue(
                            severity='MEDIUM',
                            category='API Security',
                            file_path=str(api_file.relative_to(self.project_root)),
                            line_number=line_num,
                            description='API endpoint without authentication',
                            recommendation='Add authentication to API endpoints'
                        )
                        self.issues.append(issue)
                        
        except Exception as e:
            logger.warning(f"Could not scan API file {api_file}: {e}")
            
    async def _check_infrastructure_security(self):
        """Check infrastructure configuration for security issues."""
        logger.info("🏗️ Phase 6: Infrastructure Security Check")
        
        # Check for Docker security
        dockerfile = self.project_root / 'Dockerfile'
        if dockerfile.exists():
            await self._check_dockerfile_security(dockerfile)
            
        # Check for deployment scripts
        deploy_files = list(self.project_root.rglob('*deploy*.py'))
        deploy_files.extend(list(self.project_root.rglob('*deploy*.js')))
        
        for deploy_file in deploy_files:
            await self._check_deployment_security(deploy_file)
            
    async def _check_dockerfile_security(self, dockerfile: Path):
        """Check Dockerfile for security issues."""
        try:
            with open(dockerfile, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip().upper()
                
                if line_stripped.startswith('USER ROOT'):
                    issue = SecurityIssue(
                        severity='HIGH',
                        category='Infrastructure Security',
                        file_path=str(dockerfile.relative_to(self.project_root)),
                        line_number=line_num,
                        description='Running container as root user',
                        recommendation='Create and use a non-root user'
                    )
                    self.issues.append(issue)
                    
        except Exception as e:
            logger.warning(f"Could not check Dockerfile: {e}")
            
    async def _check_deployment_security(self, deploy_file: Path):
        """Check deployment scripts for security issues."""
        try:
            with open(deploy_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check for hardcoded secrets in deployment
            if re.search(r'private.*key.*=.*["\'][^"\']{20,}', content, re.IGNORECASE):
                issue = SecurityIssue(
                    severity='CRITICAL',
                    category='Infrastructure Security',
                    file_path=str(deploy_file.relative_to(self.project_root)),
                    line_number=1,
                    description='Hardcoded private key in deployment script',
                    recommendation='Use environment variables for sensitive data'
                )
                self.issues.append(issue)
                
        except Exception as e:
            logger.warning(f"Could not check deployment file {deploy_file}: {e}")
            
    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during scanning."""
        skip_patterns = [
            'node_modules',
            '.git',
            '__pycache__',
            '.pytest_cache',
            'venv',
            '.venv',
            'build',
            'dist',
            '.coverage'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
        
    async def _generate_audit_report(self) -> AuditResult:
        """Generate comprehensive audit report."""
        logger.info("📊 Generating Security Audit Report")
        
        # Count issues by severity
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'INFO': 0
        }
        
        for issue in self.issues:
            severity_counts[issue.severity] += 1
            
        # Calculate security score (100 - weighted severity score)
        weighted_score = (
            severity_counts['CRITICAL'] * 25 +
            severity_counts['HIGH'] * 15 +
            severity_counts['MEDIUM'] * 8 +
            severity_counts['LOW'] * 3 +
            severity_counts['INFO'] * 1
        )
        
        security_score = max(0, 100 - weighted_score)
        scan_duration = time.time() - self.start_time
        
        audit_result = AuditResult(
            total_files_scanned=self.files_scanned,
            total_issues_found=len(self.issues),
            critical_issues=severity_counts['CRITICAL'],
            high_issues=severity_counts['HIGH'],
            medium_issues=severity_counts['MEDIUM'],
            low_issues=severity_counts['LOW'],
            info_issues=severity_counts['INFO'],
            security_score=security_score,
            scan_duration=scan_duration,
            timestamp=datetime.now().isoformat()
        )
        
        # Save detailed report
        await self._save_detailed_report(audit_result)
        
        # Print summary
        self._print_audit_summary(audit_result)
        
        return audit_result
        
    async def _save_detailed_report(self, audit_result: AuditResult):
        """Save detailed audit report to JSON file."""
        report_data = {
            'audit_summary': asdict(audit_result),
            'issues': [asdict(issue) for issue in self.issues],
            'scan_metadata': {
                'auditor_version': '1.0.0',
                'scan_type': 'comprehensive',
                'project_root': str(self.project_root)
            }
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.project_root / f'security_audit_report_{timestamp}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"📄 Detailed report saved: {report_file}")
        
    def _print_audit_summary(self, audit_result: AuditResult):
        """Print audit summary to console."""
        logger.info("\n" + "=" * 60)
        logger.info("🛡️  SECURITY AUDIT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📁 Files Scanned: {audit_result.total_files_scanned}")
        logger.info(f"🔍 Total Issues: {audit_result.total_issues_found}")
        logger.info(f"🚨 Critical: {audit_result.critical_issues}")
        logger.info(f"⚠️  High: {audit_result.high_issues}")
        logger.info(f"⚡ Medium: {audit_result.medium_issues}")
        logger.info(f"💡 Low: {audit_result.low_issues}")
        logger.info(f"ℹ️  Info: {audit_result.info_issues}")
        logger.info(f"📊 Security Score: {audit_result.security_score:.1f}/100")
        logger.info(f"⏱️  Scan Duration: {audit_result.scan_duration:.2f} seconds")
        
        # Security status
        if audit_result.security_score >= 90:
            status = "✅ EXCELLENT"
        elif audit_result.security_score >= 80:
            status = "🟢 GOOD"
        elif audit_result.security_score >= 70:
            status = "🟡 FAIR"
        elif audit_result.security_score >= 60:
            status = "🟠 POOR"
        else:
            status = "🔴 CRITICAL"
            
        logger.info(f"🛡️  Security Status: {status}")
        logger.info("=" * 60)

async def main():
    """Main entry point."""
    project_root = r"C:\Users\mahia\New_Flashloan"
    
    auditor = ComprehensiveSecurityAuditor(project_root)
    audit_result = await auditor.run_comprehensive_audit()
    
    # Additional recommendations based on results
    if audit_result.critical_issues > 0:
        logger.warning("🚨 CRITICAL ISSUES FOUND - Immediate action required!")
        logger.warning("   - Review all critical vulnerabilities immediately")
        logger.warning("   - Do not deploy to production until resolved")
        
    if audit_result.security_score < 80:
        logger.warning("⚠️  Security score below recommended threshold")
        logger.warning("   - Address high and medium priority issues")
        logger.warning("   - Consider additional security testing")
        
    return audit_result

if __name__ == "__main__":
    asyncio.run(main())
