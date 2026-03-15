const { expect } = require("chai");
const { ethers } = require("hardhat");
const {
  loadFixture,
  time,
} = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("PriceOracle", function () {
  // -----------------------------------------------------------------------
  //  Fixture
  // -----------------------------------------------------------------------
  async function deployOracleFixture() {
    const [admin, manager, unauthorized, base, quote] =
      await ethers.getSigners();

    // Deploy PriceOracle
    const PriceOracle = await ethers.getContractFactory("PriceOracle");
    const oracle = await PriceOracle.deploy();
    await oracle.waitForDeployment();

    // Grant ORACLE_MANAGER_ROLE to manager
    const ORACLE_MANAGER_ROLE = await oracle.ORACLE_MANAGER_ROLE();
    await oracle.grantRole(ORACLE_MANAGER_ROLE, manager.address);

    // Deploy several MockAggregator instances
    const MockAggregator = await ethers.getContractFactory("MockAggregator");

    const feed1 = await MockAggregator.deploy(100000000000n); // $1000.00000000
    await feed1.waitForDeployment();

    const feed2 = await MockAggregator.deploy(100100000000n); // $1001.00000000
    await feed2.waitForDeployment();

    const feed3 = await MockAggregator.deploy(100200000000n); // $1002.00000000
    await feed3.waitForDeployment();

    return {
      oracle,
      admin,
      manager,
      unauthorized,
      base,
      quote,
      feed1,
      feed2,
      feed3,
      MockAggregator,
      ORACLE_MANAGER_ROLE,
    };
  }

  // -----------------------------------------------------------------------
  //  Deployment & feed management
  // -----------------------------------------------------------------------
  describe("Deployment and feed management", function () {
    it("should deploy and allow ORACLE_MANAGER_ROLE to add feeds", async function () {
      const { oracle, manager, base, quote, feed1 } = await loadFixture(
        deployOracleFixture
      );

      await expect(
        oracle
          .connect(manager)
          .addFeed(base.address, quote.address, await feed1.getAddress())
      )
        .to.emit(oracle, "FeedAdded")
        .withArgs(base.address, quote.address, await feed1.getAddress());
    });

    it("should revert when unauthorized account tries to add a feed", async function () {
      const { oracle, unauthorized, base, quote, feed1 } = await loadFixture(
        deployOracleFixture
      );

      await expect(
        oracle
          .connect(unauthorized)
          .addFeed(base.address, quote.address, await feed1.getAddress())
      ).to.be.revertedWithCustomError(
        oracle,
        "AccessControlUnauthorizedAccount"
      );
    });
  });

  // -----------------------------------------------------------------------
  //  getPrice — single feed
  // -----------------------------------------------------------------------
  describe("getPrice with single valid feed", function () {
    it("should return correct price from one feed", async function () {
      const { oracle, manager, base, quote, feed1 } = await loadFixture(
        deployOracleFixture
      );

      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed1.getAddress());

      const [price, decimals] = await oracle.getPrice(
        base.address,
        quote.address
      );

      expect(price).to.equal(100000000000n); // $1000 with 8 decimals
      expect(decimals).to.equal(8);
    });
  });

  // -----------------------------------------------------------------------
  //  getPrice — stale feed
  // -----------------------------------------------------------------------
  describe("getPrice with stale feed", function () {
    it("should revert NoPriceAvailable when the only feed is stale", async function () {
      const { oracle, manager, base, quote, feed1 } = await loadFixture(
        deployOracleFixture
      );

      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed1.getAddress());

      // Make the feed stale (set updatedAt to 0, which is far in the past)
      await feed1.setStale(0);

      await expect(
        oracle.getPrice(base.address, quote.address)
      ).to.be.revertedWithCustomError(oracle, "NoPriceAvailable");
    });

    it("should revert NoPriceAvailable when ALL feeds are stale", async function () {
      const { oracle, manager, base, quote, feed1, feed2, feed3 } =
        await loadFixture(deployOracleFixture);

      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed1.getAddress());
      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed2.getAddress());
      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed3.getAddress());

      // Make all feeds stale
      await feed1.setStale(0);
      await feed2.setStale(0);
      await feed3.setStale(0);

      await expect(
        oracle.getPrice(base.address, quote.address)
      ).to.be.revertedWithCustomError(oracle, "NoPriceAvailable");
    });
  });

  // -----------------------------------------------------------------------
  //  getPrice — multiple feeds / median
  // -----------------------------------------------------------------------
  describe("getPrice with multiple feeds — median", function () {
    it("should return the median of 3 feeds", async function () {
      const { oracle, manager, base, quote, feed1, feed2, feed3 } =
        await loadFixture(deployOracleFixture);

      // Prices: 1000, 1001, 1002 (in 8 dec).  Median = 1001
      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed1.getAddress());
      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed2.getAddress());
      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed3.getAddress());

      const [price] = await oracle.getPrice(base.address, quote.address);
      // Median of [100000000000, 100100000000, 100200000000] = 100100000000
      expect(price).to.equal(100100000000n);
    });

    it("should return the correct median with 5 feeds", async function () {
      const { oracle, manager, base, quote, MockAggregator } =
        await loadFixture(deployOracleFixture);

      // Deploy 5 feeds with prices: 990, 995, 1000, 1005, 1010
      const prices = [
        99000000000n,
        99500000000n,
        100000000000n,
        100500000000n,
        101000000000n,
      ];

      for (const p of prices) {
        const feed = await MockAggregator.deploy(p);
        await feed.waitForDeployment();
        await oracle
          .connect(manager)
          .addFeed(base.address, quote.address, await feed.getAddress());
      }

      const [price] = await oracle.getPrice(base.address, quote.address);
      // Sorted: [99000000000, 99500000000, 100000000000, 100500000000, 101000000000]
      // Median (odd length 5) = element at index 2 = 100000000000
      expect(price).to.equal(100000000000n);
    });
  });

  // -----------------------------------------------------------------------
  //  Deviation check
  // -----------------------------------------------------------------------
  describe("Deviation check", function () {
    it("should revert PriceDeviationTooHigh when feeds disagree by >5%", async function () {
      const { oracle, manager, base, quote, MockAggregator } =
        await loadFixture(deployOracleFixture);

      // Feed A = $1000, Feed B = $1060 → deviation = 6%
      const feedLow = await MockAggregator.deploy(100000000000n);
      await feedLow.waitForDeployment();
      const feedHigh = await MockAggregator.deploy(106000000000n);
      await feedHigh.waitForDeployment();

      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feedLow.getAddress());
      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feedHigh.getAddress());

      await expect(
        oracle.getPrice(base.address, quote.address)
      ).to.be.revertedWithCustomError(oracle, "PriceDeviationTooHigh");
    });
  });

  // -----------------------------------------------------------------------
  //  removeFeed
  // -----------------------------------------------------------------------
  describe("removeFeed", function () {
    it("should remove a feed and emit FeedRemoved", async function () {
      const { oracle, manager, base, quote, feed1, feed2 } = await loadFixture(
        deployOracleFixture
      );

      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed1.getAddress());
      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed2.getAddress());

      await expect(
        oracle
          .connect(manager)
          .removeFeed(base.address, quote.address, await feed1.getAddress())
      )
        .to.emit(oracle, "FeedRemoved")
        .withArgs(base.address, quote.address, await feed1.getAddress());

      // After removal, only feed2 is left — price should be feed2's price
      const [price] = await oracle.getPrice(base.address, quote.address);
      expect(price).to.equal(100100000000n);
    });

    it("should revert InvalidFeed when removing a non-existent feed", async function () {
      const { oracle, manager, base, quote, feed1 } = await loadFixture(
        deployOracleFixture
      );

      await expect(
        oracle
          .connect(manager)
          .removeFeed(base.address, quote.address, await feed1.getAddress())
      ).to.be.revertedWithCustomError(oracle, "InvalidFeed");
    });
  });

  // -----------------------------------------------------------------------
  //  setStalenessThreshold
  // -----------------------------------------------------------------------
  describe("setStalenessThreshold", function () {
    it("should update the staleness window and emit event", async function () {
      const { oracle, manager, base, quote, feed1 } = await loadFixture(
        deployOracleFixture
      );

      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feed1.getAddress());

      // Set a very short staleness of 10 seconds
      await expect(
        oracle
          .connect(manager)
          .setStalenessThreshold(base.address, quote.address, 10)
      )
        .to.emit(oracle, "StalenessThresholdUpdated")
        .withArgs(base.address, quote.address, 10);

      // Advance time by 11 seconds so the feed becomes stale
      await time.increase(11);

      await expect(
        oracle.getPrice(base.address, quote.address)
      ).to.be.revertedWithCustomError(oracle, "NoPriceAvailable");
    });
  });

  // -----------------------------------------------------------------------
  //  setMaxDeviation
  // -----------------------------------------------------------------------
  describe("setMaxDeviation", function () {
    it("should update the max deviation and emit event", async function () {
      const { oracle, manager, base, quote, MockAggregator } =
        await loadFixture(deployOracleFixture);

      // Two feeds with 3% spread — under default 5% but over 2%
      const feedA = await MockAggregator.deploy(100000000000n); // $1000
      await feedA.waitForDeployment();
      const feedB = await MockAggregator.deploy(103000000000n); // $1030  (3%)
      await feedB.waitForDeployment();

      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feedA.getAddress());
      await oracle
        .connect(manager)
        .addFeed(base.address, quote.address, await feedB.getAddress());

      // Should succeed with default 5% max deviation
      await oracle.getPrice(base.address, quote.address);

      // Set max deviation to 2% (200 bps)
      await expect(
        oracle
          .connect(manager)
          .setMaxDeviation(base.address, quote.address, 200)
      )
        .to.emit(oracle, "MaxDeviationUpdated")
        .withArgs(base.address, quote.address, 200);

      // Now the 3% spread should revert
      await expect(
        oracle.getPrice(base.address, quote.address)
      ).to.be.revertedWithCustomError(oracle, "PriceDeviationTooHigh");
    });
  });
});
