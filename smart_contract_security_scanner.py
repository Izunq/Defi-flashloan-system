#!/usr/bin/env python3
"""
Smart Contract Security Scanner
==============================

Specialized security scanner for Solidity smart contracts.
Detects common vulnerabilities and security anti-patterns.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SmartContractScanner')

@dataclass
class ContractVulnerability:
    """Smart contract vulnerability data structure."""
    contract_name: str
    function_name: str
    vulnerability_type: str
    severity: str
    line_number: int
    code_snippet: str
    description: str
    recommendation: str
    gas_impact: str

class SmartContractSecurityScanner:
    """Advanced smart contract security scanner."""
    
    def __init__(self, contracts_dir: str):
        self.contracts_dir = Path(contracts_dir)
        self.vulnerabilities: List[ContractVulnerability] = []
        
        # Vulnerability patterns specific to Solidity
        self.vulnerability_patterns = {
            'reentrancy': {
                'patterns': [
                    r'external.*payable',
                    r'\.call\{value:',
                    r'\.call\.value\(',
                    r'\.send\(',
                    r'\.transfer\('
                ],
                'severity': 'HIGH',
                'description': 'Potential reentrancy vulnerability',
                'recommendation': 'Use ReentrancyGuard or checks-effects-interactions pattern'
            },
            'tx_origin': {
                'patterns': [r'tx\.origin'],
                'severity': 'HIGH',
                'description': 'Use of tx.origin for authorization',
                'recommendation': 'Use msg.sender instead of tx.origin'
            },
            'unchecked_call': {
                'patterns': [
                    r'\.call\(',
                    r'\.delegatecall\(',
                    r'\.staticcall\('
                ],
                'severity': 'MEDIUM',
                'description': 'Unchecked external call',
                'recommendation': 'Check return value of external calls'
            },
            'timestamp_dependence': {
                'patterns': [
                    r'block\.timestamp',
                    r'now\s',
                    r'block\.number'
                ],
                'severity': 'MEDIUM',
                'description': 'Timestamp dependence detected',
                'recommendation': 'Avoid using block.timestamp for critical logic'
            },
            'gas_griefing': {
                'patterns': [
                    r'gasleft\(\)',
                    r'gas\(\)',
                    r'\.gas\('
                ],
                'severity': 'MEDIUM',
                'description': 'Potential gas griefing vulnerability',
                'recommendation': 'Implement gas limits and proper gas management'
            },
            'integer_overflow': {
                'patterns': [
                    r'\+\+',
                    r'--',
                    r'\s\+\s',
                    r'\s\-\s',
                    r'\s\*\s'
                ],
                'severity': 'LOW',
                'description': 'Potential integer overflow/underflow',
                'recommendation': 'Use SafeMath library or Solidity 0.8+ built-in checks'
            },
            'access_control': {
                'patterns': [
                    r'onlyOwner',
                    r'onlyAdmin',
                    r'require\s*\(\s*msg\.sender',
                    r'modifier\s+only'
                ],
                'severity': 'INFO',
                'description': 'Access control mechanism detected',
                'recommendation': 'Ensure proper access control implementation'
            },
            'selfdestruct': {
                'patterns': [
                    r'selfdestruct\s*\(',
                    r'suicide\s*\('
                ],
                'severity': 'HIGH',
                'description': 'Self-destruct function detected',
                'recommendation': 'Ensure selfdestruct is properly protected'
            },
            'delegate_call': {
                'patterns': [r'\.delegatecall\s*\('],
                'severity': 'HIGH',
                'description': 'Delegate call detected',
                'recommendation': 'Be careful with delegate calls, they can change contract state'
            },
            'assembly_usage': {
                'patterns': [r'assembly\s*\{'],
                'severity': 'MEDIUM',
                'description': 'Inline assembly usage detected',
                'recommendation': 'Review assembly code carefully for security issues'
            }
        }
        
    def scan_all_contracts(self) -> Dict[str, Any]:
        """Scan all smart contracts in the directory."""
        logger.info("🔍 Starting Smart Contract Security Scan")
        
        sol_files = list(self.contracts_dir.rglob("*.sol"))
        logger.info(f"📄 Found {len(sol_files)} Solidity files")
        
        for sol_file in sol_files:
            self._scan_contract_file(sol_file)
            
        return self._generate_report()
        
    def _scan_contract_file(self, sol_file: Path):
        """Scan a single Solidity file."""
        try:
            with open(sol_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            contract_name = self._extract_contract_name(content)
            logger.info(f"🔎 Scanning contract: {contract_name}")
            
            current_function = "global"
            
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Track current function
                if re.match(r'function\s+(\w+)', line_stripped):
                    match = re.search(r'function\s+(\w+)', line_stripped)
                    if match:
                        current_function = match.group(1)
                        
                # Check for vulnerabilities
                self._check_line_for_vulnerabilities(
                    contract_name, current_function, line_num, line_stripped, sol_file
                )
                
        except Exception as e:
            logger.error(f"Error scanning {sol_file}: {e}")
            
    def _extract_contract_name(self, content: str) -> str:
        """Extract contract name from Solidity code."""
        match = re.search(r'contract\s+(\w+)', content)
        return match.group(1) if match else "Unknown"
        
    def _check_line_for_vulnerabilities(self, contract_name: str, function_name: str, 
                                      line_num: int, line: str, file_path: Path):
        """Check a line for vulnerabilities."""
        for vuln_type, vuln_config in self.vulnerability_patterns.items():
            for pattern in vuln_config['patterns']:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if it's in a comment
                    if '//' in line and line.index('//') < line.index(pattern):
                        continue
                        
                    # Determine gas impact
                    gas_impact = self._estimate_gas_impact(vuln_type, line)
                    
                    vulnerability = ContractVulnerability(
                        contract_name=contract_name,
                        function_name=function_name,
                        vulnerability_type=vuln_type,
                        severity=vuln_config['severity'],
                        line_number=line_num,
                        code_snippet=line.strip(),
                        description=vuln_config['description'],
                        recommendation=vuln_config['recommendation'],
                        gas_impact=gas_impact
                    )
                    
                    self.vulnerabilities.append(vulnerability)
                    break
                    
    def _estimate_gas_impact(self, vuln_type: str, line: str) -> str:
        """Estimate gas impact of vulnerability."""
        high_gas_patterns = ['external', 'storage', 'loop', 'call']
        medium_gas_patterns = ['view', 'pure', 'memory']
        
        line_lower = line.lower()
        
        if any(pattern in line_lower for pattern in high_gas_patterns):
            return "HIGH"
        elif any(pattern in line_lower for pattern in medium_gas_patterns):
            return "MEDIUM"
        else:
            return "LOW"
            
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        # Count vulnerabilities by severity
        severity_counts = {}
        contract_counts = {}
        
        for vuln in self.vulnerabilities:
            severity_counts[vuln.severity] = severity_counts.get(vuln.severity, 0) + 1
            contract_counts[vuln.contract_name] = contract_counts.get(vuln.contract_name, 0) + 1
            
        # Calculate security score
        total_score = 100
        penalty_map = {'HIGH': 15, 'MEDIUM': 8, 'LOW': 3, 'INFO': 1}
        
        for severity, count in severity_counts.items():
            total_score -= penalty_map.get(severity, 0) * count
            
        security_score = max(0, total_score)
        
        # Generate report
        report = {
            'scan_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_vulnerabilities': len(self.vulnerabilities),
                'security_score': security_score,
                'contracts_scanned': len(contract_counts),
                'severity_breakdown': severity_counts
            },
            'contract_analysis': contract_counts,
            'vulnerabilities': [
                {
                    'contract': vuln.contract_name,
                    'function': vuln.function_name,
                    'type': vuln.vulnerability_type,
                    'severity': vuln.severity,
                    'line': vuln.line_number,
                    'code': vuln.code_snippet,
                    'description': vuln.description,
                    'recommendation': vuln.recommendation,
                    'gas_impact': vuln.gas_impact
                }
                for vuln in self.vulnerabilities
            ],
            'recommendations': self._generate_recommendations(severity_counts, security_score)
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.contracts_dir.parent / f'smart_contract_security_report_{timestamp}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self._print_summary(report)
        logger.info(f"📄 Report saved: {report_file}")
        
        return report
        
    def _generate_recommendations(self, severity_counts: Dict[str, int], security_score: float) -> List[str]:
        """Generate security recommendations based on scan results."""
        recommendations = []
        
        if severity_counts.get('HIGH', 0) > 0:
            recommendations.append("🚨 Address all HIGH severity vulnerabilities immediately")
            recommendations.append("🔐 Implement reentrancy guards where needed")
            recommendations.append("⚡ Review and secure all external calls")
            
        if severity_counts.get('MEDIUM', 0) > 0:
            recommendations.append("⚠️ Review and fix MEDIUM severity issues")
            recommendations.append("🕐 Avoid timestamp dependence for critical logic")
            recommendations.append("⛽ Implement proper gas management")
            
        if security_score < 80:
            recommendations.append("📊 Security score below 80 - comprehensive review needed")
            recommendations.append("🧪 Conduct thorough testing before deployment")
            recommendations.append("🔍 Consider professional security audit")
            
        if not recommendations:
            recommendations.append("✅ No critical issues found - ready for deployment")
            recommendations.append("🔄 Continue regular security monitoring")
            
        return recommendations
        
    def _print_summary(self, report: Dict[str, Any]):
        """Print scan summary."""
        summary = report['scan_summary']
        
        logger.info("\n" + "=" * 60)
        logger.info("🛡️  SMART CONTRACT SECURITY SCAN RESULTS")
        logger.info("=" * 60)
        logger.info(f"📄 Contracts Scanned: {summary['contracts_scanned']}")
        logger.info(f"🔍 Total Vulnerabilities: {summary['total_vulnerabilities']}")
        
        for severity, count in summary['severity_breakdown'].items():
            emoji = {'HIGH': '🚨', 'MEDIUM': '⚠️', 'LOW': '💡', 'INFO': 'ℹ️'}.get(severity, '🔸')
            logger.info(f"{emoji} {severity}: {count}")
            
        logger.info(f"📊 Security Score: {summary['security_score']:.1f}/100")
        
        if summary['security_score'] >= 90:
            status = "✅ EXCELLENT"
        elif summary['security_score'] >= 80:
            status = "🟢 GOOD"
        elif summary['security_score'] >= 70:
            status = "🟡 FAIR"
        else:
            status = "🔴 NEEDS WORK"
            
        logger.info(f"🎯 Status: {status}")
        logger.info("=" * 60)

def main():
    """Main entry point."""
    contracts_dir = r"C:\Users\mahia\New_Flashloan\contracts"
    
    scanner = SmartContractSecurityScanner(contracts_dir)
    report = scanner.scan_all_contracts()
    
    return report

if __name__ == "__main__":
    main()
