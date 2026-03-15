#!/usr/bin/env python3
"""
Sentinel Production Deployment Preparation Tool
This script prepares the Sentinel Agent system for production deployment
by validating configurations, checking dependencies, and generating deployment artifacts.
"""

import os
import sys
import json
import yaml
import shutil
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel_deployment_prep.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sentinel_deployment_prep")

class SentinelDeploymentPreparation:
    """Tool for preparing Sentinel Agent system for production deployment"""
    
    def __init__(self, config_path="sentinel_config.yaml", output_dir="deployment"):
        """Initialize the deployment preparation tool"""
        logger.info("Initializing Sentinel Deployment Preparation Tool")
        
        self.config_path = config_path
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "config_validation": {},
            "dependency_check": {},
            "security_check": {},
            "deployment_artifacts": [],
            "deployment_instructions": []
        }
        
        # Load configuration
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def validate_configurations(self):
        """Validate all configuration files"""
        logger.info("Validating configuration files")
        
        config_files = [
            {"name": "sentinel_config", "path": "sentinel_config.yaml", "required": True},
            {"name": "oracle_sentinel_config", "path": "oracle_sentinel_config.yaml", "required": True},
            {"name": "mev_sentinel_config", "path": "mev_sentinel_config.yaml", "required": True},
            {"name": "strategy_sentinel_config", "path": "strategy_sentinel_config.yaml", "required": True},
            {"name": "alert_routing_config", "path": "alert_routing_config.yaml", "required": True},
            {"name": "contract_abi_registry", "path": "contract_abi_registry.json", "required": True},
            {"name": "unified_monitoring_config", "path": "unified_monitoring_config.yaml", "required": True}
        ]
        
        for config_file in config_files:
            result = {
                "name": config_file["name"],
                "path": config_file["path"],
                "status": "FAILED",
                "errors": []
            }
            
            try:
                # Check if file exists
                if not os.path.exists(config_file["path"]):
                    if config_file["required"]:
                        result["errors"].append(f"Required configuration file not found: {config_file['path']}")
                    else:
                        result["status"] = "SKIPPED"
                        result["errors"].append("Optional file not found, skipping validation")
                        self.results["config_validation"][config_file["name"]] = result
                        continue
                
                # Validate file format
                if config_file["path"].endswith(".yaml") or config_file["path"].endswith(".yml"):
                    with open(config_file["path"], "r") as f:
                        yaml_content = yaml.safe_load(f)
                    
                    # Validate required fields based on file type
                    if config_file["name"] == "sentinel_config":
                        if "integration" not in yaml_content:
                            result["errors"].append("Missing 'integration' section")
                    elif config_file["name"] == "alert_routing_config":
                        if "routing_rules" not in yaml_content:
                            result["errors"].append("Missing 'routing_rules' section")
                    elif config_file["name"] == "unified_monitoring_config":
                        if "monitoring_systems" not in yaml_content:
                            result["errors"].append("Missing 'monitoring_systems' section")
                
                elif config_file["path"].endswith(".json"):
                    with open(config_file["path"], "r") as f:
                        json_content = json.load(f)
                    
                    # Validate required fields for JSON files
                    if config_file["name"] == "contract_abi_registry":
                        if "contracts" not in json_content:
                            result["errors"].append("Missing 'contracts' section")
                        else:
                            # Validate contract entries
                            for contract_name, contract_data in json_content["contracts"].items():
                                if "address" not in contract_data:
                                    result["errors"].append(f"Missing 'address' for contract {contract_name}")
                                if "abi" not in contract_data:
                                    result["errors"].append(f"Missing 'abi' for contract {contract_name}")
                                if "emergency_functions" not in contract_data:
                                    result["errors"].append(f"Missing 'emergency_functions' for contract {contract_name}")
                
                # If no errors, mark as passed
                if not result["errors"]:
                    result["status"] = "PASSED"
                
            except Exception as e:
                result["errors"].append(f"Validation error: {str(e)}")
            
            # Record result
            self.results["config_validation"][config_file["name"]] = result
            logger.info(f"Configuration validation for {config_file['name']}: {result['status']}")
            if result["errors"]:
                for error in result["errors"]:
                    logger.warning(f"  - {error}")
    
    def check_dependencies(self):
        """Check required dependencies"""
        logger.info("Checking dependencies")
        
        # Python package dependencies
        python_packages = [
            "web3", "websocket-client", "pyyaml", "requests", 
            "psutil", "memory-profiler", "pytest"
        ]
        
        for package in python_packages:
            result = {
                "name": package,
                "type": "python_package",
                "status": "FAILED",
                "version": None,
                "errors": []
            }
            
            try:
                # Try to import the package
                module = __import__(package.replace("-", "_"))
                version = getattr(module, "__version__", "unknown")
                result["version"] = version
                result["status"] = "PASSED"
            except ImportError as e:
                result["errors"].append(f"Package not installed: {str(e)}")
            except Exception as e:
                result["errors"].append(f"Error checking package: {str(e)}")
            
            # Record result
            self.results["dependency_check"][package] = result
            logger.info(f"Dependency check for {package}: {result['status']} (version: {result['version']})")
        
        # Check Node.js and npm for backend
        node_dependencies = [
            {"name": "node", "command": "node --version"},
            {"name": "npm", "command": "npm --version"}
        ]
        
        for dep in node_dependencies:
            result = {
                "name": dep["name"],
                "type": "system_dependency",
                "status": "FAILED",
                "version": None,
                "errors": []
            }
            
            try:
                # Run command to get version
                process = subprocess.run(
                    dep["command"], 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                
                if process.returncode == 0:
                    result["version"] = process.stdout.strip()
                    result["status"] = "PASSED"
                else:
                    result["errors"].append(f"Command failed: {process.stderr}")
            except Exception as e:
                result["errors"].append(f"Error checking dependency: {str(e)}")
            
            # Record result
            self.results["dependency_check"][dep["name"]] = result
            logger.info(f"Dependency check for {dep['name']}: {result['status']} (version: {result['version']})")
    
    def perform_security_check(self):
        """Perform basic security checks"""
        logger.info("Performing security checks")
        
        security_checks = [
            {"name": "env_variables", "description": "Check for sensitive data in environment variables"},
            {"name": "private_keys", "description": "Check for hardcoded private keys"},
            {"name": "api_keys", "description": "Check for hardcoded API keys"},
            {"name": "input_validation", "description": "Check for input validation in critical functions"}
        ]
        
        for check in security_checks:
            result = {
                "name": check["name"],
                "description": check["description"],
                "status": "PENDING",
                "findings": []
            }
            
            # Implement security checks
            if check["name"] == "env_variables":
                # Check if sensitive data is properly loaded from environment variables
                env_vars = [
                    "WEB3_PROVIDER_URL", "WEB3_PRIVATE_KEY", "SLACK_WEBHOOK_URL",
                    "EMAIL_USERNAME", "EMAIL_PASSWORD", "SMS_API_KEY"
                ]
                
                missing_vars = []
                for var in env_vars:
                    if var not in os.environ:
                        missing_vars.append(var)
                
                if missing_vars:
                    result["status"] = "WARNING"
                    result["findings"].append(f"Missing environment variables: {', '.join(missing_vars)}")
                else:
                    result["status"] = "PASSED"
            
            elif check["name"] == "private_keys":
                # Search for potential hardcoded private keys
                private_key_patterns = [
                    "private_key", "privateKey", "private-key", 
                    "0x[0-9a-fA-F]{64}", "-----BEGIN PRIVATE KEY-----"
                ]
                
                # Use grep to search for patterns (simplified example)
                findings = []
                for pattern in private_key_patterns:
                    try:
                        process = subprocess.run(
                            f"grep -r '{pattern}' --include='*.py' --include='*.js' .",
                            shell=True,
                            capture_output=True,
                            text=True
                        )
                        
                        if process.stdout:
                            findings.append(f"Potential private key pattern '{pattern}' found")
                    except Exception as e:
                        logger.error(f"Error searching for private keys: {e}")
                
                if findings:
                    result["status"] = "WARNING"
                    result["findings"].extend(findings)
                else:
                    result["status"] = "PASSED"
            
            elif check["name"] == "api_keys":
                # Similar to private keys check
                api_key_patterns = [
                    "api_key", "apiKey", "api-key", "token", "secret"
                ]
                
                findings = []
                for pattern in api_key_patterns:
                    try:
                        process = subprocess.run(
                            f"grep -r '{pattern}' --include='*.py' --include='*.js' .",
                            shell=True,
                            capture_output=True,
                            text=True
                        )
                        
                        if process.stdout:
                            findings.append(f"Potential API key pattern '{pattern}' found")
                    except Exception as e:
                        logger.error(f"Error searching for API keys: {e}")
                
                if findings:
                    result["status"] = "WARNING"
                    result["findings"].extend(findings)
                else:
                    result["status"] = "PASSED"
            
            elif check["name"] == "input_validation":
                # This would require more sophisticated analysis
                # For now, just mark as manual check required
                result["status"] = "MANUAL_CHECK_REQUIRED"
                result["findings"].append("Manual review required for input validation")
            
            # Record result
            self.results["security_check"][check["name"]] = result
            logger.info(f"Security check for {check['name']}: {result['status']}")
            if result["findings"]:
                for finding in result["findings"]:
                    logger.warning(f"  - {finding}")
    
    def prepare_deployment_artifacts(self):
        """Prepare deployment artifacts"""
        logger.info("Preparing deployment artifacts")
        
        # Create deployment directory structure
        deployment_dir = os.path.join(self.output_dir, "sentinel_deployment")
        os.makedirs(deployment_dir, exist_ok=True)
        
        # Directories to create
        directories = [
            "config", "scripts", "logs", "docs"
        ]
        
        for directory in directories:
            os.makedirs(os.path.join(deployment_dir, directory), exist_ok=True)
        
        # Copy configuration files
        config_files = [
            "sentinel_config.yaml",
            "oracle_sentinel_config.yaml",
            "mev_sentinel_config.yaml",
            "strategy_sentinel_config.yaml",
            "alert_routing_config.yaml",
            "contract_abi_registry.json",
            "unified_monitoring_config.yaml"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy(
                    config_file, 
                    os.path.join(deployment_dir, "config", config_file)
                )
                self.results["deployment_artifacts"].append(f"config/{config_file}")
        
        # Copy Python scripts
        python_files = [
            "sentinel_coordinator.py",
            "oracle_sentinel.py",
            "mev_sentinel.py",
            "strategy_sentinel.py",
            "sentinel_websocket_broadcaster.py",
            "sentinel_contract_manager.py",
            "emergency_action_executor.py",
            "monitoring_bridge_orchestrator.py",
            "alert_routing_engine.py"
        ]
        
        for python_file in python_files:
            if os.path.exists(python_file):
                shutil.copy(
                    python_file, 
                    os.path.join(deployment_dir, python_file)
                )
                self.results["deployment_artifacts"].append(python_file)
        
        # Copy test and validation scripts
        test_files = [
            "test_sentinel_integration.py",
            "optimize_sentinel_performance.py",
            "validate_alert_delivery.py"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                shutil.copy(
                    test_file, 
                    os.path.join(deployment_dir, "scripts", test_file)
                )
                self.results["deployment_artifacts"].append(f"scripts/{test_file}")
        
        # Copy documentation
        doc_files = [
            "SENTINEL_INTEGRATION_DOCUMENTATION.md",
            "SENTINEL_INTEGRATION_MAP.md"
        ]
        
        for doc_file in doc_files:
            if os.path.exists(doc_file):
                shutil.copy(
                    doc_file, 
                    os.path.join(deployment_dir, "docs", doc_file)
                )
                self.results["deployment_artifacts"].append(f"docs/{doc_file}")
        
        # Create deployment scripts
        self._create_deployment_scripts(deployment_dir)
        
        # Create environment file template
        self._create_env_template(deployment_dir)
        
        # Create requirements.txt
        self._create_requirements_file(deployment_dir)
        
        # Create README
        self._create_readme(deployment_dir)
        
        # Create deployment package
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"sentinel_deployment_{timestamp}.zip"
        shutil.make_archive(
            os.path.join(self.output_dir, f"sentinel_deployment_{timestamp}"),
            'zip',
            deployment_dir
        )
        
        logger.info(f"Created deployment package: {package_name}")
        self.results["deployment_artifacts"].append(package_name)
    
    def _create_deployment_scripts(self, deployment_dir):
        """Create deployment scripts"""
        
        # Start script
        start_script = """#!/bin/bash
# Sentinel System Startup Script

# Load environment variables
source .env

# Start sentinel coordinator
echo "Starting Sentinel Coordinator..."
python sentinel_coordinator.py &

# Start individual sentinels
echo "Starting Oracle Sentinel..."
python oracle_sentinel.py &

echo "Starting MEV Sentinel..."
python mev_sentinel.py &

echo "Starting Strategy Sentinel..."
python strategy_sentinel.py &

echo "All sentinel components started."
"""
        
        with open(os.path.join(deployment_dir, "scripts", "start_sentinels.sh"), "w") as f:
            f.write(start_script)
        
        # Stop script
        stop_script = """#!/bin/bash
# Sentinel System Shutdown Script

echo "Stopping all sentinel processes..."
pkill -f "python.*sentinel"

echo "All sentinel components stopped."
"""
        
        with open(os.path.join(deployment_dir, "scripts", "stop_sentinels.sh"), "w") as f:
            f.write(stop_script)
        
        # Make scripts executable
        os.chmod(os.path.join(deployment_dir, "scripts", "start_sentinels.sh"), 0o755)
        os.chmod(os.path.join(deployment_dir, "scripts", "stop_sentinels.sh"), 0o755)
        
        self.results["deployment_artifacts"].append("scripts/start_sentinels.sh")
        self.results["deployment_artifacts"].append("scripts/stop_sentinels.sh")
    
    def _create_env_template(self, deployment_dir):
        """Create environment variables template"""
        
        env_template = """# Sentinel System Environment Variables

# Web3 Configuration
WEB3_PROVIDER_URL=https://mainnet.infura.io/v3/YOUR_API_KEY
WEB3_PRIVATE_KEY=

# Alert Channels
SLACK_WEBHOOK_URL=
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_FROM=
EMAIL_TO=
SMS_API_KEY=
SMS_FROM=
SMS_TO=

# Monitoring Configuration
MONITORING_API_KEY=
"""
        
        with open(os.path.join(deployment_dir, ".env.template"), "w") as f:
            f.write(env_template)
        
        self.results["deployment_artifacts"].append(".env.template")
    
    def _create_requirements_file(self, deployment_dir):
        """Create requirements.txt file"""
        
        requirements = """# Sentinel System Requirements

# Core dependencies
web3>=5.23.0
websocket-client>=1.3.1
pyyaml>=6.0
requests>=2.27.1

# Testing and optimization
pytest>=7.0.0
psutil>=5.9.0
memory-profiler>=0.60.0

# Monitoring
prometheus-client>=0.14.1

# Utilities
python-dotenv>=0.20.0
"""
        
        with open(os.path.join(deployment_dir, "requirements.txt"), "w") as f:
            f.write(requirements)
        
        self.results["deployment_artifacts"].append("requirements.txt")
    
    def _create_readme(self, deployment_dir):
        """Create README file"""
        
        readme = """# Sentinel System Deployment Package

## Overview
This package contains all components of the Sentinel Agent system, including WebSocket broadcasting, contract interactions, monitoring infrastructure integration, and alert routing.

## Deployment Instructions

### 1. Prerequisites
- Python 3.8+
- Node.js 14+ (for backend WebSocket service)
- Ethereum node access
- SMTP server access (for email alerts)
- Slack webhook (for Slack alerts)
- SMS API access (for SMS alerts)

### 2. Installation
1. Unzip the deployment package
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.template` to `.env` and fill in your configuration values
4. Update configuration files in the `config` directory as needed

### 3. Starting the System
```
cd scripts
./start_sentinels.sh
```

### 4. Stopping the System
```
cd scripts
./stop_sentinels.sh
```

### 5. Validation
After deployment, run the validation scripts to ensure everything is working correctly:
```
cd scripts
python test_sentinel_integration.py
python validate_alert_delivery.py
```

## Documentation
See the `docs` directory for detailed documentation on the Sentinel system.

## Support
For support, please contact the development team.
"""
        
        with open(os.path.join(deployment_dir, "README.md"), "w") as f:
            f.write(readme)
        
        self.results["deployment_artifacts"].append("README.md")
    
    def generate_deployment_instructions(self):
        """Generate deployment instructions"""
        logger.info("Generating deployment instructions")
        
        instructions = [
            {
                "step": 1,
                "title": "Prepare Environment",
                "description": "Set up the server environment with required dependencies",
                "commands": [
                    "# Install Python dependencies",
                    "pip install -r requirements.txt",
                    "",
                    "# Set up environment variables",
                    "cp .env.template .env",
                    "# Edit .env file with your configuration values"
                ]
            },
            {
                "step": 2,
                "title": "Configure System",
                "description": "Update configuration files with production values",
                "commands": [
                    "# Review and update configuration files",
                    "# Ensure contract addresses and ABIs are correct",
                    "# Configure alert routing rules",
                    "# Set up monitoring integration"
                ]
            },
            {
                "step": 3,
                "title": "Validate Configuration",
                "description": "Run validation scripts to ensure configuration is correct",
                "commands": [
                    "# Run configuration validation",
                    "python scripts/test_sentinel_integration.py --validate-config"
                ]
            },
            {
                "step": 4,
                "title": "Start Services",
                "description": "Start all sentinel services",
                "commands": [
                    "# Start all sentinel components",
                    "cd scripts",
                    "./start_sentinels.sh"
                ]
            },
            {
                "step": 5,
                "title": "Verify Deployment",
                "description": "Verify that all components are running correctly",
                "commands": [
                    "# Check process status",
                    "ps aux | grep sentinel",
                    "",
                    "# Check logs",
                    "tail -f logs/sentinel_coordinator.log",
                    "",
                    "# Run validation tests",
                    "python scripts/validate_alert_delivery.py"
                ]
            },
            {
                "step": 6,
                "title": "Set Up Monitoring",
                "description": "Configure monitoring for the sentinel system",
                "commands": [
                    "# Set up process monitoring",
                    "# Configure log monitoring",
                    "# Set up alerts for system failures"
                ]
            }
        ]
        
        self.results["deployment_instructions"] = instructions
    
    def run_preparation(self):
        """Run the complete deployment preparation process"""
        logger.info("Running deployment preparation")
        
        # Validate configurations
        self.validate_configurations()
        
        # Check dependencies
        self.check_dependencies()
        
        # Perform security checks
        self.perform_security_check()
        
        # Prepare deployment artifacts
        self.prepare_deployment_artifacts()
        
        # Generate deployment instructions
        self.generate_deployment_instructions()
        
        # Save results
        self.save_results()
        
        return self.results
    
    def save_results(self):
        """Save preparation results to file"""
        logger.info("Saving preparation results")
        
        # Save JSON results
        with open(os.path.join(self.output_dir, "deployment_preparation_results.json"), "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Generate human-readable report
        with open(os.path.join(self.output_dir, "deployment_preparation_report.md"), "w") as f:
            f.write("# Sentinel System Deployment Preparation Report\n\n")
            f.write(f"Generated: {self.results['timestamp']}\n\n")
            
            f.write("## Configuration Validation\n\n")
            f.write("| Configuration | Status | Issues |\n")
            f.write("|--------------|--------|--------|\n")
            for name, result in self.results["config_validation"].items():
                issues = ", ".join(result["errors"]) if result["errors"] else "None"
                f.write(f"| {name} | {result['status']} | {issues} |\n")
            
            f.write("\n## Dependency Check\n\n")
            f.write("| Dependency | Type | Status | Version |\n")
            f.write("|------------|------|--------|--------|\n")
            for name, result in self.results["dependency_check"].items():
                version = result["version"] or "N/A"
                f.write(f"| {name} | {result['type']} | {result['status']} | {version} |\n")
            
            f.write("\n## Security Check\n\n")
            f.write("| Check | Status | Findings |\n")
            f.write("|-------|--------|----------|\n")
            for name, result in self.results["security_check"].items():
                findings = ", ".join(result["findings"]) if result["findings"] else "None"
                f.write(f"| {result['description']} | {result['status']} | {findings} |\n")
            
            f.write("\n## Deployment Artifacts\n\n")
            for artifact in self.results["deployment_artifacts"]:
                f.write(f"- {artifact}\n")
            
            f.write("\n## Deployment Instructions\n\n")
            for instruction in self.results["deployment_instructions"]:
                f.write(f"### Step {instruction['step']}: {instruction['title']}\n\n")
                f.write(f"{instruction['description']}\n\n")
                f.write("```bash\n")
                for command in instruction["commands"]:
                    f.write(f"{command}\n")
                f.write("```\n\n")
        
        logger.info("Results saved to deployment_preparation_results.json")
        logger.info("Report saved to deployment_preparation_report.md")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Sentinel Deployment Preparation Tool")
    parser.add_argument("--config", default="sentinel_config.yaml", help="Path to sentinel config")
    parser.add_argument("--output", default="deployment", help="Output directory for deployment artifacts")
    args = parser.parse_args()
    
    try:
        preparation = SentinelDeploymentPreparation(
            config_path=args.config,
            output_dir=args.output
        )
        preparation.run_preparation()
        logger.info("Deployment preparation completed successfully")
    except Exception as e:
        logger.error(f"Deployment preparation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()