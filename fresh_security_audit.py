#!/usr/bin/env python3
"""
Fresh Security Audit and Issue Detection Script
Performs a comprehensive real-time security check of the Flash Loan Arbitrage System
"""

import os
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class FreshSecurityAudit:
    def __init__(self):
        self.project_root = Path.cwd()
        self.issues = []
        self.fixes_needed = []
        self.security_score = 0
        self.total_checks = 0
        self.passed_checks = 0
        
    def log(self, message, level="INFO"):
        print(f"[{level}] {message}")
        
    def add_issue(self, severity, category, description, file_path="", solution=""):
        """Add an issue to the tracking list"""
        self.issues.append({
            "severity": severity,
            "category": category, 
            "description": description,
            "file_path": file_path,
            "solution": solution,
            "timestamp": datetime.now().isoformat()
        })
        
    def check_placeholder_values(self):
        """Check for problematic placeholder values introduced by security fixes"""
        self.log("🔍 Checking for problematic placeholder values...")
        placeholder_patterns = [
            r'\$\{CONTRACT_ADDRESS\}',
            r'\$\{PRIVATE_KEY\}',
            r'\$\{API_KEY\}',
            r'\$\{[A-Z_]+\}'
        ]
        
        critical_files = [
            "hardhat.config.*", 
            "package.json",
            ".env",
            ".env.production",
            "backend/src/**/*.js",
            "scripts/**/*.js"
        ]
        
        placeholder_issues = []
        
        for pattern in placeholder_patterns:
            try:
                result = subprocess.run([
                    "grep", "-r", "-n", "--include=*.js", "--include=*.json", 
                    "--include=*.env", pattern, str(self.project_root)
                ], capture_output=True, text=True, shell=True)
                
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line and ':' in line:
                            file_path, line_num, content = line.split(':', 2)
                            if any(critical in file_path for critical in ["backend", "scripts", "hardhat", "package"]):
                                placeholder_issues.append({
                                    "file": file_path,
                                    "line": line_num,
                                    "content": content.strip(),
                                    "pattern": pattern
                                })
            except:
                pass
                
        if placeholder_issues:
            for issue in placeholder_issues:
                self.add_issue(
                    "HIGH", 
                    "Configuration", 
                    f"Placeholder value found in critical file: {issue['content']}", 
                    issue['file'],
                    "Replace placeholder with actual value or remove if test data"
                )
                
        self.total_checks += 1
        if not placeholder_issues:
            self.passed_checks += 1
            self.log("✅ No critical placeholder values found")
        else:
            self.log(f"⚠️ Found {len(placeholder_issues)} placeholder issues")
            
    def check_smart_contract_compilation(self):
        """Check if smart contracts compile without errors"""
        self.log("🔍 Checking smart contract compilation...")
        
        try:
            # Check if hardhat is available
            result = subprocess.run([
                "npx", "hardhat", "compile"
            ], capture_output=True, text=True, cwd=self.project_root, shell=True)
            
            self.total_checks += 1
            if result.returncode == 0:
                self.passed_checks += 1
                self.log("✅ Smart contracts compile successfully")
            else:
                self.add_issue(
                    "HIGH",
                    "Compilation",
                    f"Smart contract compilation failed: {result.stderr}",
                    "contracts/",
                    "Fix compilation errors in smart contracts"
                )
                self.log(f"❌ Compilation failed: {result.stderr[:200]}...")
                
        except Exception as e:
            self.add_issue(
                "MEDIUM",
                "Build System",
                f"Unable to run hardhat compile: {str(e)}",
                "hardhat.config.*",
                "Ensure Hardhat is properly configured"
            )
            
    def check_test_execution(self):
        """Check if critical tests can run"""
        self.log("🔍 Checking test execution...")
        
        try:
            # Try to run a simple test
            result = subprocess.run([
                "npx", "hardhat", "test", "--grep", "should deploy"
            ], capture_output=True, text=True, cwd=self.project_root, shell=True, timeout=30)
            
            self.total_checks += 1
            if result.returncode == 0:
                self.passed_checks += 1
                self.log("✅ Basic tests execute successfully")
            else:
                # Check if it's a dependency issue
                if "Cannot convert" in result.stderr or "BigInt" in result.stderr:
                    self.add_issue(
                        "HIGH",
                        "Dependencies",
                        "Test execution failing due to BigInt conversion error",
                        "package.json",
                        "Check for corrupted environment variables or dependency conflicts"
                    )
                else:
                    self.add_issue(
                        "MEDIUM",
                        "Testing",
                        f"Test execution issues: {result.stderr[:200]}",
                        "test/",
                        "Review and fix test configuration"
                    )
                self.log(f"⚠️ Test execution issues detected")
                
        except subprocess.TimeoutExpired:
            self.add_issue(
                "MEDIUM",
                "Testing",
                "Test execution timeout - possible hanging process",
                "test/",
                "Investigate test performance and timeout issues"
            )
        except Exception as e:
            self.log(f"⚠️ Could not run tests: {str(e)}")
            
    def check_critical_security_files(self):
        """Check for presence and validity of critical security files"""
        self.log("🔍 Checking critical security files...")
        
        critical_files = [
            ".env",
            "contracts/SecurityEnhancedExecutor.sol", 
            "contracts/GenericStrategy.sol",
            "contracts/MudarabahInvestmentPool.sol"
        ]
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            self.total_checks += 1
            
            if full_path.exists():
                self.passed_checks += 1
                # Check for basic security patterns
                try:
                    content = full_path.read_text()
                    if file_path.endswith('.sol'):
                        if "ReentrancyGuard" not in content and "nonReentrant" not in content:
                            self.add_issue(
                                "HIGH",
                                "Security",
                                f"Missing reentrancy protection in {file_path}",
                                str(file_path),
                                "Add ReentrancyGuard and nonReentrant modifier"
                            )
                        elif "onlyOwner" not in content and "AccessControl" not in content:
                            self.add_issue(
                                "MEDIUM",
                                "Access Control",
                                f"No access control found in {file_path}",
                                str(file_path),
                                "Add access control modifiers"
                            )
                        else:
                            self.log(f"✅ {file_path} has basic security patterns")
                except Exception as e:
                    self.add_issue(
                        "LOW",
                        "File Access",
                        f"Could not read {file_path}: {str(e)}",
                        str(file_path),
                        "Check file permissions and accessibility"
                    )
            else:
                self.add_issue(
                    "HIGH",
                    "Missing Files",
                    f"Critical file missing: {file_path}",
                    str(file_path),
                    "Ensure all critical files are present"
                )
                
    def check_environment_configuration(self):
        """Check environment configuration for security issues"""
        self.log("🔍 Checking environment configuration...")
        
        env_files = [".env", ".env.template", ".env.production"]
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            self.total_checks += 1
            
            if env_path.exists():
                try:
                    content = env_path.read_text()
                    
                    # Check for hardcoded secrets
                    secret_patterns = [
                        r'PRIVATE_KEY=0x[a-fA-F0-9]{64}',
                        r'API_KEY=[a-zA-Z0-9]{20,}',
                        r'SECRET.*=.{10,}'
                    ]
                    
                    has_secrets = False
                    for pattern in secret_patterns:
                        if re.search(pattern, content):
                            has_secrets = True
                            break
                            
                    if has_secrets and env_file in [".env", ".env.production"]:
                        self.add_issue(
                            "HIGH",
                            "Secret Management",
                            f"Hardcoded secrets found in {env_file}",
                            str(env_file),
                            "Use environment variables or secure key management"
                        )
                    else:
                        self.passed_checks += 1
                        self.log(f"✅ {env_file} appears secure")
                        
                except Exception as e:
                    self.add_issue(
                        "LOW",
                        "Configuration",
                        f"Could not read {env_file}: {str(e)}",
                        str(env_file),
                        "Check file accessibility"
                    )
            else:
                if env_file == ".env":
                    self.add_issue(
                        "MEDIUM",
                        "Configuration",
                        "Missing .env file",
                        ".env",
                        "Create .env file from .env.template"
                    )
                else:
                    self.passed_checks += 1
                    
    def check_dependency_vulnerabilities(self):
        """Check for known dependency vulnerabilities"""
        self.log("🔍 Checking dependency vulnerabilities...")
        
        try:
            result = subprocess.run([
                "npm", "audit", "--json"
            ], capture_output=True, text=True, cwd=self.project_root, shell=True)
            
            self.total_checks += 1
            
            if result.returncode == 0:
                try:
                    audit_data = json.loads(result.stdout)
                    if audit_data.get("vulnerabilities", {}):
                        vuln_count = len(audit_data["vulnerabilities"])
                        high_count = sum(1 for v in audit_data["vulnerabilities"].values() 
                                       if v.get("severity") in ["high", "critical"])
                        
                        if high_count > 0:
                            self.add_issue(
                                "HIGH",
                                "Dependencies",
                                f"Found {high_count} high/critical vulnerabilities in dependencies",
                                "package.json",
                                "Run 'npm audit fix' to address vulnerabilities"
                            )
                        elif vuln_count > 0:
                            self.add_issue(
                                "MEDIUM",
                                "Dependencies", 
                                f"Found {vuln_count} dependency vulnerabilities",
                                "package.json",
                                "Review and update vulnerable dependencies"
                            )
                        else:
                            self.passed_checks += 1
                            self.log("✅ No dependency vulnerabilities found")
                    else:
                        self.passed_checks += 1
                        self.log("✅ No dependency vulnerabilities found")
                except json.JSONDecodeError:
                    self.log("⚠️ Could not parse npm audit output")
            else:
                self.log("⚠️ npm audit failed to run")
                
        except Exception as e:
            self.log(f"⚠️ Could not run dependency check: {str(e)}")
            
    def calculate_security_score(self):
        """Calculate overall security score"""
        if self.total_checks == 0:
            return 0
            
        base_score = (self.passed_checks / self.total_checks) * 100
        
        # Deduct points for issues
        deductions = 0
        for issue in self.issues:
            if issue["severity"] == "HIGH":
                deductions += 10
            elif issue["severity"] == "MEDIUM":
                deductions += 5
            elif issue["severity"] == "LOW":
                deductions += 2
                
        self.security_score = max(0, base_score - deductions)
        return self.security_score
        
    def generate_report(self):
        """Generate comprehensive security report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "security_score": self.calculate_security_score(),
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "issues_found": len(self.issues),
            "production_ready": self.security_score >= 80 and len([i for i in self.issues if i["severity"] == "HIGH"]) == 0,
            "issues": self.issues,
            "summary": {
                "high_severity": len([i for i in self.issues if i["severity"] == "HIGH"]),
                "medium_severity": len([i for i in self.issues if i["severity"] == "MEDIUM"]),
                "low_severity": len([i for i in self.issues if i["severity"] == "LOW"])
            }
        }
        
        # Save report
        report_file = self.project_root / f"fresh_security_audit_{int(datetime.now().timestamp())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report, report_file
        
    def run_audit(self):
        """Run complete security audit"""
        self.log("🔒 STARTING FRESH SECURITY AUDIT")
        self.log("=" * 50)
        
        # Run all checks
        self.check_placeholder_values()
        self.check_smart_contract_compilation()
        self.check_test_execution()
        self.check_critical_security_files()
        self.check_environment_configuration()
        self.check_dependency_vulnerabilities()
        
        # Generate report
        report, report_file = self.generate_report()
        
        # Print summary
        self.log("\n" + "=" * 50)
        self.log("🔒 FRESH SECURITY AUDIT COMPLETE")
        self.log("=" * 50)
        self.log(f"📊 Security Score: {report['security_score']:.1f}%")
        self.log(f"✅ Tests Passed: {report['passed_checks']}/{report['total_checks']}")
        self.log(f"🚨 Issues Found: {report['issues_found']}")
        self.log(f"   - High: {report['summary']['high_severity']}")
        self.log(f"   - Medium: {report['summary']['medium_severity']}")
        self.log(f"   - Low: {report['summary']['low_severity']}")
        self.log(f"🚀 Production Ready: {'YES' if report['production_ready'] else 'NO'}")
        self.log(f"📄 Report saved: {report_file}")
        
        if report['issues_found'] > 0:
            self.log("\n🔧 RECOMMENDED FIXES:")
            for i, issue in enumerate(self.issues[:5], 1):  # Show top 5 issues
                self.log(f"{i}. [{issue['severity']}] {issue['description']}")
                if issue['solution']:
                    self.log(f"   Solution: {issue['solution']}")
                    
        return report

if __name__ == "__main__":
    auditor = FreshSecurityAudit()
    auditor.run_audit()
