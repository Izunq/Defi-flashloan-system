const { expect } = require("chai");
const { ethers } = require("hardhat");
const {
  loadFixture,
} = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("HalalAssetRegistry", function () {
  // -----------------------------------------------------------------------
  //  Fixture
  // -----------------------------------------------------------------------
  async function deployRegistryFixture() {
    const [admin, committee, nonCommittee, tokenA, tokenB, blacklistedToken] =
      await ethers.getSigners();

    const HalalAssetRegistry = await ethers.getContractFactory(
      "HalalAssetRegistry"
    );
    // Deploy with one pre-blacklisted address
    const registry = await HalalAssetRegistry.deploy([
      blacklistedToken.address,
    ]);
    await registry.waitForDeployment();

    // Grant SHARIAH_COMMITTEE_ROLE to the committee signer
    const SHARIAH_COMMITTEE_ROLE = await registry.SHARIAH_COMMITTEE_ROLE();
    await registry.grantRole(SHARIAH_COMMITTEE_ROLE, committee.address);

    return {
      registry,
      admin,
      committee,
      nonCommittee,
      tokenA,
      tokenB,
      blacklistedToken,
      SHARIAH_COMMITTEE_ROLE,
    };
  }

  // -----------------------------------------------------------------------
  //  Deployment
  // -----------------------------------------------------------------------
  describe("Deployment", function () {
    it("should deploy with pre-blacklisted tokens", async function () {
      const { registry, blacklistedToken } = await loadFixture(
        deployRegistryFixture
      );

      expect(await registry.isBlacklisted(blacklistedToken.address)).to.equal(
        true
      );
      expect(
        await registry.isHalalCompliant(blacklistedToken.address)
      ).to.equal(false);
    });
  });

  // -----------------------------------------------------------------------
  //  approveAsset
  // -----------------------------------------------------------------------
  describe("approveAsset", function () {
    it("should allow SHARIAH_COMMITTEE_ROLE to approve an asset", async function () {
      const { registry, committee, tokenA } = await loadFixture(
        deployRegistryFixture
      );

      await expect(
        registry
          .connect(committee)
          .approveAsset(tokenA.address, "Token A", "Sharia compliant equity")
      )
        .to.emit(registry, "AssetApproved")
        .withArgs(tokenA.address, "Token A", "Sharia compliant equity");

      expect(await registry.isHalalCompliant(tokenA.address)).to.equal(true);
    });

    it("should revert when called by non-committee member", async function () {
      const { registry, nonCommittee, tokenA } = await loadFixture(
        deployRegistryFixture
      );

      await expect(
        registry
          .connect(nonCommittee)
          .approveAsset(tokenA.address, "Token A", "reason")
      ).to.be.revertedWithCustomError(
        registry,
        "AccessControlUnauthorizedAccount"
      );
    });
  });

  // -----------------------------------------------------------------------
  //  revokeAsset
  // -----------------------------------------------------------------------
  describe("revokeAsset", function () {
    it("should revoke a previously approved asset", async function () {
      const { registry, committee, tokenA } = await loadFixture(
        deployRegistryFixture
      );

      // Approve first
      await registry
        .connect(committee)
        .approveAsset(tokenA.address, "Token A", "reason");
      expect(await registry.isHalalCompliant(tokenA.address)).to.equal(true);

      // Revoke
      await expect(registry.connect(committee).revokeAsset(tokenA.address))
        .to.emit(registry, "AssetRevoked")
        .withArgs(tokenA.address);

      expect(await registry.isHalalCompliant(tokenA.address)).to.equal(false);
    });
  });

  // -----------------------------------------------------------------------
  //  blacklistAsset
  // -----------------------------------------------------------------------
  describe("blacklistAsset", function () {
    it("should set blacklisted=true and approved=false", async function () {
      const { registry, committee, tokenA } = await loadFixture(
        deployRegistryFixture
      );

      // Approve first, then blacklist
      await registry
        .connect(committee)
        .approveAsset(tokenA.address, "Token A", "reason");

      await expect(
        registry
          .connect(committee)
          .blacklistAsset(tokenA.address, "Interest-bearing token")
      )
        .to.emit(registry, "AssetBlacklisted")
        .withArgs(tokenA.address, "Interest-bearing token");

      expect(await registry.isBlacklisted(tokenA.address)).to.equal(true);
      expect(await registry.isHalalCompliant(tokenA.address)).to.equal(false);
    });

    it("should not allow approving a blacklisted asset", async function () {
      const { registry, committee, blacklistedToken } = await loadFixture(
        deployRegistryFixture
      );

      await expect(
        registry
          .connect(committee)
          .approveAsset(blacklistedToken.address, "BL Token", "attempt")
      )
        .to.be.revertedWithCustomError(registry, "AssetIsBlacklisted")
        .withArgs(blacklistedToken.address);
    });
  });

  // -----------------------------------------------------------------------
  //  removeBlacklist
  // -----------------------------------------------------------------------
  describe("removeBlacklist", function () {
    it("should remove blacklist flag but NOT auto-approve", async function () {
      const { registry, committee, blacklistedToken } = await loadFixture(
        deployRegistryFixture
      );

      await expect(
        registry.connect(committee).removeBlacklist(blacklistedToken.address)
      )
        .to.emit(registry, "BlacklistRemoved")
        .withArgs(blacklistedToken.address);

      // No longer blacklisted
      expect(
        await registry.isBlacklisted(blacklistedToken.address)
      ).to.equal(false);
      // But NOT auto-approved
      expect(
        await registry.isHalalCompliant(blacklistedToken.address)
      ).to.equal(false);
    });
  });

  // -----------------------------------------------------------------------
  //  isHalalCompliant
  // -----------------------------------------------------------------------
  describe("isHalalCompliant", function () {
    it("should return true only when approved AND not blacklisted", async function () {
      const { registry, committee, tokenA } = await loadFixture(
        deployRegistryFixture
      );

      // Not approved yet
      expect(await registry.isHalalCompliant(tokenA.address)).to.equal(false);

      // Approve
      await registry
        .connect(committee)
        .approveAsset(tokenA.address, "Token A", "reason");
      expect(await registry.isHalalCompliant(tokenA.address)).to.equal(true);

      // Blacklist -> false even though approved flag was set
      await registry
        .connect(committee)
        .blacklistAsset(tokenA.address, "reason");
      expect(await registry.isHalalCompliant(tokenA.address)).to.equal(false);
    });
  });

  // -----------------------------------------------------------------------
  //  getAssetInfo
  // -----------------------------------------------------------------------
  describe("getAssetInfo", function () {
    it("should return the full struct for a registered asset", async function () {
      const { registry, committee, tokenA } = await loadFixture(
        deployRegistryFixture
      );

      await registry
        .connect(committee)
        .approveAsset(tokenA.address, "Token A", "Equity-backed stablecoin");

      const info = await registry.getAssetInfo(tokenA.address);

      expect(info.name).to.equal("Token A");
      expect(info.approvalReason).to.equal("Equity-backed stablecoin");
      expect(info.reviewTimestamp).to.be.gt(0);
      expect(info.approved).to.equal(true);
      expect(info.blacklisted).to.equal(false);
    });

    it("should return correct info for a pre-blacklisted token", async function () {
      const { registry, blacklistedToken } = await loadFixture(
        deployRegistryFixture
      );

      const info = await registry.getAssetInfo(blacklistedToken.address);

      expect(info.approved).to.equal(false);
      expect(info.blacklisted).to.equal(true);
      expect(info.reviewTimestamp).to.be.gt(0);
    });
  });
});
