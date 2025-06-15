// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./PreCognitiveOracle.sol";

/**
 * @title EventDrivenStrategy
 * @notice A strategy that executes based on event probabilities from the Pre-Cognitive Oracle
 * @dev Part of the V42 Pre-Cognitive Oracle & Causality Engine architecture
 */
contract EventDrivenStrategy is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;
    
    // Oracle reference
    PreCognitiveOracle public immutable ORACLE;
    
    // Strategy configuration
    struct StrategyConfig {
        bytes32 targetEventTypeId;
        bytes32 targetHorizonId;
        uint256 triggerProbability;  // In basis points (0-10000)
        uint256 triggerConfidence;   // In basis points (0-10000)
        bool isActive;
    }
    
    StrategyConfig public config;
    
    // Strategy execution state
    struct ExecutionState {
        bool isExecuting;
        uint256 lastCheckTime;
        uint256 lastExecutionTime;
        uint256 executionCount;
        uint256 successCount;
        int256 totalProfitLoss;
    }
    
    ExecutionState public state;
    
    // Assets managed by the strategy
    struct AssetConfig {
        address tokenAddress;
        uint256 allocation;  // In basis points (0-10000)
        bool isActive;
    }
    
    mapping(uint256 => AssetConfig) public assets;
    uint256 public assetCount;
    
    // Events
    event StrategyConfigured(
        bytes32 indexed targetEventTypeId,
        bytes32 indexed targetHorizonId,
        uint256 triggerProbability,
        uint256 triggerConfidence,
        uint256 timestamp
    );
    
    event AssetConfigured(
        uint256 indexed assetId,
        address tokenAddress,
        uint256 allocation,
        bool isActive,
        uint256 timestamp
    );
    
    event StrategyTriggered(
        bytes32 indexed eventTypeId,
        bytes32 indexed probabilityId,
        uint256 probability,
        uint256 confidence,
        uint256 timestamp
    );
    
    event StrategyExecuted(
        bool success,
        int256 profitLoss,
        uint256 timestamp
    );
    
    /**
     * @dev Constructor
     * @param _oracleAddress Address of the Pre-Cognitive Oracle
     */
    constructor(address _oracleAddress) Ownable(msg.sender) {
        require(_oracleAddress != address(0), "Invalid oracle address");
        
        ORACLE = PreCognitiveOracle(_oracleAddress);
        
        // Initialize state
        state.lastCheckTime = block.timestamp;
    }
    
    /**
     * @dev Configure the strategy
     * @param _targetEventTypeId Target event type ID
     * @param _targetHorizonId Target time horizon ID
     * @param _triggerProbability Probability threshold to trigger the strategy
     * @param _triggerConfidence Confidence threshold to trigger the strategy
     * @param _isActive Whether the strategy is active
     */
    function configureStrategy(
        bytes32 _targetEventTypeId,
        bytes32 _targetHorizonId,
        uint256 _triggerProbability,
        uint256 _triggerConfidence,
        bool _isActive
    ) external onlyOwner {
        require(_triggerProbability <= 10000, "Probability cannot exceed 10000 basis points");
        require(_triggerConfidence <= 10000, "Confidence cannot exceed 10000 basis points");
        
        config = StrategyConfig({
            targetEventTypeId: _targetEventTypeId,
            targetHorizonId: _targetHorizonId,
            triggerProbability: _triggerProbability,
            triggerConfidence: _triggerConfidence,
            isActive: _isActive
        });
        
        emit StrategyConfigured(
            _targetEventTypeId,
            _targetHorizonId,
            _triggerProbability,
            _triggerConfidence,
            block.timestamp
        );
    }
    
    /**
     * @dev Configure an asset
     * @param _assetId Asset ID
     * @param _tokenAddress Token address
     * @param _allocation Allocation in basis points
     * @param _isActive Whether the asset is active
     */
    function configureAsset(
        uint256 _assetId,
        address _tokenAddress,
        uint256 _allocation,
        bool _isActive
    ) external onlyOwner {
        require(_tokenAddress != address(0), "Invalid token address");
        require(_allocation <= 10000, "Allocation cannot exceed 10000 basis points");
        
        assets[_assetId] = AssetConfig({
            tokenAddress: _tokenAddress,
            allocation: _allocation,
            isActive: _isActive
        });
        
        if (_assetId >= assetCount) {
            assetCount = _assetId + 1;
        }
        
        emit AssetConfigured(
            _assetId,
            _tokenAddress,
            _allocation,
            _isActive,
            block.timestamp
        );
    }
    
    /**
     * @dev Check if the strategy should be triggered
     * @return shouldTrigger Whether the strategy should be triggered
     * @return probabilityId ID of the probability that triggered the strategy
     * @return probability Current probability
     * @return confidence Current confidence
     */
    function checkTrigger() public view returns (
        bool shouldTrigger,
        bytes32 probabilityId,
        uint256 probability,
        uint256 confidence
    ) {
        if (!config.isActive) {
            return (false, bytes32(0), 0, 0);
        }
        
        // Get latest probability from oracle
        (
            probabilityId,
            probability,
            confidence,
            ,  // timestamp
            // expirationTime
        ) = ORACLE.getLatestProbability(config.targetEventTypeId, config.targetHorizonId);
        
        if (probabilityId == bytes32(0)) {
            return (false, bytes32(0), 0, 0);
        }
        
        // Check if probability and confidence exceed thresholds
        shouldTrigger = (
            probability >= config.triggerProbability &&
            confidence >= config.triggerConfidence
        );
        
        return (shouldTrigger, probabilityId, probability, confidence);
    }
    
    /**
     * @dev Execute the strategy
     * @return success Whether the execution was successful
     * @return profitLoss Profit or loss from the execution
     */
    function execute() external nonReentrant returns (bool success, int256 profitLoss) {
        require(config.isActive, "Strategy not active");
        require(!state.isExecuting, "Already executing");
        
        // Check if strategy should be triggered
        (
            bool shouldTrigger,
            bytes32 probabilityId,
            uint256 probability,
            uint256 confidence
        ) = checkTrigger();
        
        require(shouldTrigger, "Trigger conditions not met");
        
        // Set executing state
        state.isExecuting = true;
        state.lastCheckTime = block.timestamp;
        
        // Emit trigger event
        emit StrategyTriggered(
            config.targetEventTypeId,
            probabilityId,
            probability,
            confidence,
            block.timestamp
        );
        
        // Execute strategy logic
        (success, profitLoss) = _executeStrategyLogic();
        
        // Update state
        state.isExecuting = false;
        state.lastExecutionTime = block.timestamp;
        state.executionCount += 1;
        
        if (success) {
            state.successCount += 1;
            state.totalProfitLoss += profitLoss;
        }
        
        // Emit execution event
        emit StrategyExecuted(
            success,
            profitLoss,
            block.timestamp
        );
        
        return (success, profitLoss);
    }
    
    /**
     * @dev Internal function to execute strategy logic
     * @return success Whether the execution was successful
     * @return profitLoss Profit or loss from the execution
     */
    function _executeStrategyLogic() internal virtual returns (bool success, int256 profitLoss) {
        // This is a placeholder implementation
        // In a real strategy, this would contain the actual trading logic
        
        // For example, if the probability of a regulatory change is high,
        // the strategy might move funds from centralized stablecoins to
        // decentralized alternatives
        
        // Simulate a successful execution with some profit
        success = true;
        profitLoss = 1000000000000000000;  // 1 ETH worth of profit
        
        return (success, profitLoss);
    }
    
    /**
     * @dev Deposit tokens into the strategy
     * @param _tokenAddress Address of the token to deposit
     * @param _amount Amount to deposit
     */
    function deposit(address _tokenAddress, uint256 _amount) external onlyOwner {
        require(_tokenAddress != address(0), "Invalid token address");
        require(_amount > 0, "Amount must be greater than zero");
        
        // Transfer tokens from sender to contract
        IERC20(_tokenAddress).safeTransferFrom(msg.sender, address(this), _amount);
    }
    
    /**
     * @dev Withdraw tokens from the strategy
     * @param _tokenAddress Address of the token to withdraw
     * @param _amount Amount to withdraw
     * @param _recipient Recipient address
     */
    function withdraw(
        address _tokenAddress,
        uint256 _amount,
        address _recipient
    ) external onlyOwner {
        require(_tokenAddress != address(0), "Invalid token address");
        require(_amount > 0, "Amount must be greater than zero");
        require(_recipient != address(0), "Invalid recipient address");
        
        // Transfer tokens to recipient
        IERC20(_tokenAddress).safeTransfer(_recipient, _amount);
    }
    
    /**
     * @dev Get strategy status
     * @return isActive Whether the strategy is active
     * @return executionCount Number of executions
     * @return successCount Number of successful executions
     * @return totalProfitLoss Total profit or loss
     * @return lastExecutionTime Timestamp of the last execution
     */
    function getStatus() external view returns (
        bool isActive,
        uint256 executionCount,
        uint256 successCount,
        int256 totalProfitLoss,
        uint256 lastExecutionTime
    ) {
        return (
            config.isActive,
            state.executionCount,
            state.successCount,
            state.totalProfitLoss,
            state.lastExecutionTime
        );
    }
    
    /**
     * @dev Receive ETH
     */
    receive() external payable {}
    
    /**
     * @dev Rescue ETH from the contract
     * @param _amount Amount to rescue
     * @param _recipient Recipient address
     */
    function rescueETH(uint256 _amount, address payable _recipient) external onlyOwner {
        require(_recipient != address(0), "Invalid recipient address");
        require(_amount <= address(this).balance, "Insufficient balance");
        
        (bool success, ) = _recipient.call{value: _amount}("");
        require(success, "ETH transfer failed");
    }
    
    /**
     * @dev Rescue tokens from the contract
     * @param _tokenAddress Address of the token to rescue
     * @param _amount Amount to rescue
     * @param _recipient Recipient address
     */
    function rescueTokens(
        address _tokenAddress,
        uint256 _amount,
        address _recipient
    ) external onlyOwner {
        require(_tokenAddress != address(0), "Invalid token address");
        require(_recipient != address(0), "Invalid recipient address");
        
        IERC20(_tokenAddress).safeTransfer(_recipient, _amount);
    }
}