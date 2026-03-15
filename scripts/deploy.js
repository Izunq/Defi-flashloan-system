/**
 * deploy.js — Deploy all core contracts to Arbitrum One (mainnet)
 *
 * Usage:
 *   npx hardhat run scripts/deploy.js --network arbitrum
 *
 * Prerequisites:
 *   - ALCHEMY_ARBITRUM_URL set in .env
 *   - PRIVATE_KEY set in .env (deployer wallet with real ETH on Arbitrum)
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

const CONFIG_PATH = path.resolve(__dirname, "../config/arbitrum.json");
const TOKENS_PATH = path.resolve(__dirname, "../config/tokens.json");

async function main() {
  const [deployer] = await ethers.getSigners();
  const deployerAddress = await deployer.getAddress();

  console.log("=".repeat(60));
  console.log("  Arbitrum One — MAINNET Deployment");
  console.log("=".repeat(60));
  console.log(`  Deployer : ${deployerAddress}`);

  const balance = await ethers.provider.getBalance(deployerAddress);
  console.log(`  Balance  : ${ethers.formatEther(balance)} ETH`);

  const network = await ethers.provider.getNetwork();
  if (network.chainId !== 42161n) {
    throw new Error(
      `Expected chain ID 42161 (Arbitrum One) but got ${network.chainId}. ` +
        "Use --network arbitrum"
    );
  }
  console.log(`  Chain ID : ${network.chainId}`);
  console.log("=".repeat(60));

  // Load configs
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf-8"));
  const tokensConfig = JSON.parse(fs.readFileSync(TOKENS_PATH, "utf-8"));

  const aavePoolAddress = config.contracts.aave_v3_pool;
  console.log(`\n  Aave V3 Pool : ${aavePoolAddress}`);

  // ── 1. Deploy HalalAssetRegistry ────────────────────────────────────
  // Pre-blacklist known interest-bearing tokens (aTokens, etc.)
  const blacklistedTokens = tokensConfig.known_interest_bearing || [];
  console.log("\n[1/4] Deploying HalalAssetRegistry ...");
  console.log(`       Pre-blacklisting ${blacklistedTokens.length} interest-bearing token(s):`);
  blacklistedTokens.forEach((addr, i) => console.log(`         ${i + 1}. ${addr}`));

  const HalalAssetRegistry = await ethers.getContractFactory("HalalAssetRegistry");
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
    deployerAddress // profitReceiver = deployer
  );
  await flashLoan.waitForDeployment();
  const flashLoanAddress = await flashLoan.getAddress();
  console.log(`       FlashLoanArbitrage deployed at: ${flashLoanAddress}`);

  // ── Post-deployment setup ───────────────────────────────────────────

  // Grant MUDARIB_ROLE on MudarabahPool to deployer
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

  // Approve standard tokens as halal
  console.log("\n[Setup] Approving halal tokens ...");
  const halalTokens = [
    { addr: config.tokens.WETH, name: "WETH", reason: "Wrapped native ETH" },
    { addr: config.tokens.USDC, name: "USDC", reason: "Fiat-backed stablecoin" },
    { addr: config.tokens.USDT, name: "USDT", reason: "Fiat-backed stablecoin" },
    { addr: config.tokens.WBTC, name: "WBTC", reason: "Wrapped Bitcoin" },
    { addr: config.tokens.ARB, name: "ARB", reason: "Arbitrum governance token" },
  ];
  for (const t of halalTokens) {
    if (t.addr) {
      const tx = await halalRegistry.approveAsset(t.addr, t.name, t.reason);
      await tx.wait();
      console.log(`        Approved: ${t.name} (${t.addr})`);
    }
  }

  // Add Chainlink ETH/USD feed
  const WETH = config.tokens.WETH;
  const USDC = config.tokens.USDC;
  const WBTC = config.tokens.WBTC;

  if (config.contracts.chainlink_eth_usd) {
    console.log("\n[Setup] Adding Chainlink ETH/USD feed to PriceOracle ...");
    const tx1 = await priceOracle.addFeed(
      WETH,
      USDC,
      config.contracts.chainlink_eth_usd
    );
    await tx1.wait();
    console.log(`        Feed added: ETH/USD -> ${config.contracts.chainlink_eth_usd}`);
  }

  // Add Chainlink BTC/USD feed
  if (config.contracts.chainlink_btc_usd) {
    console.log("\n[Setup] Adding Chainlink BTC/USD feed to PriceOracle ...");
    const tx2 = await priceOracle.addFeed(
      WBTC,
      USDC,
      config.contracts.chainlink_btc_usd
    );
    await tx2.wait();
    console.log(`        Feed added: BTC/USD -> ${config.contracts.chainlink_btc_usd}`);
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
  console.log("  Deployment Summary — Arbitrum One (Mainnet)");
  console.log("=".repeat(60));
  console.log(`  HalalAssetRegistry  : ${halalRegistryAddress}`);
  console.log(`  PriceOracle         : ${priceOracleAddress}`);
  console.log(`  MudarabahPool       : ${mudarabahPoolAddress}`);
  console.log(`  FlashLoanArbitrage  : ${flashLoanAddress}`);
  console.log("-".repeat(60));
  console.log(`  Chainlink ETH/USD   : ${config.contracts.chainlink_eth_usd}`);
  console.log(`  Chainlink BTC/USD   : ${config.contracts.chainlink_btc_usd}`);
  console.log(`  Blacklisted tokens  : ${blacklistedTokens.length}`);
  console.log("=".repeat(60));
  console.log("\nNext steps:");
  console.log("  1. Verify contracts:  npx hardhat run scripts/verify.js --network arbitrum");
  console.log("  2. Approve halal tokens on the HalalAssetRegistry (WETH, USDC, USDT, WBTC, ARB)");
  console.log("  3. Fund the MudarabahPool with liquidity");
  console.log("  4. Grant EXECUTOR_ROLE on FlashLoanArbitrage to your bot address");
  console.log("");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
