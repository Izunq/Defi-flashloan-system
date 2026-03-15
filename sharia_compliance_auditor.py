#!/usr/bin/env python3
"""
SHARIA COMPLIANCE & SECURITY AUDIT TOOL
Comprehensive audit of the Halal Flash Loan Arbitrage System
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

class ShariaComplianceAuditor:
    def __init__(self):
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "audit_type": "Sharia Compliance & Security",
            "compliance_score": 0,
            "security_score": 0,
            "issues": [],
            "recommendations": [],
            "halal_components": [],
            "non_compliant_components": [],
            "summary": {}
        }
        
        # Sharia compliance criteria
        self.forbidden_keywords = [
            "interest", "riba", "aave", "compound", "lending", "borrowing",
            "flashloan", "liquidity_mining", "staking_rewards", "yield_farming",
            "casino", "gambling", "lottery", "random", "bet", "wager"
        ]
        
        self.compliant_keywords = [
            "mudarabah", "musharakah", "ijara", "salam", "istisna",
            "takaful", "zakat", "halal", "shariah", "profit_sharing",
            "risk_sharing", "islamic_finance"
        ]

    def scan_contract_for_riba(self, file_path):
        """Scan a contract file for interest-based (Riba) elements"""
        issues = []
        compliant_features = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                
            # Check for forbidden elements
            for keyword in self.forbidden_keywords:
                if keyword in content:
                    line_numbers = []
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if keyword in line:
                            line_numbers.append(i)
                    
                    issues.append({
                        "type": "RIBA_VIOLATION",
                        "keyword": keyword,
                        "file": file_path,
                        "lines": line_numbers,
                        "severity": "CRITICAL" if keyword in ["interest", "riba", "flashloan"] else "HIGH"
                    })
            
            # Check for compliant elements
            for keyword in self.compliant_keywords:
                if keyword in content:
                    compliant_features.append({
                        "type": "HALAL_FEATURE",
                        "keyword": keyword,
                        "file": file_path
                    })
                    
        except Exception as e:
            issues.append({
                "type": "FILE_READ_ERROR",
                "file": file_path,
                "error": str(e),
                "severity": "MEDIUM"
            })
            
        return issues, compliant_features

    def audit_contract_structure(self, file_path):
        """Audit contract structure for Islamic finance compliance"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for proper access control
            if "AccessControl" not in content and "Ownable" not in content:
                issues.append({
                    "type": "MISSING_ACCESS_CONTROL",
                    "file": file_path,
                    "severity": "HIGH",
                    "description": "Contract lacks proper access control mechanisms"
                })
            
            # Check for reentrancy protection
            if "ReentrancyGuard" not in content:
                issues.append({
                    "type": "MISSING_REENTRANCY_PROTECTION",
                    "file": file_path,
                    "severity": "HIGH",
                    "description": "Contract lacks reentrancy protection"
                })
            
            # Check for pause functionality
            if "Pausable" not in content and "emergency" not in content.lower():
                issues.append({
                    "type": "MISSING_EMERGENCY_CONTROLS",
                    "file": file_path,
                    "severity": "MEDIUM",
                    "description": "Contract lacks emergency pause functionality"
                })
                
            # Check for proper profit sharing mechanisms
            if "profit" in content.lower() and "share" not in content.lower():
                issues.append({
                    "type": "MISSING_PROFIT_SHARING",
                    "file": file_path,
                    "severity": "HIGH",
                    "description": "Profit mechanisms without proper sharing structure"
                })
                
        except Exception as e:
            issues.append({
                "type": "STRUCTURE_AUDIT_ERROR",
                "file": file_path,
                "error": str(e),
                "severity": "MEDIUM"
            })
            
        return issues

    def audit_halal_contracts(self):
        """Audit all Sharia-compliant contracts"""
        print("🕌 Starting Sharia Compliance Audit...")
        
        halal_contracts = [
            "contracts/HalalAssetRegistry.sol",
            "contracts/MudarabahFlashSwap.sol", 
            "contracts/MudarabahInvestmentPool.sol",
            "contracts/StrategyLeasingPlatform.sol",
            "contracts/TakafulPool.sol",
            "contracts/ZakatManager.sol",
            "contracts/SalamFactory.sol",
            "contracts/IstisnaFactory.sol"
        ]
        
        total_issues = 0
        total_compliant_features = 0
        
        for contract_path in halal_contracts:
            if os.path.exists(contract_path):
                print(f"   Auditing {contract_path}...")
                
                # Scan for Riba violations
                riba_issues, compliant_features = self.scan_contract_for_riba(contract_path)
                
                # Audit contract structure
                structure_issues = self.audit_contract_structure(contract_path)
                
                all_issues = riba_issues + structure_issues
                total_issues += len(all_issues)
                total_compliant_features += len(compliant_features)
                
                self.audit_results["issues"].extend(all_issues)
                self.audit_results["halal_components"].extend(compliant_features)
                
                if all_issues:
                    print(f"      ⚠️  {len(all_issues)} issues found")
                else:
                    print(f"      ✅ Clean - {len(compliant_features)} halal features")
            else:
                print(f"      ❌ Contract not found: {contract_path}")
                self.audit_results["issues"].append({
                    "type": "MISSING_CONTRACT",
                    "file": contract_path,
                    "severity": "HIGH"
                })
        
        return total_issues, total_compliant_features

    def check_removed_components(self):
        """Verify that non-Sharia compliant components have been removed"""
        print("🗑️  Checking removal of non-compliant components...")
        
        non_compliant_files = [
            "contracts/GenericStrategy.sol",
            "contracts/ArbitrageExecutorV33.sol",
            "contracts/ArbitrageVaultERC4626.sol",
            "contracts/SecureArbitrageExecutorV42.sol",
            "contracts/SecureArbitrageExecutorV43.sol",
            "contracts/interfaces/IAavePool.sol",
            "contracts/interfaces/IFlashLoanSimpleReceiver.sol"
        ]
        
        removal_score = 0
        for file_path in non_compliant_files:
            if not os.path.exists(file_path):
                print(f"   ✅ Removed: {file_path}")
                removal_score += 1
            else:
                print(f"   ❌ Still exists: {file_path}")
                self.audit_results["non_compliant_components"].append(file_path)
                self.audit_results["issues"].append({
                    "type": "NON_COMPLIANT_FILE_EXISTS",
                    "file": file_path,
                    "severity": "CRITICAL",
                    "description": "Non-Sharia compliant file still exists"
                })
        
        removal_percentage = (removal_score / len(non_compliant_files)) * 100
        print(f"   Removal completion: {removal_percentage:.1f}%")
        
        return removal_percentage

    def audit_interface_compliance(self):
        """Audit interface files for compliance"""
        print("🔌 Auditing interface compliance...")
        
        interface_dir = "contracts/interfaces"
        compliant_interfaces = [
            "IHalalAssetRegistry.sol",
            "IMudarabahFlashSwap.sol", 
            "IMudarabahInvestmentPool.sol",
            "IStrategyLeasingPlatform.sol"
        ]
        
        interface_issues = 0
        if os.path.exists(interface_dir):
            for interface_file in os.listdir(interface_dir):
                if interface_file.endswith('.sol'):
                    if interface_file in compliant_interfaces:
                        print(f"   ✅ Compliant interface: {interface_file}")
                    else:
                        print(f"   ⚠️  Review needed: {interface_file}")
                        interface_issues += 1
        
        return interface_issues

    def generate_recommendations(self):
        """Generate Sharia compliance recommendations"""
        recommendations = []
        
        # Critical issues
        critical_issues = [issue for issue in self.audit_results["issues"] if issue.get("severity") == "CRITICAL"]
        if critical_issues:
            recommendations.append({
                "priority": "IMMEDIATE",
                "category": "Critical Compliance",
                "action": f"Address {len(critical_issues)} critical Sharia compliance violations",
                "description": "Remove or modify components that violate Islamic finance principles"
            })
        
        # High priority issues  
        high_issues = [issue for issue in self.audit_results["issues"] if issue.get("severity") == "HIGH"]
        if high_issues:
            recommendations.append({
                "priority": "HIGH",
                "category": "Security & Compliance",
                "action": f"Resolve {len(high_issues)} high-priority issues",
                "description": "Implement missing security controls and compliance features"
            })
        
        # Enhancement recommendations
        recommendations.extend([
            {
                "priority": "MEDIUM",
                "category": "Sharia Board Governance",
                "action": "Establish formal Sharia supervisory board",
                "description": "Create governance structure with qualified Islamic finance scholars"
            },
            {
                "priority": "MEDIUM", 
                "category": "Compliance Monitoring",
                "action": "Implement real-time compliance monitoring",
                "description": "Add automated checks for ongoing Sharia compliance"
            },
            {
                "priority": "LOW",
                "category": "Documentation",
                "action": "Create Sharia compliance documentation",
                "description": "Document Islamic finance principles implementation"
            }
        ])
        
        return recommendations

    def calculate_compliance_scores(self):
        """Calculate overall compliance and security scores"""
        total_issues = len(self.audit_results["issues"])
        critical_issues = len([i for i in self.audit_results["issues"] if i.get("severity") == "CRITICAL"])
        high_issues = len([i for i in self.audit_results["issues"] if i.get("severity") == "HIGH"])
        
        # Compliance score (0-100)
        if critical_issues > 0:
            compliance_score = max(0, 30 - (critical_issues * 10))
        elif high_issues > 0:
            compliance_score = max(50, 80 - (high_issues * 5))
        else:
            compliance_score = max(80, 100 - total_issues)
        
        # Security score based on security features
        security_features = len([f for f in self.audit_results["halal_components"] if "security" in str(f).lower()])
        security_score = min(100, 70 + security_features * 5)
        
        return compliance_score, security_score

    def run_full_audit(self):
        """Run complete Sharia compliance and security audit"""
        print("=" * 70)
        print("🕌 SHARIA COMPLIANCE & SECURITY AUDIT")
        print("=" * 70)
        
        # Audit halal contracts
        total_issues, total_compliant_features = self.audit_halal_contracts()
        
        # Check removed components
        removal_percentage = self.check_removed_components()
        
        # Audit interfaces
        interface_issues = self.audit_interface_compliance()
        
        # Generate recommendations
        self.audit_results["recommendations"] = self.generate_recommendations()
        
        # Calculate scores
        compliance_score, security_score = self.calculate_compliance_scores()
        self.audit_results["compliance_score"] = compliance_score
        self.audit_results["security_score"] = security_score
        
        # Summary
        self.audit_results["summary"] = {
            "total_issues": total_issues,
            "compliant_features": total_compliant_features,
            "removal_completion": removal_percentage,
            "interface_issues": interface_issues,
            "compliance_score": compliance_score,
            "security_score": security_score,
            "overall_status": "COMPLIANT" if compliance_score >= 80 else "NEEDS_REVIEW"
        }
        
        self.print_audit_results()
        self.save_audit_report()
        
        return self.audit_results

    def print_audit_results(self):
        """Print formatted audit results"""
        summary = self.audit_results["summary"]
        
        print("\n📊 AUDIT RESULTS SUMMARY")
        print("-" * 40)
        print(f"🎯 Compliance Score: {summary['compliance_score']}/100")
        print(f"🔒 Security Score: {summary['security_score']}/100")
        print(f"📋 Total Issues: {summary['total_issues']}")
        print(f"✅ Halal Features: {summary['compliant_features']}")
        print(f"🗑️  Removal Complete: {summary['removal_completion']:.1f}%")
        print(f"📊 Overall Status: {summary['overall_status']}")
        
        print("\n🚨 CRITICAL FINDINGS")
        print("-" * 40)
        critical_issues = [i for i in self.audit_results["issues"] if i.get("severity") == "CRITICAL"]
        if critical_issues:
            for issue in critical_issues:
                print(f"❌ {issue['type']}: {issue.get('description', 'See details')}")
        else:
            print("✅ No critical issues found")
        
        print("\n📝 TOP RECOMMENDATIONS")
        print("-" * 40)
        for rec in self.audit_results["recommendations"][:3]:
            print(f"🔧 [{rec['priority']}] {rec['action']}")

    def save_audit_report(self):
        """Save detailed audit report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sharia_compliance_audit_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        print(f"\n💾 Detailed report saved: {filename}")

def main():
    auditor = ShariaComplianceAuditor()
    results = auditor.run_full_audit()
    
    print("\n" + "=" * 70)
    print("🎉 SHARIA COMPLIANCE AUDIT COMPLETE")
    print("=" * 70)
    
    return results

if __name__ == "__main__":
    main()
