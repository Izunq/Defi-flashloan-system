const { expect } = require("chai");
const { ethers } = require("hardhat");
const {
  loadFixture,
} = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("FlashLoanArbitrage", function () {
  // -----------------------------------------------------------------------
  //  Fixture
  // -----------------------------------------------------------------------
  async function deployArbitrageFixture() {
    const [admin, executor, nonAdmin, profitReceiver] =
      await ethers.getSigners();

    // Deploy mock tokens
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    const tokenA = await MockERC20.deploy("Token A", "TKA", 18);
    await tokenA.waitForDeployment();
    const tokenB = await MockERC20.deploy("Token B", "TKB", 18);
    await tokenB.waitForDeployment();

    // Deploy mock Aave pool
    const MockAavePool = await ethers.getContractFactory("MockAavePool");
    const aavePool = await MockAavePool.deploy();
    await aavePool.waitForDeployment();

    // Deploy mock DEXes
    // dexA: tokenA -> tokenB at 1.02x (leg 1 earns)
    const MockDEX = await ethers.getContractFactory("MockDEX");
    const dexA = await MockDEX.deploy(10200); // 1.02x
    await dexA.waitForDeployment();
    // dexB: tokenB -> tokenA at 1.00x (leg 2 flat)
    const dexB = await MockDEX.deploy(10000); // 1.00x
    await dexB.waitForDeployment();

    // Deploy FlashLoanArbitrage
    const FlashLoanArbitrage = await ethers.getContractFactory(
      "FlashLoanArbitrage"
    );
    const arbitrage = await FlashLoanArbitrage.deploy(
      await aavePool.getAddress(),
      profitReceiver.address
    );
    await arbitrage.waitForDeployment();

    // Grant EXECUTOR_ROLE to executor
    const EXECUTOR_ROLE = await arbitrage.EXECUTOR_ROLE();
    await arbitrage.grantRole(EXECUTOR_ROLE, executor.address);

    // Fund the mock Aave pool with tokenA for flash loans
    const loanAmount = ethers.parseEther("1000");
    await tokenA.mint(await aavePool.getAddress(), loanAmount * 2n);

    // Fund dexA with tokenB (it gives out tokenB)
    await tokenB.mint(await dexA.getAddress(), ethers.parseEther("100000"));
    // Fund dexB with tokenA (it gives out tokenA)
    await tokenA.mint(await dexB.getAddress(), ethers.parseEther("100000"));

    const DEFAULT_ADMIN_ROLE = await arbitrage.DEFAULT_ADMIN_ROLE();

    return {
      arbitrage,
      aavePool,
      dexA,
      dexB,
      tokenA,
      tokenB,
      admin,
      executor,
      nonAdmin,
      profitReceiver,
      loanAmount,
      EXECUTOR_ROLE,
      DEFAULT_ADMIN_ROLE,
    };
  }

  // -----------------------------------------------------------------------
  //  Helper to encode SwapRoute params
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
  //  Deployment
  // -----------------------------------------------------------------------
  describe("Deployment", function () {
    it("should set aavePool and profitReceiver correctly", async function () {
      const { arbitrage, aavePool, profitReceiver } = await loadFixture(
        deployArbitrageFixture
      );

      expect(await arbitrage.aavePool()).to.equal(
        await aavePool.getAddress()
      );
      expect(await arbitrage.profitReceiver()).to.equal(
        profitReceiver.address
      );
    });
  });

  // -----------------------------------------------------------------------
  //  executeFlashLoan — access control
  // -----------------------------------------------------------------------
  describe("executeFlashLoan access control", function () {
    it("should revert when called by non-EXECUTOR_ROLE", async function () {
      const { arbitrage, nonAdmin, tokenA } = await loadFixture(
        deployArbitrageFixture
      );

      await expect(
        arbitrage
          .connect(nonAdmin)
          .executeFlashLoan(await tokenA.getAddress(), 1000, "0x")
      ).to.be.revertedWithCustomError(
        arbitrage,
        "AccessControlUnauthorizedAccount"
      );
    });
  });

  // -----------------------------------------------------------------------
  //  executeFlashLoan — paused
  // -----------------------------------------------------------------------
  describe("executeFlashLoan when paused", function () {
    it("should revert with EnforcedPause when contract is paused", async function () {
      const { arbitrage, admin, executor, tokenA } = await loadFixture(
        deployArbitrageFixture
      );

      await arbitrage.connect(admin).pause();

      await expect(
        arbitrage
          .connect(executor)
          .executeFlashLoan(await tokenA.getAddress(), 1000, "0x")
      ).to.be.revertedWithCustomError(arbitrage, "EnforcedPause");
    });
  });

  // -----------------------------------------------------------------------
  //  setProfitReceiver
  // -----------------------------------------------------------------------
  describe("setProfitReceiver", function () {
    it("should update profitReceiver when called by admin", async function () {
      const { arbitrage, admin, nonAdmin, profitReceiver } = await loadFixture(
        deployArbitrageFixture
      );

      // Capture the old receiver before the state-changing transaction
      const oldReceiver = profitReceiver.address;

      await expect(
        arbitrage.connect(admin).setProfitReceiver(nonAdmin.address)
      )
        .to.emit(arbitrage, "ProfitReceiverUpdated")
        .withArgs(oldReceiver, nonAdmin.address);

      expect(await arbitrage.profitReceiver()).to.equal(nonAdmin.address);
    });

    it("should revert when called by non-admin", async function () {
      const { arbitrage, nonAdmin } = await loadFixture(
        deployArbitrageFixture
      );

      await expect(
        arbitrage.connect(nonAdmin).setProfitReceiver(nonAdmin.address)
      ).to.be.revertedWithCustomError(
        arbitrage,
        "AccessControlUnauthorizedAccount"
      );
    });

    it("should revert with ZeroAddress when address(0) is passed", async function () {
      const { arbitrage, admin } = await loadFixture(deployArbitrageFixture);

      await expect(
        arbitrage.connect(admin).setProfitReceiver(ethers.ZeroAddress)
      ).to.be.revertedWithCustomError(arbitrage, "ZeroAddress");
    });
  });

  // -----------------------------------------------------------------------
  //  withdrawToken
  // -----------------------------------------------------------------------
  describe("withdrawToken", function () {
    it("should allow admin to withdraw stuck tokens", async function () {
      const { arbitrage, admin, tokenA } = await loadFixture(
        deployArbitrageFixture
      );

      // Send some tokens to the arbitrage contract
      const amount = ethers.parseEther("50");
      await tokenA.mint(await arbitrage.getAddress(), amount);

      const balBefore = await tokenA.balanceOf(admin.address);

      await expect(
        arbitrage
          .connect(admin)
          .withdrawToken(await tokenA.getAddress(), amount)
      )
        .to.emit(arbitrage, "TokenWithdrawn")
        .withArgs(await tokenA.getAddress(), amount, admin.address);

      const balAfter = await tokenA.balanceOf(admin.address);
      expect(balAfter - balBefore).to.equal(amount);
    });
  });

  // -----------------------------------------------------------------------
  //  pause / unpause
  // -----------------------------------------------------------------------
  describe("pause / unpause", function () {
    it("should allow admin to pause and unpause", async function () {
      const { arbitrage, admin } = await loadFixture(deployArbitrageFixture);

      await arbitrage.connect(admin).pause();
      expect(await arbitrage.paused()).to.equal(true);

      await arbitrage.connect(admin).unpause();
      expect(await arbitrage.paused()).to.equal(false);
    });

    it("should revert pause/unpause for non-admin", async function () {
      const { arbitrage, nonAdmin } = await loadFixture(
        deployArbitrageFixture
      );

      await expect(
        arbitrage.connect(nonAdmin).pause()
      ).to.be.revertedWithCustomError(
        arbitrage,
        "AccessControlUnauthorizedAccount"
      );

      await expect(
        arbitrage.connect(nonAdmin).unpause()
      ).to.be.revertedWithCustomError(
        arbitrage,
        "AccessControlUnauthorizedAccount"
      );
    });
  });

  // -----------------------------------------------------------------------
  //  executeOperation — unauthorized caller
  // -----------------------------------------------------------------------
  describe("executeOperation guards", function () {
    it("should revert UnauthorizedCaller when called by non-aavePool", async function () {
      const { arbitrage, nonAdmin, tokenA } = await loadFixture(
        deployArbitrageFixture
      );

      await expect(
        arbitrage
          .connect(nonAdmin)
          .executeOperation(
            await tokenA.getAddress(),
            1000,
            5,
            await arbitrage.getAddress(),
            "0x"
          )
      ).to.be.revertedWithCustomError(arbitrage, "UnauthorizedCaller");
    });

    it("should revert UnauthorizedInitiator when initiator is not self", async function () {
      const { arbitrage, aavePool, admin, tokenA } = await loadFixture(
        deployArbitrageFixture
      );

      // We need to call executeOperation from the aavePool address.
      // Since MockAavePool passes `receiver` as the initiator, we need to
      // craft a situation where the initiator differs from the contract.
      // We'll impersonate the aave pool to call executeOperation directly
      // with a wrong initiator.
      const aavePoolAddress = await aavePool.getAddress();
      const arbitrageAddress = await arbitrage.getAddress();

      await ethers.provider.send("hardhat_impersonateAccount", [
        aavePoolAddress,
      ]);
      // Fund the impersonated account with ETH for gas
      await admin.sendTransaction({
        to: aavePoolAddress,
        value: ethers.parseEther("1"),
      });
      const aaveSigner = await ethers.getSigner(aavePoolAddress);

      // Call with wrong initiator (admin instead of contract)
      await expect(
        arbitrage
          .connect(aaveSigner)
          .executeOperation(
            await tokenA.getAddress(),
            1000,
            5,
            admin.address, // wrong initiator — should be arbitrage address
            "0x"
          )
      ).to.be.revertedWithCustomError(arbitrage, "UnauthorizedInitiator");

      await ethers.provider.send("hardhat_stopImpersonatingAccount", [
        aavePoolAddress,
      ]);
    });
  });

  // -----------------------------------------------------------------------
  //  Full flash loan execution (profitable arbitrage)
  // -----------------------------------------------------------------------
  describe("Successful flash loan arbitrage", function () {
    it("should execute a profitable arbitrage and send profit to receiver", async function () {
      const {
        arbitrage,
        dexA,
        dexB,
        tokenA,
        tokenB,
        executor,
        profitReceiver,
        loanAmount,
      } = await loadFixture(deployArbitrageFixture);

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

      const receiverBalBefore = await tokenA.balanceOf(
        profitReceiver.address
      );

      await expect(
        arbitrage
          .connect(executor)
          .executeFlashLoan(await tokenA.getAddress(), loanAmount, params)
      ).to.emit(arbitrage, "FlashLoanExecuted");

      const receiverBalAfter = await tokenA.balanceOf(
        profitReceiver.address
      );

      // dexA gives 1.02x tokenB, dexB gives 1.00x tokenA back
      // So from 1000 tokenA: leg1 -> 1020 tokenB, leg2 -> 1020 tokenA
      // premium = 1000 * 5 / 10000 = 0.5 tokenA
      // profit = 1020 - 1000 - 0.5 = 19.5 tokenA
      expect(receiverBalAfter - receiverBalBefore).to.be.gt(0n);
    });
  });
});
