const { expect } = require("chai");
const { ethers } = require("hardhat");
const {
  loadFixture,
  time,
} = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("MudarabahPool", function () {
  // -----------------------------------------------------------------------
  //  Fixture
  // -----------------------------------------------------------------------
  async function deployPoolFixture() {
    const [admin, providerA, providerB, nonMudarib] =
      await ethers.getSigners();

    // Deploy mock halal registry
    const MockHalalRegistry = await ethers.getContractFactory(
      "MockHalalRegistry"
    );
    const halalRegistry = await MockHalalRegistry.deploy();
    await halalRegistry.waitForDeployment();

    // Deploy mock ERC20 token
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    const token = await MockERC20.deploy("Halal Token", "HLT", 18);
    await token.waitForDeployment();
    const nonHalalToken = await MockERC20.deploy("Haram Token", "HRM", 18);
    await nonHalalToken.waitForDeployment();

    // Mark token as halal-compliant
    await halalRegistry.setCompliant(await token.getAddress(), true);
    // nonHalalToken stays non-compliant (default false)

    // Deploy MudarabahPool
    const MudarabahPool = await ethers.getContractFactory("MudarabahPool");
    const pool = await MudarabahPool.deploy(
      await halalRegistry.getAddress()
    );
    await pool.waitForDeployment();

    // Deploy MockMudarib
    const MockMudarib = await ethers.getContractFactory("MockMudarib");
    const mockMudarib = await MockMudarib.deploy();
    await mockMudarib.waitForDeployment();

    // Grant MUDARIB_ROLE to the mockMudarib contract
    const MUDARIB_ROLE = await pool.MUDARIB_ROLE();
    await pool.grantRole(MUDARIB_ROLE, await mockMudarib.getAddress());

    const DEFAULT_ADMIN_ROLE = await pool.DEFAULT_ADMIN_ROLE();

    // Mint tokens to providers
    const depositAmount = ethers.parseEther("1000");
    await token.mint(providerA.address, depositAmount * 10n);
    await token.mint(providerB.address, depositAmount * 10n);

    // Approve pool to spend tokens on behalf of providers
    await token
      .connect(providerA)
      .approve(await pool.getAddress(), ethers.MaxUint256);
    await token
      .connect(providerB)
      .approve(await pool.getAddress(), ethers.MaxUint256);

    return {
      pool,
      halalRegistry,
      token,
      nonHalalToken,
      mockMudarib,
      admin,
      providerA,
      providerB,
      nonMudarib,
      depositAmount,
      MUDARIB_ROLE,
      DEFAULT_ADMIN_ROLE,
    };
  }

  // -----------------------------------------------------------------------
  //  Deployment
  // -----------------------------------------------------------------------
  describe("Deployment", function () {
    it("should deploy with mock HalalAssetRegistry", async function () {
      const { pool, halalRegistry } = await loadFixture(deployPoolFixture);

      expect(await pool.halalRegistry()).to.equal(
        await halalRegistry.getAddress()
      );
      expect(await pool.providerShareBps()).to.equal(7000);
      expect(await pool.mudaribShareBps()).to.equal(3000);
    });
  });

  // -----------------------------------------------------------------------
  //  deposit
  // -----------------------------------------------------------------------
  describe("deposit", function () {
    it("should issue correct shares and emit Deposit event", async function () {
      const { pool, token, providerA, depositAmount } = await loadFixture(
        deployPoolFixture
      );

      await expect(
        pool
          .connect(providerA)
          .deposit(await token.getAddress(), depositAmount)
      )
        .to.emit(pool, "Deposit")
        .withArgs(
          providerA.address,
          await token.getAddress(),
          depositAmount,
          depositAmount // first deposit: shares == amount
        );

      // Verify state
      expect(
        await pool.shares(await token.getAddress(), providerA.address)
      ).to.equal(depositAmount);
      expect(await pool.totalShares(await token.getAddress())).to.equal(
        depositAmount
      );
      expect(await pool.totalDeposited(await token.getAddress())).to.equal(
        depositAmount
      );
    });

    it("should revert for non-halal token", async function () {
      const { pool, nonHalalToken, providerA, depositAmount } =
        await loadFixture(deployPoolFixture);

      await nonHalalToken.mint(providerA.address, depositAmount);
      await nonHalalToken
        .connect(providerA)
        .approve(await pool.getAddress(), ethers.MaxUint256);

      await expect(
        pool
          .connect(providerA)
          .deposit(await nonHalalToken.getAddress(), depositAmount)
      ).to.be.revertedWithCustomError(pool, "AssetNotHalalCompliant");
    });
  });

  // -----------------------------------------------------------------------
  //  withdraw
  // -----------------------------------------------------------------------
  describe("withdraw", function () {
    it("should return correct tokens and burn shares", async function () {
      const { pool, token, providerA, depositAmount } = await loadFixture(
        deployPoolFixture
      );

      // Deposit first
      await pool
        .connect(providerA)
        .deposit(await token.getAddress(), depositAmount);

      const balBefore = await token.balanceOf(providerA.address);

      await expect(
        pool
          .connect(providerA)
          .withdraw(await token.getAddress(), depositAmount)
      )
        .to.emit(pool, "Withdrawal")
        .withArgs(
          providerA.address,
          await token.getAddress(),
          depositAmount,
          depositAmount
        );

      const balAfter = await token.balanceOf(providerA.address);
      expect(balAfter - balBefore).to.equal(depositAmount);

      // Shares should be 0
      expect(
        await pool.shares(await token.getAddress(), providerA.address)
      ).to.equal(0);
    });

    it("should revert when withdrawing more shares than balance", async function () {
      const { pool, token, providerA, depositAmount } = await loadFixture(
        deployPoolFixture
      );

      await pool
        .connect(providerA)
        .deposit(await token.getAddress(), depositAmount);

      await expect(
        pool
          .connect(providerA)
          .withdraw(await token.getAddress(), depositAmount + 1n)
      ).to.be.revertedWithCustomError(pool, "InsufficientShares");
    });
  });

  // -----------------------------------------------------------------------
  //  executeMudarabah
  // -----------------------------------------------------------------------
  describe("executeMudarabah", function () {
    it("should only be callable by MUDARIB_ROLE", async function () {
      const { pool, token, nonMudarib } = await loadFixture(
        deployPoolFixture
      );

      await expect(
        pool
          .connect(nonMudarib)
          .executeMudarabah(await token.getAddress(), 100, "0x")
      ).to.be.revertedWithCustomError(
        pool,
        "AccessControlUnauthorizedAccount"
      );
    });

    it("should revert PrincipalNotReturned if principal is not returned", async function () {
      const { pool, token, mockMudarib, providerA, admin, depositAmount } =
        await loadFixture(deployPoolFixture);

      // Provider deposits
      await pool
        .connect(providerA)
        .deposit(await token.getAddress(), depositAmount);

      const borrowAmount = ethers.parseEther("100");

      // MockMudarib will return less than borrowed (only 50 of 100)
      const returnAmount = ethers.parseEther("50");
      // Pre-fund the mudarib with tokens to return
      await token.mint(await mockMudarib.getAddress(), returnAmount);

      // Encode the call: mockMudarib.execute(token, pool, returnAmount)
      // The pool sends 100 to mudarib, mudarib returns only 50.
      // Pool balance goes from X to X - 100 + 50 = X - 50, triggering PrincipalNotReturned.
      const executeData = mockMudarib.interface.encodeFunctionData("execute", [
        await token.getAddress(),
        await pool.getAddress(),
        returnAmount,
      ]);

      // Impersonate the mockMudarib contract (it has MUDARIB_ROLE)
      const mudaribAddress = await mockMudarib.getAddress();
      await ethers.provider.send("hardhat_impersonateAccount", [
        mudaribAddress,
      ]);
      await admin.sendTransaction({
        to: mudaribAddress,
        value: ethers.parseEther("1"),
      });
      const mudaribSigner = await ethers.getSigner(mudaribAddress);

      await expect(
        pool
          .connect(mudaribSigner)
          .executeMudarabah(
            await token.getAddress(),
            borrowAmount,
            executeData
          )
      ).to.be.revertedWithCustomError(pool, "PrincipalNotReturned");

      await ethers.provider.send("hardhat_stopImpersonatingAccount", [
        mudaribAddress,
      ]);
    });

    it("should charge no fee when profit is zero", async function () {
      const { pool, token, mockMudarib, providerA, admin, depositAmount } =
        await loadFixture(deployPoolFixture);

      // Provider deposits
      await pool
        .connect(providerA)
        .deposit(await token.getAddress(), depositAmount);

      const borrowAmount = ethers.parseEther("100");

      // Pre-fund the mudarib with exactly borrowAmount so it can return
      // principal but generate zero profit.
      await token.mint(await mockMudarib.getAddress(), borrowAmount);

      // The mudarib receives borrowAmount from pool, then sends borrowAmount
      // back via execute(). Pool balance is unchanged => profit = 0.
      const executeData = mockMudarib.interface.encodeFunctionData("execute", [
        await token.getAddress(),
        await pool.getAddress(),
        borrowAmount,
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

      await expect(
        pool
          .connect(mudaribSigner)
          .executeMudarabah(
            await token.getAddress(),
            borrowAmount,
            executeData
          )
      )
        .to.emit(pool, "MudarabahExecuted")
        .withArgs(
          mudaribAddress,
          await token.getAddress(),
          borrowAmount,
          0, // profit
          0, // providerProfit
          0  // mudaribProfit
        );

      await ethers.provider.send("hardhat_stopImpersonatingAccount", [
        mudaribAddress,
      ]);
    });

    it("should split profit correctly (70/30 provider/mudarib)", async function () {
      const { pool, token, mockMudarib, providerA, admin, depositAmount } =
        await loadFixture(deployPoolFixture);

      // Provider deposits
      await pool
        .connect(providerA)
        .deposit(await token.getAddress(), depositAmount);

      const borrowAmount = ethers.parseEther("100");
      const profit = ethers.parseEther("10");
      const returnAmount = borrowAmount + profit;

      // Pre-fund the mudarib so it has enough to return principal + profit
      await token.mint(await mockMudarib.getAddress(), returnAmount);

      const executeData = mockMudarib.interface.encodeFunctionData("execute", [
        await token.getAddress(),
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

      const expectedProviderProfit = (profit * 7000n) / 10000n; // 70% = 7 ETH
      const expectedMudaribProfit = profit - expectedProviderProfit; // 30% = 3 ETH

      const mudaribBalBefore = await token.balanceOf(mudaribAddress);

      await expect(
        pool
          .connect(mudaribSigner)
          .executeMudarabah(
            await token.getAddress(),
            borrowAmount,
            executeData
          )
      )
        .to.emit(pool, "MudarabahExecuted")
        .withArgs(
          mudaribAddress,
          await token.getAddress(),
          borrowAmount,
          profit,
          expectedProviderProfit,
          expectedMudaribProfit
        );

      // Verify the mudarib's final balance.
      // Flow: mudarib starts with returnAmount (pre-funded). During the tx it
      // receives borrowAmount from pool, returns returnAmount via execute(),
      // then receives mudaribProfit from pool.
      // Final = returnAmount + borrowAmount - returnAmount + mudaribProfit
      //       = borrowAmount + mudaribProfit
      const mudaribBalAfter = await token.balanceOf(mudaribAddress);
      expect(mudaribBalAfter).to.equal(
        borrowAmount + expectedMudaribProfit
      );

      await ethers.provider.send("hardhat_stopImpersonatingAccount", [
        mudaribAddress,
      ]);
    });
  });

  // -----------------------------------------------------------------------
  //  claimProfit
  // -----------------------------------------------------------------------
  describe("claimProfit", function () {
    it("should allow provider to claim accumulated profit after mudarabah", async function () {
      const { pool, token, mockMudarib, providerA, admin, depositAmount } =
        await loadFixture(deployPoolFixture);

      // Provider deposits
      await pool
        .connect(providerA)
        .deposit(await token.getAddress(), depositAmount);

      // Execute a profitable mudarabah
      const borrowAmount = ethers.parseEther("100");
      const profit = ethers.parseEther("10");
      const returnAmount = borrowAmount + profit;
      await token.mint(await mockMudarib.getAddress(), returnAmount);

      const executeData = mockMudarib.interface.encodeFunctionData("execute", [
        await token.getAddress(),
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

      await pool
        .connect(mudaribSigner)
        .executeMudarabah(
          await token.getAddress(),
          borrowAmount,
          executeData
        );

      await ethers.provider.send("hardhat_stopImpersonatingAccount", [
        mudaribAddress,
      ]);

      // Provider claims profit (70% of 10 = 7)
      const expectedProviderProfit = (profit * 7000n) / 10000n;
      const balBefore = await token.balanceOf(providerA.address);

      await expect(
        pool.connect(providerA).claimProfit(await token.getAddress())
      )
        .to.emit(pool, "ProfitClaimed")
        .withArgs(
          providerA.address,
          await token.getAddress(),
          expectedProviderProfit
        );

      const balAfter = await token.balanceOf(providerA.address);
      expect(balAfter - balBefore).to.equal(expectedProviderProfit);
    });
  });

  // -----------------------------------------------------------------------
  //  Multiple providers — proportional profit
  // -----------------------------------------------------------------------
  describe("Multiple providers", function () {
    it("should distribute profit proportionally to share holdings", async function () {
      const {
        pool,
        token,
        mockMudarib,
        providerA,
        providerB,
        admin,
      } = await loadFixture(deployPoolFixture);

      const amountA = ethers.parseEther("700");
      const amountB = ethers.parseEther("300");

      // Both providers deposit (A = 70%, B = 30%)
      await pool
        .connect(providerA)
        .deposit(await token.getAddress(), amountA);
      await pool
        .connect(providerB)
        .deposit(await token.getAddress(), amountB);

      // Execute a profitable mudarabah
      const borrowAmount = ethers.parseEther("100");
      const profit = ethers.parseEther("10");
      const returnAmount = borrowAmount + profit;
      await token.mint(await mockMudarib.getAddress(), returnAmount);

      const executeData = mockMudarib.interface.encodeFunctionData("execute", [
        await token.getAddress(),
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

      await pool
        .connect(mudaribSigner)
        .executeMudarabah(
          await token.getAddress(),
          borrowAmount,
          executeData
        );

      await ethers.provider.send("hardhat_stopImpersonatingAccount", [
        mudaribAddress,
      ]);

      // Provider profit = 70% of 10 = 7 ETH total for all providers
      const totalProviderProfit = (profit * 7000n) / 10000n;

      // ProviderA holds 70% of shares -> gets 70% of providerProfit
      // ProviderB holds 30% of shares -> gets 30% of providerProfit
      const expectedA =
        (totalProviderProfit * amountA) / (amountA + amountB);
      const expectedB =
        (totalProviderProfit * amountB) / (amountA + amountB);

      // Claim for providerA
      const balBeforeA = await token.balanceOf(providerA.address);
      await pool.connect(providerA).claimProfit(await token.getAddress());
      const balAfterA = await token.balanceOf(providerA.address);

      // Claim for providerB
      const balBeforeB = await token.balanceOf(providerB.address);
      await pool.connect(providerB).claimProfit(await token.getAddress());
      const balAfterB = await token.balanceOf(providerB.address);

      const claimedA = balAfterA - balBeforeA;
      const claimedB = balAfterB - balBeforeB;

      // Allow for rounding (within 1 wei)
      expect(claimedA).to.be.closeTo(expectedA, 1);
      expect(claimedB).to.be.closeTo(expectedB, 1);

      // Total claimed should equal total provider profit (within rounding)
      expect(claimedA + claimedB).to.be.closeTo(totalProviderProfit, 2);
    });
  });

  // -----------------------------------------------------------------------
  //  proposeRatioChange + applyRatioChange with timelock
  // -----------------------------------------------------------------------
  describe("proposeRatioChange / applyRatioChange", function () {
    it("should propose and apply a ratio change after timelock", async function () {
      const { pool, admin } = await loadFixture(deployPoolFixture);

      // Propose 60/40
      await expect(pool.connect(admin).proposeRatioChange(6000, 4000))
        .to.emit(pool, "RatioChangeProposed");

      // Attempt to apply before timelock
      await expect(pool.applyRatioChange()).to.be.revertedWithCustomError(
        pool,
        "TimelockNotExpired"
      );

      // Advance time past the 24-hour timelock
      await time.increase(24 * 60 * 60 + 1);

      await expect(pool.applyRatioChange())
        .to.emit(pool, "RatioChangeApplied")
        .withArgs(6000, 4000);

      expect(await pool.providerShareBps()).to.equal(6000);
      expect(await pool.mudaribShareBps()).to.equal(4000);
    });

    it("should revert applyRatioChange when no change is pending", async function () {
      const { pool } = await loadFixture(deployPoolFixture);

      await expect(pool.applyRatioChange()).to.be.revertedWithCustomError(
        pool,
        "NoRatioChangePending"
      );
    });

    it("should revert proposeRatioChange when ratios do not sum to 10000", async function () {
      const { pool, admin } = await loadFixture(deployPoolFixture);

      await expect(
        pool.connect(admin).proposeRatioChange(5000, 4000)
      ).to.be.revertedWithCustomError(pool, "InvalidRatio");
    });
  });

  // -----------------------------------------------------------------------
  //  pause / unpause
  // -----------------------------------------------------------------------
  describe("pause / unpause", function () {
    it("should allow admin to pause and unpause", async function () {
      const { pool, admin } = await loadFixture(deployPoolFixture);

      await pool.connect(admin).pause();
      expect(await pool.paused()).to.equal(true);

      await pool.connect(admin).unpause();
      expect(await pool.paused()).to.equal(false);
    });

    it("should block deposits when paused", async function () {
      const { pool, admin, token, providerA, depositAmount } =
        await loadFixture(deployPoolFixture);

      await pool.connect(admin).pause();

      await expect(
        pool
          .connect(providerA)
          .deposit(await token.getAddress(), depositAmount)
      ).to.be.revertedWithCustomError(pool, "EnforcedPause");
    });

    it("should revert pause for non-admin", async function () {
      const { pool, providerA } = await loadFixture(deployPoolFixture);

      await expect(
        pool.connect(providerA).pause()
      ).to.be.revertedWithCustomError(
        pool,
        "AccessControlUnauthorizedAccount"
      );
    });
  });
});
