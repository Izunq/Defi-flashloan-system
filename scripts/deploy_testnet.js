const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 Deploying Testnet Halal Arbitrage System...");
    
    // Get deployer account
    const [deployer] = await ethers.getSigners();
    console.log("📮 Deploying from account:", deployer.address);
    
    // Check balance
    const balance = await deployer.getBalance();
    console.log("💰 Account balance:", ethers.utils.formatEther(balance), "ETH");
    
    if (balance.eq(0)) {
        console.log("❌ No testnet ETH! Get some from faucets:");
        console.log("   • Mumbai: https://faucet.polygon.technology/");
        console.log("   • Arbitrum Goerli: https://bridge.arbitrum.io/");
        console.log("   • Optimism Goerli: https://app.optimism.io/faucet");
        return;
    }
    
    // Deploy the contract
    console.log("📦 Deploying TestnetHalalArbitrage...");
    const TestnetHalalArbitrage = await ethers.getContractFactory("TestnetHalalArbitrage");
    
    const arbitrage = await TestnetHalalArbitrage.deploy({
        gasLimit: 2000000,
        gasPrice: ethers.utils.parseUnits("1", "gwei") // 1 gwei for testnet
    });
    
    await arbitrage.deployed();
    
    console.log("✅ TestnetHalalArbitrage deployed to:", arbitrage.address);
    console.log("🔗 Network:", network.name);
    console.log("⛽ Gas used for deployment:", (await arbitrage.deployTransaction.wait()).gasUsed.toString());
    
    // Save deployment info
    const deploymentInfo = {
        network: network.name,
        contractAddress: arbitrage.address,
        deployerAddress: deployer.address,
        deploymentHash: arbitrage.deployTransaction.hash,
        timestamp: new Date().toISOString(),
        gasUsed: (await arbitrage.deployTransaction.wait()).gasUsed.toString()
    };
    
    console.log("\n📄 Deployment Summary:");
    console.log(JSON.stringify(deploymentInfo, null, 2));
    
    // Verify basic functionality
    console.log("\n🧪 Testing basic functionality...");
    const stats = await arbitrage.getTradingStats();
    console.log("📊 Initial stats:", {
        totalTrades: stats.totalTrades.toString(),
        totalProfit: stats.totalProfit.toString(),
        myProfit: stats.myProfit.toString()
    });
    
    console.log("\n🎉 Deployment complete!");
    console.log("💡 Ready for 24-hour testnet trading session");
    
    // Explorer links
    const explorerUrls = {
        mumbai: `https://mumbai.polygonscan.com/address/${arbitrage.address}`,
        arbitrumGoerli: `https://goerli.arbiscan.io/address/${arbitrage.address}`,
        optimismGoerli: `https://goerli-optimism.etherscan.io/address/${arbitrage.address}`
    };
    
    if (explorerUrls[network.name]) {
        console.log("🔍 View on explorer:", explorerUrls[network.name]);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
