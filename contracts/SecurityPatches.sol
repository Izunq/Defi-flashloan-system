// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

import "./AccessControlSecurityFix.sol";

/**
 * @title SecurityPatches
 * @notice Patches for access control vulnerabilities in existing contracts
 * @dev These patches should be applied to the vulnerable contracts
 */
contract SecurityPatches {
    
    // =================
    // PATCH 1: STRATEGY PROPOSAL ACCESS CONTROL
    // =================
    
    /**
     * @dev SECURE VERSION of proposeStrategy function
     * FIXES: Missing access control in solidity_contracts_v26.sol line 221
     */
    function proposeStrategy_SECURE(
        address _strategyAddress, 
        IStrategyIncubatorV26.StrategyGenome memory _genome
    ) 
        external 
        onlyRole(STRATEGY_PROPOSER_ROLE)  // FIX: Added access control
        onlyApprovedProposer()            // FIX: Additional proposer verification
        proposalCooldown()                // FIX: Prevent spam proposals
        whenNotPaused()                   // FIX: Respect pause state
        nonReentrant()                    // FIX: Prevent reentrancy
    {
        require(strategyAddressToId[_strategyAddress] == 0, "Strategy already proposed");
        require(_strategyAddress != address(0), "Invalid strategy address");
        require(_strategyAddress.code.length > 0, "Strategy must be a contract"); // FIX: Ensure it's a contract
        
        // FIX: Validate strategy genome
        require(bytes(_genome.topology).length > 0, "Topology cannot be empty");
        require(_genome.dexTypes.length > 0, "Must specify at least one DEX type");
        
        // FIX: Rate limiting per proposer
        proposerNonce[msg.sender]++;
        require(proposerNonce[msg.sender] <= 10, "Too many proposals from this address");
        
        uint256 oldRep = proposerReputation[msg.sender];
        if (oldRep == 0 && msg.sender != owner()) {
             proposerReputation[msg.sender] = INITIAL_REPUTATION;
        }
        proposerReputation[msg.sender] += PROPOSAL_REPUTATION_GAIN;
        emit ReputationChanged(msg.sender, oldRep, proposerReputation[msg.sender], "Strategy Proposal");
        
        uint256 id = strategies.length;
        strategyAddressToId[_strategyAddress] = id + 1;

        strategies.push(IncubatedStrategy({
            strategyAddress: _strategyAddress,
            proposer: msg.sender,
            status: StrategyStatus.Proposed,
            genome: _genome,
            backtest: BacktestReport(bytes32(0), 0, 0, 0),
            totalLiveProfit: 0,
            proposedAt: block.timestamp
        }));

        if (incentivesManager != address(0)) {
            IncentivesManagerV26(incentivesManager).rewardProposer(id, msg.sender);
        }
        emit StrategyProposed(id, _strategyAddress, msg.sender, proposerReputation[msg.sender]);
        emit StrategyStatusChanged(id, StrategyStatus.Proposed, StrategyStatus.Proposed);
    }
    
    // =================
    // PATCH 2: EMERGENCY WITHDRAWAL ACCESS CONTROL
    // =================
    
    /**
     * @dev SECURE VERSION of requestEmergencyWithdrawal function
     * FIXES: Insufficient access control in MudarabahInvestmentPool.sol line 852
     */
    function requestEmergencyWithdrawal_SECURE() 
        external 
        whenPaused()                      // FIX: Only during emergency pause
        nonReentrant()                    // FIX: Prevent reentrancy
    {
        require(emergencyShutdown, "Not in emergency shutdown");
        require(investors[msg.sender].capitalInvested > 0, "No investment to withdraw");
        require(emergencyWithdrawalRequests[msg.sender] == 0, "Request already submitted");
        
        // FIX: Additional validation for emergency withdrawals
        require(
            block.timestamp >= emergencyShutdown + 1 hours, 
            "Emergency withdrawal cooling period not elapsed"
        );
        
        // FIX: Validate investor is in good standing
        require(
            !blacklistedInvestors[msg.sender], 
            "Investor is blacklisted"
        );
        
        // FIX: Check if investor has any pending violations
        require(
            investorViolations[msg.sender] == 0, 
            "Investor has pending violations"
        );
        
        emergencyWithdrawalRequests[msg.sender] = block.timestamp + emergencyWithdrawalDelay;
        
        // FIX: Log emergency withdrawal request
        emit EmergencyWithdrawalRequested(
            msg.sender, 
            investors[msg.sender].capitalInvested, 
            block.timestamp
        );
    }
    
    // =================
    // PATCH 3: ORACLE SECURITY MONITORING ACCESS CONTROL
    // =================
    
    /**
     * @dev SECURE VERSION of performSecurityMonitoring function
     * FIXES: Missing access control in OracleSecurityWrapper.sol line 239
     */
    function performSecurityMonitoring_SECURE(bytes32 assetId) 
        external 
        onlyRole(SECURITY_MANAGER_ROLE)   // FIX: Added access control
        whenNotPaused()                   // FIX: Respect pause state
        nonReentrant()                    // FIX: Prevent reentrancy
    {
        require(assetId != bytes32(0), "Invalid asset ID");
        
        // FIX: Rate limiting for security monitoring
        require(
            block.timestamp >= lastAnomalyCheck[assetId] + REAL_TIME_MONITORING_INTERVAL,
            "Monitoring interval not elapsed"
        );
        
        // FIX: Validate caller permissions for specific asset
        require(
            hasRole(ORACLE_ADMIN_ROLE, msg.sender) || 
            authorizedMonitors[assetId][msg.sender],
            "Not authorized to monitor this asset"
        );
        
        lastAnomalyCheck[assetId] = block.timestamp;
        
        // Get current price data
        (uint256 currentPrice, bool isValid) = primaryOracle.getSafePrice(assetId, 1 hours);
        require(isValid, "Invalid price data for monitoring");
        
        // FIX: Additional validation
        require(currentPrice > 0, "Price cannot be zero");
        require(currentPrice < MAX_REASONABLE_PRICE, "Price exceeds reasonable bounds");
        
        // Update price history
        _updatePriceHistory(assetId, currentPrice);
        
        // Perform anomaly detection
        bool anomalyDetected = _detectPriceAnomalies(assetId, currentPrice);
        
        if (anomalyDetected) {
            _handleAnomalyDetection(assetId, currentPrice);
            
            // FIX: Alert security team
            emit SecurityAlert(
                assetId, 
                currentPrice, 
                "Anomaly detected during monitoring", 
                AlertSeverity.HIGH,
                msg.sender,
                block.timestamp
            );
        }
        
        // Update security metrics
        _updateSecurityMetrics(assetId, currentPrice);
        
        // Check for predictive manipulation warnings
        _checkPredictiveWarnings(assetId);
        
        // FIX: Log monitoring activity
        emit SecurityMonitoringPerformed(assetId, msg.sender, currentPrice, block.timestamp);
    }
    
    // =================
    // PATCH 4: STRATEGY EXECUTION ACCESS CONTROL
    // =================
    
    /**
     * @dev SECURE VERSION for strategy execution functions
     */
    function executeStrategy_SECURE(
        bytes32 strategyId,
        address[] calldata assets,
        uint256[] calldata amounts,
        bytes[] calldata executionData,
        bytes32 aiPredictionId
    ) 
        external 
        onlyRole(STRATEGY_EXECUTOR_ROLE)  // FIX: Added access control
        nonReentrant()                    // Already present
        whenNotPaused()                   // Already present
        notEmergencyShutdown()            // Already present
        riskLimitsCheck()                 // Already present
    {
        require(approvedStrategies[strategyId], "Strategy not approved");
        require(assets.length == amounts.length, "Array length mismatch");
        require(assets.length == executionData.length, "Execution data mismatch");
        
        // FIX: Additional validation
        require(assets.length > 0 && assets.length <= 10, "Invalid number of assets");
        require(strategyId != bytes32(0), "Invalid strategy ID");
        
        // FIX: Validate executor permissions
        require(
            authorizedExecutors[msg.sender] || hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Not authorized to execute strategies"
        );
        
        // FIX: Check strategy-specific permissions
        require(
            strategyExecutors[strategyId][msg.sender] || hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Not authorized for this specific strategy"
        );
        
        // Check all assets are Halal-compliant
        for (uint256 i = 0; i < assets.length; i++) {
            require(HALAL_REGISTRY.isHalalCompliant(assets[i]), "Non-compliant asset");
            require(assets[i] != address(0), "Invalid asset address");
            require(amounts[i] > 0, "Amount must be greater than zero");
        }
        
        // Continue with existing validation and execution logic...
        _executeStrategyWithEnhancedSecurity(strategyId, assets, amounts, executionData, aiPredictionId);
    }
    
    // =================
    // PATCH 5: ADMINISTRATIVE FUNCTION PROTECTION
    // =================
    
    /**
     * @dev SECURE VERSION for administrative functions
     */
    function updateSystemConfiguration_SECURE(
        bytes32 configKey,
        uint256 configValue
    ) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE)      // FIX: Added access control
        emergencyTimelock(                // FIX: Added timelock for critical changes
            keccak256(abi.encodePacked("CONFIG_UPDATE", configKey, configValue)),
            "Configuration Update"
        )
    {
        require(configKey != bytes32(0), "Invalid config key");
        require(configValue > 0, "Config value must be positive");
        
        // FIX: Validate configuration bounds
        if (configKey == keccak256("MAX_SLIPPAGE_BPS")) {
            require(configValue <= 1000, "Slippage cannot exceed 10%");
        } else if (configKey == keccak256("EXECUTION_TIMEOUT")) {
            require(configValue >= 30 seconds && configValue <= 1 hours, "Invalid timeout");
        } else if (configKey == keccak256("MAX_GAS_PRICE")) {
            require(configValue <= 1000 gwei, "Gas price too high");
        }
        
        systemConfiguration[configKey] = configValue;
        
        emit SystemConfigurationUpdated(configKey, configValue, msg.sender, block.timestamp);
    }
    
    // =================
    // ADDITIONAL SECURITY HELPERS
    // =================
    
    event SecurityAlert(
        bytes32 indexed assetId,
        uint256 price,
        string reason,
        AlertSeverity severity,
        address triggeredBy,
        uint256 timestamp
    );
    
    event SecurityMonitoringPerformed(
        bytes32 indexed assetId,
        address indexed monitor,
        uint256 price,
        uint256 timestamp
    );
    
    event EmergencyWithdrawalRequested(
        address indexed investor,
        uint256 amount,
        uint256 timestamp
    );
    
    event SystemConfigurationUpdated(
        bytes32 indexed configKey,
        uint256 configValue,
        address updatedBy,
        uint256 timestamp
    );
}
