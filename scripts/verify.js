/**
 * verify.js — Verify all deployed contracts on Arbiscan
 *
 * Usage:
 *   npx hardhat run scripts/verify.js --network arbitrumSepolia
 *   npx hardhat run scripts/verify.js --network arbitrum
 *
 * Prerequisites:
 *   - ARBISCAN_API_KEY set in .env
 *   - Contracts already deployed (addresses read from config/*.json)
 */

const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

// Map Hardhat network names to their config files
const NETWORK_CONFIG_MAP = {
  arbitrum: path.resolve(__dirname, "../config/arbitrum.json"),
  arbitrumSepolia: path.resolve(__dirname, "../config/arbitrum-sepolia.json"),
};

const TOKENS_PATH = path.resolve(__dirname, "../config/tokens.json");

/**
 * Attempt to verify a single contract. Handles "already verified" gracefully.
 */
async function verifyContract(name, address, constructorArguments) {
  console.log(`\n  Verifying ${name} at ${address} ...`);
  try {
    await hre.run("verify:verify", {
      address,
      constructorArguments,
    });
    console.log(`  [OK] ${name} verified successfully.`);
    return true;
  } catch (error) {
    const message = error.message || "";
    if (
      message.includes("Already Verified") ||
      message.includes("already verified")
    ) {
      console.log(`  [SKIP] ${name} is already verified.`);
      return true;
    }
    console.error(`  [FAIL] ${name} verification failed: ${message}`);
    return false;
  }
}

async function main() {
  const networkName = hre.network.name;
  const configPath = NETWORK_CONFIG_MAP[networkName];

  if (!configPath) {
    throw new Error(
      `Unknown network "${networkName}". ` +
        `Supported networks: ${Object.keys(NETWORK_CONFIG_MAP).join(", ")}`
    );
  }

  console.log("=".repeat(60));
  console.log(`  Arbiscan Verification — ${networkName}`);
  console.log("=".repeat(60));

  // Load config
  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  const deployed = config.deployed_contracts;

  if (!deployed || Object.keys(deployed).length === 0) {
    throw new Error(
      `No deployed contracts found in ${configPath}. ` +
        "Run the deploy script first."
    );
  }

  console.log(`  Config   : ${configPath}`);
  console.log(`  Deployer : ${deployed.deployer || "unknown"}`);
  console.log(`  Deployed : ${deployed.deployed_at || "unknown"}`);

  // Determine constructor arguments per contract based on network
  const tokensConfig = JSON.parse(fs.readFileSync(TOKENS_PATH, "utf-8"));
  const isMainnet = networkName === "arbitrum";

  // HalalAssetRegistry constructor: (address[] memory _blacklistedTokens)
  const blacklistedTokens = isMainnet
    ? tokensConfig.known_interest_bearing || []
    : [];

  // PriceOracle constructor: () — no arguments
  // MudarabahPool constructor: (address _halalRegistry)
  // FlashLoanArbitrage constructor: (address _aavePool, address _profitReceiver)

  const aavePoolAddress = config.contracts.aave_v3_pool;
  const profitReceiver = deployed.deployer;

  // ── Verify each contract ────────────────────────────────────────────
  const results = [];

  if (deployed.HalalAssetRegistry) {
    const ok = await verifyContract(
      "HalalAssetRegistry",
      deployed.HalalAssetRegistry,
      [blacklistedTokens]
    );
    results.push({ name: "HalalAssetRegistry", ok });
  }

  if (deployed.PriceOracle) {
    const ok = await verifyContract(
      "PriceOracle",
      deployed.PriceOracle,
      [] // no constructor arguments
    );
    results.push({ name: "PriceOracle", ok });
  }

  if (deployed.MudarabahPool) {
    const ok = await verifyContract(
      "MudarabahPool",
      deployed.MudarabahPool,
      [deployed.HalalAssetRegistry]
    );
    results.push({ name: "MudarabahPool", ok });
  }

  if (deployed.FlashLoanArbitrage) {
    const ok = await verifyContract(
      "FlashLoanArbitrage",
      deployed.FlashLoanArbitrage,
      [aavePoolAddress, profitReceiver]
    );
    results.push({ name: "FlashLoanArbitrage", ok });
  }

  // ── Summary ─────────────────────────────────────────────────────────
  const explorer = config.explorer || "https://arbiscan.io";
  const passed = results.filter((r) => r.ok).length;
  const failed = results.filter((r) => !r.ok).length;

  console.log("\n" + "=".repeat(60));
  console.log("  Verification Summary");
  console.log("=".repeat(60));

  results.forEach((r) => {
    const status = r.ok ? "OK" : "FAILED";
    const addr = deployed[r.name] || "";
    console.log(`  [${status}] ${r.name}`);
    if (addr) {
      console.log(`        ${explorer}/address/${addr}#code`);
    }
  });

  console.log("-".repeat(60));
  console.log(`  Passed: ${passed}  |  Failed: ${failed}  |  Total: ${results.length}`);
  console.log("=".repeat(60));

  if (failed > 0) {
    console.log(
      "\nSome verifications failed. Common fixes:"
    );
    console.log("  - Ensure ARBISCAN_API_KEY is set in .env");
    console.log("  - Wait a few minutes after deployment for the explorer to index the contract");
    console.log("  - Re-run this script to retry failed verifications");
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
