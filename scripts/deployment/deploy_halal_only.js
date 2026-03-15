// SPDX-License-Identifier: MIT
const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying Halal-Compliant AI Trading & Investment Protocol...");

  // Get signers
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  // Deploy HalalAssetRegistry
  const HalalAssetRegistry = await ethers.getContractFactory("HalalAssetRegistry");
  const halalRegistry = await HalalAssetRegistry.deploy(
    deployer.address, // admin
    deployer.address  // shariah committee
  );
  await halalRegistry.deployed();
  console.log("HalalAssetRegistry deployed to:", halalRegistry.address);

  // Deploy MudarabahFlashSwap
  const MudarabahFlashSwap = await ethers.getContractFactory("MudarabahFlashSwap");
  const mudarabahFlashSwap = await MudarabahFlashSwap.deploy(
    halalRegistry.address, // halal registry
    deployer.address,      // mudarib treasury
    deployer.address       // admin
  );
  await mudarabahFlashSwap.deployed();
  console.log("MudarabahFlashSwap deployed to:", mudarabahFlashSwap.address);

  // Deploy MudarabahInvestmentPool
  const MudarabahInvestmentPool = await ethers.getContractFactory("MudarabahInvestmentPool");
  const mudarabahInvestmentPool = await MudarabahInvestmentPool.deploy(
    halalRegistry.address, // halal registry
    deployer.address,      // admin
    deployer.address,      // mudarib
    deployer.address,      // shariah advisor
    deployer.address,      // risk manager
    deployer.address,      // zakat manager
    deployer.address,      // AI agent
    deployer.address       // zakat treasury
  );
  await mudarabahInvestmentPool.deployed();
  console.log("MudarabahInvestmentPool deployed to:", mudarabahInvestmentPool.address);

  // Deploy StrategyLeasingPlatform
  const StrategyLeasingPlatform = await ethers.getContractFactory("StrategyLeasingPlatform");
  const strategyLeasingPlatform = await StrategyLeasingPlatform.deploy(
    halalRegistry.address, // halal registry
    deployer.address,      // fee treasury
    deployer.address,      // admin
    deployer.address       // shariah committee
  );
  await strategyLeasingPlatform.deployed();
  console.log("StrategyLeasingPlatform deployed to:", strategyLeasingPlatform.address);

  // Deploy TakafulPool
  const TakafulPool = await ethers.getContractFactory("TakafulPool");
  const takafulPool = await TakafulPool.deploy(
    halalRegistry.address,                // halal registry
    deployer.address,                     // admin
    deployer.address,                     // shariah committee
    deployer.address,                     // claim manager
    "Halal Protocol Takaful Pool",        // name
    "Cooperative insurance for the Halal Protocol", // description
    "0x0000000000000000000000000000000000000000", // contribution token (placeholder)
    ethers.utils.parseEther("50")         // min contribution
  );
  await takafulPool.deployed();
  console.log("TakafulPool deployed to:", takafulPool.address);

  // Deploy ZakatManager
  const ZakatManager = await ethers.getContractFactory("ZakatManager");
  const zakatManager = await ZakatManager.deploy(
    halalRegistry.address, // halal registry
    deployer.address,      // admin
    deployer.address,      // shariah committee
    deployer.address,      // zakat distributor
    deployer.address,      // treasury
    5000 * 10**6,          // gold nisab in USD (6 decimals)
    700 * 10**6            // silver nisab in USD (6 decimals)
  );
  await zakatManager.deployed();
  console.log("ZakatManager deployed to:", zakatManager.address);

  // Deploy SalamFactory
  const SalamFactory = await ethers.getContractFactory("SalamFactory");
  const salamFactory = await SalamFactory.deploy(
    halalRegistry.address, // halal registry
    deployer.address,      // admin
    deployer.address       // shariah committee
  );
  await salamFactory.deployed();
  console.log("SalamFactory deployed to:", salamFactory.address);

  // Deploy IstisnaFactory
  const IstisnaFactory = await ethers.getContractFactory("IstisnaFactory");
  const istisnaFactory = await IstisnaFactory.deploy(
    halalRegistry.address, // halal registry
    deployer.address,      // admin
    deployer.address,      // shariah committee
    deployer.address       // auditor
  );
  await istisnaFactory.deployed();
  console.log("IstisnaFactory deployed to:", istisnaFactory.address);

  console.log("Halal-Compliant AI Trading & Investment Protocol deployed successfully!");

  // Save deployment information
  const deploymentInfo = {
    HalalAssetRegistry: halalRegistry.address,
    MudarabahFlashSwap: mudarabahFlashSwap.address,
    MudarabahInvestmentPool: mudarabahInvestmentPool.address,
    StrategyLeasingPlatform: strategyLeasingPlatform.address,
    TakafulPool: takafulPool.address,
    ZakatManager: zakatManager.address,
    SalamFactory: salamFactory.address,
    IstisnaFactory: istisnaFactory.address
  };

  console.log("Deployment Info:", deploymentInfo);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });