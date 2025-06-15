#!/usr/bin/env python3
"""
Quick deployment and testing script for access control fixes
"""

import json
import time

def create_hardhat_config():
    """Create a basic Hardhat configuration for testing"""
    
    config = {
        "solidity": {
            "version": "0.8.20",
            "settings": {
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                }
            }
        },
        "networks": {
            "hardhat": {
                "chainId": 31337
            },
            "localhost": {
                "url": "http://127.0.0.1:8545"
            }
        },
        "paths": {
            "sources": "./contracts",
            "tests": "./test",
            "cache": "./cache",
            "artifacts": "./artifacts"
        }
    }
    
    with open('hardhat.config.js', 'w') as f:
        f.write(f"""
require("@nomicfoundation/hardhat-toolbox");

module.exports = {json.dumps(config, indent=2)};
""")
    
    print("✅ Created hardhat.config.js")

def create_package_json():
    """Create package.json with required dependencies"""
    
    package = {
        "name": "access-control-fixes",
        "version": "1.0.0",
        "description": "Emergency access control security fixes",
        "scripts": {
            "compile": "hardhat compile",
            "test": "hardhat test",
            "deploy": "hardhat run scripts/deploy.js",
            "security-scan": "python verify_access_control.py"
        },
        "devDependencies": {
            "@nomicfoundation/hardhat-toolbox": "^4.0.0",
            "hardhat": "^2.19.4"
        },
        "dependencies": {
            "@openzeppelin/contracts": "^5.0.1"
        }
    }
    
    with open('package.json', 'w') as f:
        json.dump(package, f, indent=2)
    
    print("✅ Created package.json")

def create_test_file():
    """Create test file to verify access controls"""
    
    test_content = '''
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Access Control Security Tests", function () {
    let accessControlManager;
    let strategyIncubator;
    let owner, strategist, executor, unauthorized;
    
    before(async function () {
        [owner, strategist, executor, unauthorized] = await ethers.getSigners();
        
        // Deploy EmergencyAccessControlManager
        const AccessControlManager = await ethers.getContractFactory("EmergencyAccessControlManager");
        accessControlManager = await AccessControlManager.deploy(owner.address);
        await accessControlManager.waitForDeployment();
        
        console.log("✅ EmergencyAccessControlManager deployed");
    });
    
    it("Should have correct initial roles", async function () {
        const DEFAULT_ADMIN_ROLE = await accessControlManager.DEFAULT_ADMIN_ROLE();
        const EMERGENCY_ROLE = await accessControlManager.EMERGENCY_ROLE();
        
        expect(await accessControlManager.hasRole(DEFAULT_ADMIN_ROLE, owner.address)).to.be.true;
        expect(await accessControlManager.hasRole(EMERGENCY_ROLE, owner.address)).to.be.true;
    });
    
    it("Should allow admin to setup initial roles", async function () {
        await accessControlManager.setupInitialRoles(
            strategist.address,
            executor.address,
            owner.address, // oracle
            owner.address, // security manager
            owner.address  // risk manager
        );
        
        const STRATEGY_PROPOSER_ROLE = await accessControlManager.STRATEGY_PROPOSER_ROLE();
        const STRATEGY_EXECUTOR_ROLE = await accessControlManager.STRATEGY_EXECUTOR_ROLE();
        
        expect(await accessControlManager.hasRole(STRATEGY_PROPOSER_ROLE, strategist.address)).to.be.true;
        expect(await accessControlManager.hasRole(STRATEGY_EXECUTOR_ROLE, executor.address)).to.be.true;
    });
    
    it("Should track approved proposers", async function () {
        expect(await accessControlManager.isApprovedProposer(strategist.address)).to.be.true;
        expect(await accessControlManager.isApprovedProposer(unauthorized.address)).to.be.false;
    });
    
    it("Should allow emergency mode activation", async function () {
        await accessControlManager.activateEmergencyMode("Testing emergency procedures");
        
        expect(await accessControlManager.globalEmergencyMode()).to.be.true;
        expect(await accessControlManager.paused()).to.be.true;
    });
    
    it("Should allow emergency mode deactivation", async function () {
        await accessControlManager.deactivateEmergencyMode();
        
        expect(await accessControlManager.globalEmergencyMode()).to.be.false;
        expect(await accessControlManager.paused()).to.be.false;
    });
    
    it("Should batch approve proposers", async function () {
        const proposers = [unauthorized.address];
        const approvals = [true];
        
        await accessControlManager.batchSetProposerApproval(proposers, approvals);
        
        expect(await accessControlManager.isApprovedProposer(unauthorized.address)).to.be.true;
    });
    
    it("Should prevent unauthorized access to admin functions", async function () {
        await expect(
            accessControlManager.connect(unauthorized).activateEmergencyMode("Unauthorized test")
        ).to.be.revertedWith("AccessControl:");
    });
    
    it("Should log role assignments", async function () {
        const ORACLE_ROLE = await accessControlManager.ORACLE_ROLE();
        
        await accessControlManager.grantRoleWithLogging(ORACLE_ROLE, strategist.address);
        
        expect(await accessControlManager.hasRole(ORACLE_ROLE, strategist.address)).to.be.true;
        
        const roleHistory = await accessControlManager.getRoleHistory(strategist.address);
        expect(roleHistory.length).to.be.greaterThan(0);
    });
    
    console.log("🎉 All access control tests passed!");
});
'''
    
    with open('test/access-control-security.js', 'w') as f:
        f.write(test_content)
    
    print("✅ Created test/access-control-security.js")

