/**
 * deploy-testnet.js — Deploy all core contracts to Arbitrum Sepolia
 *
 * Usage:
 *   npx hardhat run scripts/deploy-testnet.js --network arbitrumSepolia
 *
 * Prerequisites:
 *   - ALCHEMY_ARBITRUM_SEPOLIA_URL set in .env
 *   - PRIVATE_KEY set in .env (deployer wallet with Sepolia ETH)
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

const CONFIG_PATH = path.resolve(__dirname, "../config/arbitrum-sepolia.json");

async function main() {
  const [deployer] = await ethers.getSigners();
  const deployerAddress = await deployer.getAddress();

  console.log("=".repeat(60));
  console.log("  Arbitrum Sepolia — Testnet Deployment");
  console.log("=".repeat(60));
  console.log(`  Deployer : ${deployerAddress}`);

  const balance = await ethers.provider.getBalance(deployerAddress);
  console.log(`  Balance  : ${ethers.formatEther(balance)} ETH`);
  console.log("=".repeat(60));

  // Load network config for Aave pool address
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf-8"));
  const aavePoolAddress = config.contracts.aave_v3_pool;
  console.log(`\n  Aave V3 Pool : ${aavePoolAddress}`);

  // ── 1. Deploy HalalAssetRegistry ────────────────────────────────────
  console.log("\n[1/4] Deploying HalalAssetRegistry ...");
  const HalalAssetRegistry = await ethers.getContractFactory("HalalAssetRegistry");
  // Empty blacklist for testnet — no known interest-bearing tokens on Sepolia
  const blacklistedTokens = [];
  const halalRegistry = await HalalAssetRegistry.deploy(blacklistedTokens);
  await halalRegistry.waitForDeployment();
  const halalRegistryAddress = await halalRegistry.getAddress();
  console.log(`       HalalAssetRegistry deployed at: ${halalRegistryAddress}`);

  // ── 2. Deploy PriceOracle ───────────────────────────────────────────
  console.log("\n[2/4] Deploying PriceOracle ...");
  const PriceOracle = await ethers.getContractFactory("PriceOracle");
  const priceOracle = await PriceOracle.deploy();
  await priceOracle.waitForDeployment();
  const priceOracleAddress = await priceOracle.getAddress();
  console.log(`       PriceOracle deployed at: ${priceOracleAddress}`);

  // ── 3. Deploy MudarabahPool ─────────────────────────────────────────
  console.log("\n[3/4] Deploying MudarabahPool ...");
  const MudarabahPool = await ethers.getContractFactory("MudarabahPool");
  const mudarabahPool = await MudarabahPool.deploy(halalRegistryAddress);
  await mudarabahPool.waitForDeployment();
  const mudarabahPoolAddress = await mudarabahPool.getAddress();
  console.log(`       MudarabahPool deployed at: ${mudarabahPoolAddress}`);

  // ── 4. Deploy FlashLoanArbitrage ────────────────────────────────────
  console.log("\n[4/4] Deploying FlashLoanArbitrage ...");
  const FlashLoanArbitrage = await ethers.getContractFactory("FlashLoanArbitrage");
  const flashLoan = await FlashLoanArbitrage.deploy(
    aavePoolAddress,
    deployerAddress // profitReceiver = deployer on testnet
  );
  await flashLoan.waitForDeployment();
  const flashLoanAddress = await flashLoan.getAddress();
  console.log(`       FlashLoanArbitrage deployed at: ${flashLoanAddress}`);

  // ── Post-deployment setup ───────────────────────────────────────────

  // Grant MUDARIB_ROLE on MudarabahPool to the deployer
  console.log("\n[Setup] Granting MUDARIB_ROLE to deployer on MudarabahPool ...");
  const MUDARIB_ROLE = await mudarabahPool.MUDARIB_ROLE();
  const hasRole = await mudarabahPool.hasRole(MUDARIB_ROLE, deployerAddress);
  if (hasRole) {
    console.log("        Deployer already has MUDARIB_ROLE (granted in constructor).");
  } else {
    const grantTx = await mudarabahPool.grantRole(MUDARIB_ROLE, deployerAddress);
    await grantTx.wait();
    console.log("        MUDARIB_ROLE granted.");
  }

  // Approve halal tokens if any are configured
  const halalTokens = [
    { addr: config.tokens.WETH, name: "WETH", reason: "Wrapped native ETH" },
    { addr: config.tokens.USDC, name: "USDC", reason: "Fiat-backed stablecoin" },
    { addr: config.tokens.USDT, name: "USDT", reason: "Fiat-backed stablecoin" },
    { addr: config.tokens.WBTC, name: "WBTC", reason: "Wrapped Bitcoin" },
    { addr: config.tokens.ARB, name: "ARB", reason: "Arbitrum governance token" },
  ].filter(t => t.addr);
  if (halalTokens.length > 0) {
    console.log("\n[Setup] Approving halal tokens ...");
    for (const t of halalTokens) {
      const tx = await halalRegistry.approveAsset(t.addr, t.name, t.reason);
      await tx.wait();
      console.log(`        Approved: ${t.name} (${t.addr})`);
    }
  } else {
    console.log("\n[Setup] No tokens configured for testnet -- skipping halal approvals.");
  }

  // Set up oracle feeds if Chainlink addresses are available on testnet
  // Arbitrum Sepolia may not have official Chainlink feeds — set up only if
  // addresses are present in the config.
  if (config.contracts.chainlink_eth_usd) {
    console.log("\n[Setup] Adding Chainlink ETH/USD feed to PriceOracle ...");
    const WETH = config.tokens.WETH || ethers.ZeroAddress;
    const USDC = config.tokens.USDC || ethers.ZeroAddress;
    if (WETH !== ethers.ZeroAddress && USDC !== ethers.ZeroAddress) {
      const feedTx = await priceOracle.addFeed(
        WETH,
        USDC,
        config.contracts.chainlink_eth_usd
      );
      await feedTx.wait();
      console.log("        ETH/USD feed added.");
    } else {
      console.log("        Skipped — WETH or USDC token address not configured.");
    }
  } else {
    console.log("\n[Setup] No Chainlink feeds configured for testnet — skipping oracle setup.");
  }

  // ── Write deployed addresses to config ──────────────────────────────
  config.deployed_contracts = {
    HalalAssetRegistry: halalRegistryAddress,
    PriceOracle: priceOracleAddress,
    MudarabahPool: mudarabahPoolAddress,
    FlashLoanArbitrage: flashLoanAddress,
    deployed_at: new Date().toISOString(),
    deployer: deployerAddress,
  };
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2) + "\n", "utf-8");
  console.log(`\n[Config] Deployed addresses written to ${CONFIG_PATH}`);

  // ── Summary ─────────────────────────────────────────────────────────
  console.log("\n" + "=".repeat(60));
  console.log("  Deployment Summary — Arbitrum Sepolia");
  console.log("=".repeat(60));
  console.log(`  HalalAssetRegistry  : ${halalRegistryAddress}`);
  console.log(`  PriceOracle         : ${priceOracleAddress}`);
  console.log(`  MudarabahPool       : ${mudarabahPoolAddress}`);
  console.log(`  FlashLoanArbitrage  : ${flashLoanAddress}`);
  console.log("=".repeat(60));
  console.log("\nNext steps:");
  console.log("  1. Verify contracts:  npx hardhat run scripts/verify.js --network arbitrumSepolia");
  console.log("  2. Approve halal tokens on the HalalAssetRegistry");
  console.log("  3. Fund the MudarabahPool with test tokens");
  console.log("");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
