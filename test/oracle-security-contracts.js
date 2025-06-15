const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Oracle Security Contracts", function () {
  // Test variables
  let secureMultiOracle;
  let oracleSecurityWrapper;
  let oracleManipulationMonitor;
  let preCognitiveOracle;
  let owner;
  let oracle1;
  let oracle2;
  let oracle3;
  let oracle4;
  let oracle5;
  let user;
  let emergencyAdmin;
  let monitorAdmin;

  // Price IDs
  const ETH_USD_ID = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("ETH"));
  const BTC_USD_ID = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("BTC"));
  const USDC_USD_ID = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("USDC"));

  // Constants
  const ORACLE_ROLE = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("ORACLE_ROLE"));
  const ADMIN_ROLE = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("ADMIN_ROLE"));
  const EMERGENCY_ROLE = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("EMERGENCY_ROLE"));
  const MONITOR_ADMIN_ROLE = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("MONITOR_ADMIN_ROLE"));
  const ALERT_MANAGER_ROLE = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("ALERT_MANAGER_ROLE"));
  const RESPONSE_TEAM_ROLE = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("RESPONSE_TEAM_ROLE"));

  // Helper functions
  const toWei = (value) => ethers.utils.parseEther(value.toString());
  const fromWei = (value) => ethers.utils.formatEther(value);
  const toBytes32 = (str) => ethers.utils.formatBytes32String(str);
  const getCurrentTime = async () => {
    const blockNum = await ethers.provider.getBlockNumber();
    const block = await ethers.provider.getBlock(blockNum);
    return block.timestamp;
  };

  beforeEach(async function () {
    // Get signers
    [owner, oracle1, oracle2, oracle3, oracle4, oracle5, user, emergencyAdmin, monitorAdmin] = await ethers.getSigners();

    // Deploy PreCognitiveOracle first (dependency for OracleSecurityWrapper)
    const PreCognitiveOracle = await ethers.getContractFactory("PreCognitiveOracle");
    preCognitiveOracle = await PreCognitiveOracle.deploy(owner.address);
    await preCognitiveOracle.deployed();

    // Deploy SecureMultiOracle
    const SecureMultiOracle = await ethers.getContractFactory("SecureMultiOracle");
    secureMultiOracle = await SecureMultiOracle.deploy(owner.address);
    await secureMultiOracle.deployed();

    // Deploy OracleSecurityWrapper
    const OracleSecurityWrapper = await ethers.getContractFactory("OracleSecurityWrapper");
    oracleSecurityWrapper = await OracleSecurityWrapper.deploy(
      secureMultiOracle.address,
      preCognitiveOracle.address,
      owner.address
    );
    await oracleSecurityWrapper.deployed();

    // Deploy OracleManipulationMonitor
    const OracleManipulationMonitor = await ethers.getContractFactory("OracleManipulationMonitor");
    oracleManipulationMonitor = await OracleManipulationMonitor.deploy(
      secureMultiOracle.address,
      oracleSecurityWrapper.address,
      owner.address
    );
    await oracleManipulationMonitor.deployed();

    // Setup oracles
    await secureMultiOracle.addOracle(oracle1.address, 20, "Chainlink");
    await secureMultiOracle.addOracle(oracle2.address, 20, "Band Protocol");
    await secureMultiOracle.addOracle(oracle3.address, 20, "API3");
    await secureMultiOracle.addOracle(oracle4.address, 20, "Tellor");
    await secureMultiOracle.addOracle(oracle5.address, 20, "DIA");

    // Grant roles
    await secureMultiOracle.grantRole(EMERGENCY_ROLE, emergencyAdmin.address);
    await oracleManipulationMonitor.grantRole(MONITOR_ADMIN_ROLE, monitorAdmin.address);
    await oracleManipulationMonitor.grantRole(ALERT_MANAGER_ROLE, monitorAdmin.address);
    await oracleManipulationMonitor.grantRole(RESPONSE_TEAM_ROLE, emergencyAdmin.address);
  });

  describe("SecureMultiOracle", function () {
    it("Should initialize with correct settings", async function () {
      expect(await secureMultiOracle.hasRole(ADMIN_ROLE, owner.address)).to.be.true;
      expect(await secureMultiOracle.hasRole(EMERGENCY_ROLE, emergencyAdmin.address)).to.be.true;
      expect(await secureMultiOracle.totalOracleWeight()).to.equal(100); // 5 oracles with weight 20 each
    });

    it("Should allow oracles to submit prices", async function () {
      // Oracle 1 submits ETH price
      await secureMultiOracle.connect(oracle1).submitPrice(
        ETH_USD_ID,
        toWei(1500), // $1500
        95 // 95% confidence
      );

      // Oracle 2 submits ETH price
      await secureMultiOracle.connect(oracle2).submitPrice(
        ETH_USD_ID,
        toWei(1505), // $1505
        90 // 90% confidence
      );

      // Oracle 3 submits ETH price
      await secureMultiOracle.connect(oracle3).submitPrice(
        ETH_USD_ID,
        toWei(1495), // $1495
        92 // 92% confidence
      );

      // Get consensus price
      const priceData = await secureMultiOracle.consensusPrices(ETH_USD_ID);
      
      // Calculate expected consensus price (weighted average)
      // (1500*20 + 1505*20 + 1495*20) / (20+20+20) = 1500
      const expectedPrice = toWei(1500);
      
      // Allow for small rounding differences
      expect(priceData.consensusPrice).to.be.closeTo(expectedPrice, toWei(0.1));
      expect(priceData.isValid).to.be.true;
    });

    it("Should detect price deviations", async function () {
      // First set of normal prices
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1500), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1505), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1495), 92);
      
      // Get consensus price
      const priceData = await secureMultiOracle.consensusPrices(ETH_USD_ID);
      
      // Now oracle4 submits a significantly deviated price (11% higher)
      // This should trigger the circuit breaker
      await expect(
        secureMultiOracle.connect(oracle4).submitPrice(ETH_USD_ID, toWei(1665), 95)
      ).to.be.revertedWithCustomError(secureMultiOracle, "ExcessivePriceDeviation");
      
      // Check that circuit breaker is active
      expect(await secureMultiOracle.circuitBreakerActive(ETH_USD_ID)).to.be.true;
    });

    it("Should allow resetting circuit breakers", async function () {
      // First set of normal prices
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1500), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1505), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1495), 92);
      
      // Trigger circuit breaker with large deviation
      await expect(
        secureMultiOracle.connect(oracle4).submitPrice(ETH_USD_ID, toWei(1665), 95)
      ).to.be.revertedWithCustomError(secureMultiOracle, "ExcessivePriceDeviation");
      
      // Verify circuit breaker is active
      expect(await secureMultiOracle.circuitBreakerActive(ETH_USD_ID)).to.be.true;
      
      // Reset circuit breaker
      await secureMultiOracle.connect(emergencyAdmin).resetCircuitBreaker(ETH_USD_ID);
      
      // Verify circuit breaker is reset
      expect(await secureMultiOracle.circuitBreakerActive(ETH_USD_ID)).to.be.false;
    });

    it("Should enforce minimum oracle consensus", async function () {
      // Only one oracle submits price - should not be enough for consensus
      await secureMultiOracle.connect(oracle1).submitPrice(BTC_USD_ID, toWei(30000), 95);
      
      // Try to get price - should fail due to insufficient oracles
      await expect(
        secureMultiOracle.getPrice(BTC_USD_ID)
      ).to.be.revertedWithCustomError(secureMultiOracle, "InsufficientOracles");
    });
  });

  describe("OracleSecurityWrapper", function () {
    beforeEach(async function () {
      // Setup initial prices for testing
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1500), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1505), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1495), 92);
      
      await secureMultiOracle.connect(oracle1).submitPrice(BTC_USD_ID, toWei(30000), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(BTC_USD_ID, toWei(30100), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(BTC_USD_ID, toWei(29900), 92);
    });

    it("Should provide validated price data", async function () {
      // Get validated price
      const validationResult = await oracleSecurityWrapper.getValidatedPrice(ETH_USD_ID);
      
      // Verify validation result
      expect(validationResult.isValid).to.be.true;
      expect(validationResult.consensusPrice).to.be.closeTo(toWei(1500), toWei(0.1));
    });

    it("Should detect anomalies during security monitoring", async function () {
      // Authorize monitor admin for the asset
      await oracleSecurityWrapper.authorizeMonitor(ETH_USD_ID, monitorAdmin.address);
      
      // Perform initial security monitoring
      await oracleSecurityWrapper.connect(monitorAdmin).performSecurityMonitoring(ETH_USD_ID);
      
      // Now simulate a price spike by having oracles submit higher prices
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1650), 95); // 10% increase
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1655), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1645), 92);
      
      // Perform security monitoring again - should detect the anomaly
      // We'll check for the AnomalyDetected event
      await expect(
        oracleSecurityWrapper.connect(monitorAdmin).performSecurityMonitoring(ETH_USD_ID)
      ).to.emit(oracleSecurityWrapper, "AnomalyDetected");
      
      // Check that anomaly is recorded in state
      const anomalyData = await oracleSecurityWrapper.anomalyData(ETH_USD_ID);
      expect(anomalyData.anomalyDetected).to.be.true;
    });

    it("Should activate security mode for critical issues", async function () {
      // Grant security manager role to monitorAdmin
      await oracleSecurityWrapper.grantRole(
        ethers.utils.keccak256(ethers.utils.toUtf8Bytes("SECURITY_MANAGER_ROLE")),
        monitorAdmin.address
      );
      
      // Activate security mode
      await expect(
        oracleSecurityWrapper.connect(monitorAdmin).activateSecurityMode("Critical security threat detected")
      ).to.emit(oracleSecurityWrapper, "SecurityModeActivated");
      
      // Verify security mode is active
      expect(await oracleSecurityWrapper.globalSecurityMode()).to.be.true;
      
      // Validated price should now return invalid
      const validationResult = await oracleSecurityWrapper.getValidatedPrice(ETH_USD_ID);
      expect(validationResult.isValid).to.be.false;
    });
  });

  describe("OracleManipulationMonitor", function () {
    beforeEach(async function () {
      // Setup initial prices for testing
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1500), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1505), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1495), 92);
    });

    it("Should perform monitoring checks", async function () {
      // Perform monitoring check
      await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID);
      
      // Verify monitoring data was updated
      const monitoringData = await oracleManipulationMonitor.assetMonitoring(ETH_USD_ID);
      expect(monitoringData.lastUpdate).to.be.gt(0);
    });

    it("Should generate alerts for price manipulation", async function () {
      // First perform normal monitoring
      await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID);
      
      // Now simulate price manipulation
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1650), 95); // 10% increase
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1655), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1645), 92);
      
      // Perform monitoring check - should generate alert
      await expect(
        oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID)
      ).to.emit(oracleManipulationMonitor, "ManipulationAlert");
      
      // Check alert history
      const alertCount = await oracleManipulationMonitor.assetMonitoring(ETH_USD_ID);
      expect(alertCount.alertCount).to.be.gt(0);
    });

    it("Should execute automated responses for critical issues", async function () {
      // First perform normal monitoring
      await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID);
      
      // Now simulate extreme price manipulation
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1800), 95); // 20% increase
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1805), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1795), 92);
      
      // This should trigger critical status and automated response
      await expect(
        oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID)
      ).to.emit(oracleManipulationMonitor, "AutomatedResponseExecuted");
    });

    it("Should allow acknowledging and resolving alerts", async function () {
      // First generate an alert
      await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID);
      
      // Simulate price manipulation
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1650), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1655), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1645), 92);
      
      // Generate alert
      await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID);
      
      // Get the alert ID from events
      const filter = oracleManipulationMonitor.filters.ManipulationAlert(null, ETH_USD_ID);
      const events = await oracleManipulationMonitor.queryFilter(filter);
      const alertId = events[0].args.alertId;
      
      // Acknowledge alert
      await expect(
        oracleManipulationMonitor.connect(emergencyAdmin).acknowledgeAlert(alertId)
      ).to.emit(oracleManipulationMonitor, "AlertAcknowledged");
      
      // Resolve alert
      await expect(
        oracleManipulationMonitor.connect(emergencyAdmin).resolveAlert(alertId, "Price returned to normal range")
      ).to.emit(oracleManipulationMonitor, "AlertResolved");
    });
  });

  describe("Integration Tests", function () {
    beforeEach(async function () {
      // Setup initial prices for testing
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1500), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1505), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1495), 92);
    });

    it("Should detect and respond to flash loan attack pattern", async function () {
      // Authorize monitor admin for the asset
      await oracleSecurityWrapper.authorizeMonitor(ETH_USD_ID, monitorAdmin.address);
      
      // Perform initial security monitoring
      await oracleSecurityWrapper.connect(monitorAdmin).performSecurityMonitoring(ETH_USD_ID);
      await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID);
      
      // Simulate flash loan attack - sudden large price spike
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1800), 95); // 20% spike
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1805), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1795), 92);
      
      // Security wrapper should detect anomaly
      await expect(
        oracleSecurityWrapper.connect(monitorAdmin).performSecurityMonitoring(ETH_USD_ID)
      ).to.emit(oracleSecurityWrapper, "AnomalyDetected");
      
      // Manipulation monitor should generate alert
      await expect(
        oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID)
      ).to.emit(oracleManipulationMonitor, "ManipulationAlert");
      
      // Simulate price returning to normal
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1510), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1515), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1505), 92);
      
      // Security monitoring should still show anomaly
      const anomalyData = await oracleSecurityWrapper.anomalyData(ETH_USD_ID);
      expect(anomalyData.anomalyDetected).to.be.true;
    });

    it("Should handle coordinated oracle manipulation", async function () {
      // Authorize monitor admin for the asset
      await oracleSecurityWrapper.authorizeMonitor(ETH_USD_ID, monitorAdmin.address);
      
      // Perform initial security monitoring
      await oracleSecurityWrapper.connect(monitorAdmin).performSecurityMonitoring(ETH_USD_ID);
      await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID);
      
      // Simulate coordinated manipulation - multiple oracles report similar incorrect prices
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1650), 95); // 10% increase
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1655), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1645), 92);
      
      // Only oracle4 reports correct price
      await secureMultiOracle.connect(oracle4).submitPrice(ETH_USD_ID, toWei(1505), 95);
      
      // Security wrapper should detect anomaly
      await expect(
        oracleSecurityWrapper.connect(monitorAdmin).performSecurityMonitoring(ETH_USD_ID)
      ).to.emit(oracleSecurityWrapper, "AnomalyDetected");
      
      // Manipulation monitor should generate alert
      await expect(
        oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID)
      ).to.emit(oracleManipulationMonitor, "ManipulationAlert");
      
      // Check that the consensus price is affected by the manipulation
      const priceData = await secureMultiOracle.consensusPrices(ETH_USD_ID);
      expect(Number(fromWei(priceData.consensusPrice))).to.be.closeTo(1650, 50);
    });

    it("Should activate emergency protocol for system-wide issues", async function () {
      // Perform system monitoring
      await oracleManipulationMonitor.connect(monitorAdmin).performSystemMonitoring();
      
      // Simulate multiple assets being manipulated
      // ETH manipulation
      await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(1800), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(1805), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(1795), 92);
      
      // BTC manipulation
      await secureMultiOracle.connect(oracle1).submitPrice(BTC_USD_ID, toWei(36000), 95);
      await secureMultiOracle.connect(oracle2).submitPrice(BTC_USD_ID, toWei(36100), 90);
      await secureMultiOracle.connect(oracle3).submitPrice(BTC_USD_ID, toWei(35900), 92);
      
      // Authorize monitor admin for both assets
      await oracleSecurityWrapper.authorizeMonitor(ETH_USD_ID, monitorAdmin.address);
      await oracleSecurityWrapper.authorizeMonitor(BTC_USD_ID, monitorAdmin.address);
      
      // Perform security monitoring on both assets
      await oracleSecurityWrapper.connect(monitorAdmin).performSecurityMonitoring(ETH_USD_ID);
      await oracleSecurityWrapper.connect(monitorAdmin).performSecurityMonitoring(BTC_USD_ID);
      
      // Perform monitoring checks on both assets
      await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(ETH_USD_ID);
      await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(BTC_USD_ID);
      
      // System monitoring should activate emergency protocol
      await expect(
        oracleManipulationMonitor.connect(monitorAdmin).performSystemMonitoring()
      ).to.emit(oracleManipulationMonitor, "EmergencyProtocolActivated");
      
      // Verify emergency protocol is active
      expect(await oracleManipulationMonitor.emergencyProtocolActive()).to.be.true;
    });
  });

  describe("Stress Tests", function () {
    it("Should handle high frequency price updates", async function () {
      // Submit many prices in rapid succession
      for (let i = 0; i < 10; i++) {
        const price = 1500 + i;
        await secureMultiOracle.connect(oracle1).submitPrice(ETH_USD_ID, toWei(price), 95);
        await secureMultiOracle.connect(oracle2).submitPrice(ETH_USD_ID, toWei(price + 5), 90);
        await secureMultiOracle.connect(oracle3).submitPrice(ETH_USD_ID, toWei(price - 5), 92);
      }
      
      // Verify the system handled all updates
      const priceData = await secureMultiOracle.consensusPrices(ETH_USD_ID);
      expect(Number(fromWei(priceData.consensusPrice))).to.be.closeTo(1509, 1);
    });

    it("Should handle multiple assets simultaneously", async function () {
      // Setup multiple assets
      const assets = [ETH_USD_ID, BTC_USD_ID, USDC_USD_ID];
      const baseValues = [1500, 30000, 1];
      
      // Submit prices for all assets
      for (let i = 0; i < assets.length; i++) {
        const assetId = assets[i];
        const baseValue = baseValues[i];
        
        await secureMultiOracle.connect(oracle1).submitPrice(assetId, toWei(baseValue), 95);
        await secureMultiOracle.connect(oracle2).submitPrice(assetId, toWei(baseValue * 1.01), 90);
        await secureMultiOracle.connect(oracle3).submitPrice(assetId, toWei(baseValue * 0.99), 92);
      }
      
      // Authorize monitor admin for all assets
      for (let assetId of assets) {
        await oracleSecurityWrapper.authorizeMonitor(assetId, monitorAdmin.address);
      }
      
      // Perform security monitoring on all assets
      for (let assetId of assets) {
        await oracleSecurityWrapper.connect(monitorAdmin).performSecurityMonitoring(assetId);
        await oracleManipulationMonitor.connect(monitorAdmin).performMonitoringCheck(assetId);
      }
      
      // Verify all assets have monitoring data
      for (let i = 0; i < assets.length; i++) {
        const monitoringData = await oracleManipulationMonitor.assetMonitoring(assets[i]);
        expect(monitoringData.lastUpdate).to.be.gt(0);
      }
    });
  });
});