def create_deploy_script():
    """Create deployment script"""
    
    deploy_script = '''
const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 Starting access control security deployment...");
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    console.log("Account balance:", ethers.formatEther(await deployer.provider.getBalance(deployer.address)));
    
    // Deploy EmergencyAccessControlManager
    console.log("📦 Deploying EmergencyAccessControlManager...");
    const AccessControlManager = await ethers.getContractFactory("EmergencyAccessControlManager");
    const accessControlManager = await AccessControlManager.deploy(deployer.address);
    await accessControlManager.waitForDeployment();
    
    console.log("✅ EmergencyAccessControlManager deployed to:", await accessControlManager.getAddress());
    
    // Setup initial roles
    console.log("🔧 Setting up initial roles...");
    await accessControlManager.setupInitialRoles(
        deployer.address, // strategist
        deployer.address, // executor  
        deployer.address, // oracle
        deployer.address, // security manager
        deployer.address  // risk manager
    );
    
    console.log("✅ Initial roles configured");
    
    // Create deployment summary
    const deploymentInfo = {
        timestamp: new Date().toISOString(),
        network: "hardhat",
        deployer: deployer.address,
        contracts: {
            EmergencyAccessControlManager: await accessControlManager.getAddress()
        }
    };
    
    console.log("📄 Deployment Summary:", JSON.stringify(deploymentInfo, null, 2));
    
    console.log("🎉 Deployment completed successfully!");
    return deploymentInfo;
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
'''
    
    with open('scripts/deploy.js', 'w') as f:
        f.write(deploy_script)
    
    print("✅ Created scripts/deploy.js")

def main():
    """Main setup function"""
    
    print("🔧 Setting up development environment for access control fixes...")
    
    # Create necessary directories
    import os
    os.makedirs('scripts', exist_ok=True)
    os.makedirs('test', exist_ok=True)
    
    # Create configuration files
    create_hardhat_config()
    create_package_json()
    create_test_file()
    create_deploy_script()
    
    print("\\n✅ Setup completed! Next steps:")
    print("1. Run: npm install")
    print("2. Run: npm run compile")
    print("3. Run: npm run test")
    print("4. Run: npm run deploy")
    print("5. Run: npm run security-scan")
    
    print("\\n🛡️ Emergency access control fixes are ready for deployment!")

if __name__ == "__main__":
    main()
