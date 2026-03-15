const { expect } = require("chai");
const { ethers } = require("hardhat");
const {
  loadFixture,
} = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("Integration: Full Arbitrage Flow", function () {
  // -----------------------------------------------------------------------
  //  Fixture — deploy all contracts together with mocks
  // -----------------------------------------------------------------------
  async function deployFullSystemFixture() {
    const [admin, executor, providerA, providerB] =
      await ethers.getSigners();

    // ── Mock Tokens ───────────────────────────────────────────────────────
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    const tokenA = await MockERC20.deploy("USDC Mock", "USDC", 6);
    await tokenA.waitForDeployment();
    const tokenB = await MockERC20.deploy("WETH Mock", "WETH", 18);
    await tokenB.waitForDeployment();

    // ── HalalAssetRegistry ────────────────────────────────────────────────
    const HalalAssetRegistry = await ethers.getContractFactory(
      "HalalAssetRegistry"
    );
    const registry = await HalalAssetRegistry.deploy([]); // no pre-blacklisted
    await registry.waitForDeployment();

    // Approve tokenA as halal
    await registry.approveAsset(
      await tokenA.getAddress(),
      "USDC Mock",
      "Stablecoin backed by fiat"
    );
    // Approve tokenB as halal
    await registry.approveAsset(
      await tokenB.getAddress(),
      "WETH Mock",
      "Wrapped Ether"
    );

    // ── PriceOracle ───────────────────────────────────────────────────────
    const PriceOracle = await ethers.getContractFactory("PriceOracle");
    const oracle = await PriceOracle.deploy();
    await oracle.waitForDeployment();

    // Deploy mock price feed for tokenA/tokenB pair
    const MockAggregator = await ethers.getContractFactory("MockAggregator");
    const feed = await MockAggregator.deploy(200000000000n); // $2000 with 8 dec
    await feed.waitForDeployment();

    await oracle.addFeed(
      await tokenA.getAddress(),
      await tokenB.getAddress(),
      await feed.getAddress()
    );

    // ── Mock Aave Pool ────────────────────────────────────────────────────
    const MockAavePool = await ethers.getContractFactory("MockAavePool");
    const aavePool = await MockAavePool.deploy();
    await aavePool.waitForDeployment();

    // ── Mock DEXes ────────────────────────────────────────────────────────
    const MockDEX = await ethers.getContractFactory("MockDEX");
    // dexA: tokenA -> tokenB at 1.03x (profitable leg 1)
    const dexA = await MockDEX.deploy(10300);
    await dexA.waitForDeployment();
    // dexB: tokenB -> tokenA at 1.00x (flat leg 2)
    const dexB = await MockDEX.deploy(10000);
    await dexB.waitForDeployment();

    // ── FlashLoanArbitrage ────────────────────────────────────────────────
    const FlashLoanArbitrage = await ethers.getContractFactory(
      "FlashLoanArbitrage"
    );
    const arbitrage = await FlashLoanArbitrage.deploy(
      await aavePool.getAddress(),
      admin.address // profit goes to admin in this test
    );
    await arbitrage.waitForDeployment();

    const EXECUTOR_ROLE = await arbitrage.EXECUTOR_ROLE();
    await arbitrage.grantRole(EXECUTOR_ROLE, executor.address);

    // ── MudarabahPool ─────────────────────────────────────────────────────
    const MudarabahPool = await ethers.getContractFactory("MudarabahPool");
    const pool = await MudarabahPool.deploy(await registry.getAddress());
    await pool.waitForDeployment();

    // Deploy MockMudarib
    const MockMudarib = await ethers.getContractFactory("MockMudarib");
    const mockMudarib = await MockMudarib.deploy();
    await mockMudarib.waitForDeployment();

    const MUDARIB_ROLE = await pool.MUDARIB_ROLE();
    await pool.grantRole(MUDARIB_ROLE, await mockMudarib.getAddress());

    // ── Fund everything ───────────────────────────────────────────────────
    const loanAmount = 1000_000000n; // 1000 USDC (6 decimals)

    // Fund Aave pool
    await tokenA.mint(await aavePool.getAddress(), loanAmount * 10n);

    // Fund DEXes
    await tokenB.mint(await dexA.getAddress(), ethers.parseEther("100000"));
    await tokenA.mint(await dexB.getAddress(), loanAmount * 100n);

    // Fund providers
    await tokenA.mint(providerA.address, loanAmount * 5n);
    await tokenA.mint(providerB.address, loanAmount * 5n);

    // Approve pool spending
    await tokenA
      .connect(providerA)
      .approve(await pool.getAddress(), ethers.MaxUint256);
    await tokenA
      .connect(providerB)
      .approve(await pool.getAddress(), ethers.MaxUint256);

    return {
      tokenA,
      tokenB,
      registry,
      oracle,
      feed,
      aavePool,
      dexA,
      dexB,
      arbitrage,
      pool,
      mockMudarib,
      admin,
      executor,
      providerA,
      providerB,
      loanAmount,
      EXECUTOR_ROLE,
      MUDARIB_ROLE,
    };
  }

  // -----------------------------------------------------------------------
  //  Helper to encode SwapRoute
  // -----------------------------------------------------------------------
  function encodeSwapRoute(route) {
    return ethers.AbiCoder.defaultAbiCoder().encode(
      [
        "tuple(address dexA, address dexB, address tokenOut, uint24 feeA, uint24 feeB, uint256 amountOutMinA, uint256 amountOutMinB)",
      ],
      [route]
    );
  }

  // -----------------------------------------------------------------------
  //  Tests
  // -----------------------------------------------------------------------

  it("should register a token as halal and verify compliance", async function () {
    const { registry, tokenA } = await loadFixture(deployFullSystemFixture);

    expect(await registry.isHalalCompliant(await tokenA.getAddress())).to.equal(
      true
    );
    expect(await registry.isBlacklisted(await tokenA.getAddress())).to.equal(
      false
    );
  });

  it("should return a valid price from the oracle", async function () {
    const { oracle, tokenA, tokenB } = await loadFixture(
      deployFullSystemFixture
    );

    const [price, decimals] = await oracle.getPrice(
      await tokenA.getAddress(),
      await tokenB.getAddress()
    );
    expect(price).to.equal(200000000000n);
    expect(decimals).to.equal(8);
  });

  it("should execute a profitable flash loan end-to-end", async function () {
    const {
      arbitrage,
      dexA,
      dexB,
      tokenA,
      tokenB,
      executor,
      admin,
      loanAmount,
    } = await loadFixture(deployFullSystemFixture);

    const route = {
      dexA: await dexA.getAddress(),
      dexB: await dexB.getAddress(),
      tokenOut: await tokenB.getAddress(),
      feeA: 3000,
      feeB: 3000,
      amountOutMinA: 0,
      amountOutMinB: 0,
    };
    const params = encodeSwapRoute(route);

    const adminBalBefore = await tokenA.balanceOf(admin.address);

    await expect(
      arbitrage
        .connect(executor)
        .executeFlashLoan(await tokenA.getAddress(), loanAmount, params)
    ).to.emit(arbitrage, "FlashLoanExecuted");

    const adminBalAfter = await tokenA.balanceOf(admin.address);
    const profit = adminBalAfter - adminBalBefore;

    // With 1.03x on leg1 and 1.00x on leg2:
    // leg1: 1000 USDC -> 1030 (tokenB units, scaled by USDC decimals in mock)
    // leg2: 1030 -> 1030 USDC
    // premium: 1000 * 5 / 10000 = 0.5 USDC
    // profit: 1030 - 1000 - 0.5 = 29.5 USDC
    expect(profit).to.be.gt(0n);
  });

  it("should deposit into MudarabahPool, execute mudarabah, and verify profit split", async function () {
    const {
      pool,
      token: _,
      tokenA,
      mockMudarib,
      providerA,
      providerB,
      admin,
      loanAmount,
    } = await loadFixture(deployFullSystemFixture);

    // ── Providers deposit ─────────────────────────────────────────────────
    const depositA = loanAmount * 3n; // 3000 USDC
    const depositB = loanAmount * 2n; // 2000 USDC

    await pool
      .connect(providerA)
      .deposit(await tokenA.getAddress(), depositA);
    await pool
      .connect(providerB)
      .deposit(await tokenA.getAddress(), depositB);

    expect(
      await pool.totalDeposited(await tokenA.getAddress())
    ).to.equal(depositA + depositB);

    // ── Execute mudarabah with profit ─────────────────────────────────────
    const borrowAmount = loanAmount; // 1000 USDC
    const tradeProfit = 100_000000n; // 100 USDC profit
    const returnAmount = borrowAmount + tradeProfit;

    await tokenA.mint(await mockMudarib.getAddress(), returnAmount);

    const executeData = mockMudarib.interface.encodeFunctionData("execute", [
      await tokenA.getAddress(),
      await pool.getAddress(),
      returnAmount,
    ]);

    const mudaribAddress = await mockMudarib.getAddress();
    await ethers.provider.send("hardhat_impersonateAccount", [
      mudaribAddress,
    ]);
    await admin.sendTransaction({
      to: mudaribAddress,
      value: ethers.parseEther("1"),
    });
    const mudaribSigner = await ethers.getSigner(mudaribAddress);

    const expectedProviderProfit = (tradeProfit * 7000n) / 10000n; // 70 USDC
    const expectedMudaribProfit = tradeProfit - expectedProviderProfit; // 30 USDC

    await expect(
      pool
        .connect(mudaribSigner)
        .executeMudarabah(
          await tokenA.getAddress(),
          borrowAmount,
          executeData
        )
    )
      .to.emit(pool, "MudarabahExecuted")
      .withArgs(
        mudaribAddress,
        await tokenA.getAddress(),
        borrowAmount,
        tradeProfit,
        expectedProviderProfit,
        expectedMudaribProfit
      );

    await ethers.provider.send("hardhat_stopImpersonatingAccount", [
      mudaribAddress,
    ]);

    // ── Verify proportional profit distribution ───────────────────────────
    // ProviderA has 60% of shares (3000 out of 5000)
    // ProviderB has 40% of shares (2000 out of 5000)
    const expectedA =
      (expectedProviderProfit * depositA) / (depositA + depositB);
    const expectedB =
      (expectedProviderProfit * depositB) / (depositA + depositB);

    const balBeforeA = await tokenA.balanceOf(providerA.address);
    await pool.connect(providerA).claimProfit(await tokenA.getAddress());
    const balAfterA = await tokenA.balanceOf(providerA.address);

    const balBeforeB = await tokenA.balanceOf(providerB.address);
    await pool.connect(providerB).claimProfit(await tokenA.getAddress());
    const balAfterB = await tokenA.balanceOf(providerB.address);

    const claimedA = balAfterA - balBeforeA;
    const claimedB = balAfterB - balBeforeB;

    expect(claimedA).to.be.closeTo(expectedA, 1);
    expect(claimedB).to.be.closeTo(expectedB, 1);

    // Total claimed approximates total provider profit
    expect(claimedA + claimedB).to.be.closeTo(expectedProviderProfit, 2);
  });

  it("should integrate all contracts: registry check before flash loan and pool deposit", async function () {
    const {
      registry,
      oracle,
      arbitrage,
      pool,
      tokenA,
      tokenB,
      dexA,
      dexB,
      executor,
      providerA,
      admin,
      loanAmount,
    } = await loadFixture(deployFullSystemFixture);

    // 1. Verify registry compliance
    expect(
      await registry.isHalalCompliant(await tokenA.getAddress())
    ).to.equal(true);

    // 2. Verify oracle price is fresh
    const [price, decimals] = await oracle.getPrice(
      await tokenA.getAddress(),
      await tokenB.getAddress()
    );
    expect(price).to.be.gt(0n);

    // 3. Provider deposits into pool
    await pool
      .connect(providerA)
      .deposit(await tokenA.getAddress(), loanAmount * 2n);
    expect(
      await pool.shares(await tokenA.getAddress(), providerA.address)
    ).to.equal(loanAmount * 2n);

    // 4. Execute flash loan arbitrage
    const route = {
      dexA: await dexA.getAddress(),
      dexB: await dexB.getAddress(),
      tokenOut: await tokenB.getAddress(),
      feeA: 3000,
      feeB: 3000,
      amountOutMinA: 0,
      amountOutMinB: 0,
    };
    const params = encodeSwapRoute(route);

    const adminBalBefore = await tokenA.balanceOf(admin.address);
    await arbitrage
      .connect(executor)
      .executeFlashLoan(await tokenA.getAddress(), loanAmount, params);
    const adminBalAfter = await tokenA.balanceOf(admin.address);

    expect(adminBalAfter).to.be.gt(adminBalBefore);

    // 5. Provider can still withdraw from pool
    const shares = await pool.shares(
      await tokenA.getAddress(),
      providerA.address
    );
    const providerBalBefore = await tokenA.balanceOf(providerA.address);
    await pool
      .connect(providerA)
      .withdraw(await tokenA.getAddress(), shares);
    const providerBalAfter = await tokenA.balanceOf(providerA.address);

    expect(providerBalAfter).to.be.gt(providerBalBefore);
  });
});
