#!/usr/bin/env python3
"""
ENHANCED SHARIA COMPLIANCE & SECURITY AUDIT
Intelligent audit that understands context and intent
"""

import os
import json
import re
from datetime import datetime

class EnhancedShariaAuditor:
    def __init__(self):
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "audit_type": "Enhanced Sharia Compliance & Security",
            "compliance_score": 0,
            "security_score": 0,
            "issues": [],
            "halal_features": [],
            "security_features": [],
            "summary": {}
        }

    def analyze_contract_intent(self, file_path, content):
        """Analyze if contract is designed for Sharia compliance"""
        halal_indicators = [
            "halal", "shariah", "sharia", "islamic", "mudarabah", "musharakah",
            "ijara", "salam", "istisna", "takaful", "zakat", "profit_sharing",
            "risk_sharing", "compliant", "blacklist.*interest", "prohibited.*industry"
        ]
        
        riba_usage_patterns = [
            r"interest.*rate",
            r"borrow.*interest", 
            r"lend.*interest",
            r"yield.*farming",
            r"flashloan\s*\(",
            r"aave\..*function"
        ]
        
        # Check if contract is designed for compliance
        is_compliance_contract = any(indicator in content.lower() for indicator in halal_indicators)
        
        # Check for actual problematic usage (not just mentions)
        actual_riba_usage = []
        for pattern in riba_usage_patterns:
            matches = re.finditer(pattern, content.lower())
            for match in matches:
                actual_riba_usage.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "start": match.start()
                })
        
        return is_compliance_contract, actual_riba_usage

    def audit_halal_contract(self, file_path):
        """Audit a halal contract with context awareness"""
        if not os.path.exists(file_path):
            return {
                "status": "MISSING",
                "issues": [{"type": "CONTRACT_MISSING", "severity": "HIGH"}],
                "features": []
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            is_compliance_contract, riba_usage = self.analyze_contract_intent(file_path, content)
            
            issues = []
            features = []
            
            # Check for actual Riba usage (not compliance mentions)
            for usage in riba_usage:
                issues.append({
                    "type": "ACTUAL_RIBA_USAGE",
                    "pattern": usage["pattern"],
                    "match": usage["match"],
                    "file": file_path,
                    "severity": "CRITICAL"
                })
            
            # Check for compliance features
            if "HalalAssetRegistry" in content:
                features.append({"type": "HALAL_ASSET_VERIFICATION", "description": "Uses halal asset registry"})
            
            if "SHARIAH_COMMITTEE_ROLE" in content:
                features.append({"type": "SHARIAH_GOVERNANCE", "description": "Implements Shariah committee oversight"})
            
            if "profit.*shar" in content.lower():
                features.append({"type": "PROFIT_SHARING", "description": "Implements profit sharing mechanism"})
            
            if "mudarib" in content.lower():
                features.append({"type": "MUDARABAH_PRINCIPLE", "description": "Follows Mudarabah principles"})
            
            # Security features
            security_features = []
            if "ReentrancyGuard" in content:
                security_features.append({"type": "REENTRANCY_PROTECTION", "level": "HIGH"})
            
            if "AccessControl" in content or "Ownable" in content:
                security_features.append({"type": "ACCESS_CONTROL", "level": "HIGH"})
            
            if "Pausable" in content:
                security_features.append({"type": "EMERGENCY_CONTROLS", "level": "MEDIUM"})
            
            if "nonReentrant" in content:
                security_features.append({"type": "FUNCTION_PROTECTION", "level": "HIGH"})
            
            return {
                "status": "COMPLIANT" if not issues else "NEEDS_REVIEW",
                "is_compliance_contract": is_compliance_contract,
                "issues": issues,
                "features": features,
                "security_features": security_features
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "issues": [{"type": "AUDIT_ERROR", "error": str(e), "severity": "MEDIUM"}],
                "features": []
            }

    def run_comprehensive_audit(self):
        """Run comprehensive audit of the entire system"""
        print("🕌 ENHANCED SHARIA COMPLIANCE & SECURITY AUDIT")
        print("=" * 60)
        
        # Core Sharia-compliant contracts
        halal_contracts = {
            "HalalAssetRegistry": "contracts/HalalAssetRegistry.sol",
            "MudarabahFlashSwap": "contracts/MudarabahFlashSwap.sol",
            "MudarabahInvestmentPool": "contracts/MudarabahInvestmentPool.sol", 
            "StrategyLeasingPlatform": "contracts/StrategyLeasingPlatform.sol",
            "TakafulPool": "contracts/TakafulPool.sol",
            "ZakatManager": "contracts/ZakatManager.sol",
            "SalamFactory": "contracts/SalamFactory.sol",
            "IstisnaFactory": "contracts/IstisnaFactory.sol"
        }
        
        total_issues = 0
        total_features = 0
        total_security_features = 0
        
        print("📋 AUDITING CORE HALAL CONTRACTS")
        print("-" * 40)
        
        for name, path in halal_contracts.items():
            result = self.audit_halal_contract(path)
            
            print(f"🔍 {name}:")
            if result["status"] == "COMPLIANT":
                print(f"   ✅ COMPLIANT - {len(result['features'])} halal features")
            elif result["status"] == "MISSING":
                print(f"   ❌ MISSING CONTRACT")
            else:
                print(f"   ⚠️  {result['status']} - {len(result['issues'])} issues")
            
            total_issues += len(result["issues"])
            total_features += len(result["features"])
            total_security_features += len(result.get("security_features", []))
            
            self.audit_results["issues"].extend(result["issues"])
            self.audit_results["halal_features"].extend(result["features"])
            self.audit_results["security_features"].extend(result.get("security_features", []))
        
        # Check for removed non-compliant files
        print("\n🗑️  VERIFYING REMOVAL OF NON-COMPLIANT COMPONENTS")
        print("-" * 40)
        
        removed_files = [
            "contracts/GenericStrategy.sol",
            "contracts/interfaces/IAavePool.sol", 
            "contracts/interfaces/IFlashLoanSimpleReceiver.sol"
        ]
        
        removal_score = 0
        for file_path in removed_files:
            if not os.path.exists(file_path):
                print(f"   ✅ Removed: {os.path.basename(file_path)}")
                removal_score += 1
            else:
                print(f"   ❌ Still exists: {os.path.basename(file_path)}")
                total_issues += 1
        
        removal_percentage = (removal_score / len(removed_files)) * 100
        
        # Calculate scores
        compliance_score = self.calculate_compliance_score(total_issues, total_features, removal_percentage)
        security_score = self.calculate_security_score(total_security_features, total_issues)
        
        # Print results
        print("\n📊 AUDIT RESULTS")
        print("-" * 40)
        print(f"🎯 Sharia Compliance Score: {compliance_score}/100")
        print(f"🔒 Security Score: {security_score}/100") 
        print(f"📋 Issues Found: {total_issues}")
        print(f"✅ Halal Features: {total_features}")
        print(f"🛡️  Security Features: {total_security_features}")
        print(f"🗑️  Cleanup Complete: {removal_percentage:.1f}%")
        
        overall_status = self.determine_overall_status(compliance_score, security_score)
        print(f"📈 Overall Status: {overall_status}")
        
        # Generate recommendations
        self.generate_final_recommendations(compliance_score, security_score, total_issues)
        
        # Save results
        self.audit_results.update({
            "compliance_score": compliance_score,
            "security_score": security_score,
            "total_issues": total_issues,
            "total_features": total_features,
            "total_security_features": total_security_features,
            "removal_percentage": removal_percentage,
            "overall_status": overall_status
        })
        
        return self.audit_results

    def calculate_compliance_score(self, issues, features, removal_percentage):
        """Calculate Sharia compliance score"""
        # Base score from features
        base_score = min(60, features * 4)
        
        # Bonus for removal of non-compliant components
        removal_bonus = removal_percentage * 0.3
        
        # Penalty for issues
        issue_penalty = issues * 5
        
        score = max(0, min(100, base_score + removal_bonus - issue_penalty))
        return int(score)

    def calculate_security_score(self, security_features, issues):
        """Calculate security score"""
        base_score = 50
        feature_bonus = min(40, security_features * 5)
        issue_penalty = issues * 3
        
        score = max(0, min(100, base_score + feature_bonus - issue_penalty))
        return int(score)

    def determine_overall_status(self, compliance_score, security_score):
        """Determine overall system status"""
        avg_score = (compliance_score + security_score) / 2
        
        if avg_score >= 90:
            return "EXCELLENT - READY FOR PRODUCTION"
        elif avg_score >= 75:
            return "GOOD - MINOR IMPROVEMENTS NEEDED"
        elif avg_score >= 60:
            return "ACCEPTABLE - NEEDS ATTENTION"
        else:
            return "NEEDS SIGNIFICANT WORK"

    def generate_final_recommendations(self, compliance_score, security_score, issues):
        """Generate final recommendations"""
        print("\n💡 RECOMMENDATIONS")
        print("-" * 40)
        
        if compliance_score >= 80 and security_score >= 80:
            print("✅ System is ready for production deployment")
            print("🔧 Consider establishing Sharia supervisory board")
            print("📊 Set up continuous compliance monitoring")
        elif compliance_score >= 60:
            print("⚠️  Address remaining compliance issues")
            print("🔧 Enhance security features") 
            print("📋 Conduct manual review of contracts")
        else:
            print("❌ Significant work required")
            print("🔧 Fix critical compliance violations")
            print("📋 Complete removal of non-compliant components")

    def save_report(self):
        """Save audit report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_sharia_audit_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        print(f"\n💾 Report saved: {filename}")

def main():
    auditor = EnhancedShariaAuditor()
    results = auditor.run_comprehensive_audit()
    auditor.save_report()
    
    print("\n" + "=" * 60)
    print("🎉 ENHANCED SHARIA AUDIT COMPLETE")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    main()
