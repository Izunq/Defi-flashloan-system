const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Access Control Security Tests", function () {
    let accessControlManager;
    let owner, strategist, executor, unauthorized;
    
    before(async function () {
        [owner, strategist, executor, unauthorized] = await ethers.getSigners();
        
        // Deploy EmergencyAccessControlManager
        const AccessControlManager = await ethers.getContractFactory("EmergencyAccessControlManager");
        accessControlManager = await AccessControlManager.deploy(owner.address);
        await accessControlManager.waitForDeployment();
        
        console.log("EmergencyAccessControlManager deployed");
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
    
    it("Should prevent unauthorized access to admin functions", async function () {
        await expect(
            accessControlManager.connect(unauthorized).activateEmergencyMode("Unauthorized test")
        ).to.be.revertedWith("AccessControl:");
    });
    
    console.log("All access control tests passed!");
});
