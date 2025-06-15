const { ethers } = require("hardhat");

async function main() {
    console.log("Starting access control security deployment...");
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    // Deploy EmergencyAccessControlManager
    console.log("Deploying EmergencyAccessControlManager...");
    const AccessControlManager = await ethers.getContractFactory("EmergencyAccessControlManager");
    const accessControlManager = await AccessControlManager.deploy(deployer.address);
    await accessControlManager.waitForDeployment();
    
    console.log("EmergencyAccessControlManager deployed to:", await accessControlManager.getAddress());
    
    // Setup initial roles
    console.log("Setting up initial roles...");
    await accessControlManager.setupInitialRoles(
        deployer.address, // strategist
        deployer.address, // executor  
        deployer.address, // oracle
        deployer.address, // security manager
        deployer.address  // risk manager
    );
    
    console.log("Initial roles configured");
    console.log("Deployment completed successfully!");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("Deployment failed:", error);
        process.exit(1);
    });
