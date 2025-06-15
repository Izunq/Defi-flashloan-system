// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "./TrustCurve.sol";
import "./interfaces/IGenericStrategy.sol";
import "./interfaces/IZKVerifier.sol";

/**
 * @title AIStrategyV35
 * @notice Advanced AI-driven strategy that adjusts its risk parameters based on trust scores
 * @dev Part of the V35 Cognitive Kernel (Proof-Aware) architecture with enhanced security
 */
contract AIStrategyV35 is Ownable, ReentrancyGuard, Pausable, IGenericStrategy {
    using SafeERC20 for IERC20;
    using ECDSA for bytes32;

    // Trust curve contract for strategy scoring
    TrustCurve public immutable TRUST_CURVE;
    
    // ZK Verifier contract
    IZKVerifier public immutable ZK_VERIFIER;
    
    // Strategy identification
    uint256 public immutable strategyId;
    string public name;
    string public description;
    
    // Risk parameters (adjustable based on trust score)
    struct RiskParameters {
        uint256 maxCapitalAtRisk;     // Maximum capital that can be used (basis points of total)
        uint256 minProfitThreshold;   // Minimum profit required to execute (basis points)
        uint256 maxSlippage;          // Maximum allowed slippage (basis points)
        uint256 maxGasPrice;          // Maximum gas price willing to pay (gwei)
        uint256 emergencyThreshold;   // Threshold for emergency shutdown (basis points loss)
    }
    
    // Base risk parameters (when trust score = 50)
    RiskParameters public baseRiskParams;
    
    // Current risk parameters (adjusted by trust score)
    RiskParameters public currentRiskParams;
      // Execution statistics
    uint256 public totalExecutions;
    
    // Gas griefing protection
    uint256 public constant MAX_TOKEN_ARRAY_LENGTH = 50; // Maximum tokens per operation
    uint256 public constant MAX_AMOUNT_ARRAY_LENGTH = 50; // Maximum amounts per operation
    uint256 public successfulExecutions;
    uint256 public totalProfit;
    uint256 public lastExecutionTime;
    uint256 public lastTrustScore;
    
    // ZK proof verification
    struct ZKProof {
        bytes32 proofHash;
        uint256 timestamp;
        bool verified;
        address verifier;
        uint256 expirationTime;
    }
    
    ZKProof public latestProof;
    
    // Timelock for critical operations
    uint256 public constant TIMELOCK_PERIOD = 24 hours;
    mapping(bytes32 => uint256) public timelockExpirations;
    
    // Maximum adjustment factors
    uint256 public constant MAX_ADJUSTMENT_FACTOR = 15000; // 1.5x
    uint256 public constant MIN_ADJUSTMENT_FACTOR = 5000;  // 0.5x
    
    // Minimum risk parameters (safety floor)
    uint256 public constant MIN_PROFIT_THRESHOLD = 10; // 0.1% minimum profit threshold
    uint256 public constant MAX_CAPITAL_LIMIT = 8000;  // 80% maximum capital at risk
    uint256 public constant MAX_SLIPPAGE_LIMIT = 500;  // 5% maximum slippage
    
    // Proof validity period
    uint256 public constant PROOF_VALIDITY_PERIOD = 7 days;
    
    // Events
    event StrategyExecuted(
        uint256 indexed strategyId,
        bool success,
        uint256 profit,
        uint256 trustScore,
        uint256 gasUsed
    );
    
    event RiskParametersAdjusted(
        uint256 trustScore,
        uint256 maxCapitalAtRisk,
        uint256 minProfitThreshold,
        uint256 maxSlippage,
        uint256 adjustmentFactor
    );
    
    event ZKProofSubmitted(
        uint256 indexed strategyId,
        bytes32 proofHash,
        uint256 timestamp,
        uint256 expirationTime
    );
    
    event ZKProofVerified(
        uint256 indexed strategyId,
        bytes32 proofHash,
        bool verified,
        address verifier
    );
    
    event TimelockInitiated(
        bytes32 indexed operationId,
        string operation,
        uint256 executeAfter
    );
    
    event TimelockExecuted(
        bytes32 indexed operationId,
        string operation
    );
    
    event TimelockCancelled(
        bytes32 indexed operationId,
        string operation
    );
    
    event EmergencyShutdown(
        uint256 indexed strategyId,
        address indexed caller,
        string reason
    );

    /**
     * @dev Constructor
     * @param _trustCurveAddress Address of the TrustCurve contract
     * @param _zkVerifierAddress Address of the ZK Verifier contract
     * @param _strategyId Unique identifier for this strategy
     * @param _name Name of the strategy
     * @param _description Description of the strategy
     * @param _baseMaxCapital Base maximum capital at risk (basis points)
     * @param _baseMinProfit Base minimum profit threshold (basis points)
     * @param _baseMaxSlippage Base maximum slippage (basis points)
     * @param _baseMaxGasPrice Base maximum gas price (gwei)
     * @param _baseEmergencyThreshold Base emergency threshold (basis points)
     */
    constructor(
        address _trustCurveAddress,
        address _zkVerifierAddress,
        uint256 _strategyId,
        string memory _name,
        string memory _description,
        uint256 _baseMaxCapital,
        uint256 _baseMinProfit,
        uint256 _baseMaxSlippage,
        uint256 _baseMaxGasPrice,
        uint256 _baseEmergencyThreshold
    ) Ownable(msg.sender) {
        require(_trustCurveAddress != address(0), "Invalid TrustCurve address");
        require(_zkVerifierAddress != address(0), "Invalid ZKVerifier address");
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(_baseMaxCapital <= MAX_CAPITAL_LIMIT, "Max capital too high");
        require(_baseMinProfit >= MIN_PROFIT_THRESHOLD, "Min profit too low");
        require(_baseMaxSlippage <= MAX_SLIPPAGE_LIMIT, "Max slippage too high");
        
        TRUST_CURVE = TrustCurve(_trustCurveAddress);
        ZK_VERIFIER = IZKVerifier(_zkVerifierAddress);
        strategyId = _strategyId;
        name = _name;
        description = _description;
        
        // Set base risk parameters
        baseRiskParams = RiskParameters({
            maxCapitalAtRisk: _baseMaxCapital,
            minProfitThreshold: _baseMinProfit,
            maxSlippage: _baseMaxSlippage,
            maxGasPrice: _baseMaxGasPrice,
            emergencyThreshold: _baseEmergencyThreshold
        });
        
        // Initialize current risk parameters to base values
        currentRiskParams = baseRiskParams;
    }
    
    /**
     * @dev Execute the strategy
     * @param _data Execution data
     * @return success Whether the execution was successful
     * @return result The result of the execution
     */
    function execute(bytes calldata _data) 
        external 
        override 
        nonReentrant 
        whenNotPaused 
        onlyOwner 
        returns (bool success, bytes memory result) 
    {
        // Check if proof is valid and not expired
        require(
            latestProof.verified && 
            block.timestamp <= latestProof.expirationTime,
            "No valid ZK proof or proof expired"
        );
        
        // Get current trust score
        uint256 trustScore = TRUST_CURVE.getTrustScore(strategyId);
        lastTrustScore = trustScore;
        
        // Adjust risk parameters based on trust score
        _adjustRiskParameters(trustScore);
        
        // Check gas price
        require(tx.gasprice <= currentRiskParams.maxGasPrice * 1 gwei, "Gas price too high");
        
        // Record gas at start
        uint256 gasStart = gasleft();
        
        // Execute strategy logic
        (success, result) = _executeStrategyLogic(_data);
        
        // Calculate gas used
        uint256 gasUsed = gasStart - gasleft();
        
        // Update execution statistics
        totalExecutions++;
        lastExecutionTime = block.timestamp;
        
        if (success) {
            successfulExecutions++;
            
            // Extract profit from result
            uint256 profit = abi.decode(result, (uint256));
            
            // Verify profit meets minimum threshold
            require(
                profit >= (baseRiskParams.minProfitThreshold * 1e16), 
                "Profit below threshold"
            );
            
            totalProfit += profit;
            
            // Update trust curve with execution result
            TRUST_CURVE.updateOnChainPerformance(strategyId, true, int256(profit));
            
            emit StrategyExecuted(strategyId, true, profit, trustScore, gasUsed);
        } else {
            // Update trust curve with failed execution
            TRUST_CURVE.updateOnChainPerformance(strategyId, false, 0);
            
            emit StrategyExecuted(strategyId, false, 0, trustScore, gasUsed);
        }
        
        return (success, result);
    }
    
    /**
     * @dev Execute strategy logic
     * @param _data Execution data
     * @return success Whether the execution was successful
     * @return result The result of the execution
     */
    function _executeStrategyLogic(bytes calldata _data) internal returns (bool success, bytes memory result) {
        // This would contain the actual arbitrage logic
        // For now, we'll just return a mock result
        
        // Mock implementation - in a real contract this would execute the actual strategy        (address[] memory tokens, uint256[] memory amounts) = abi.decode(_data, (address[], uint256[]));
        
        // Gas griefing protection
        require(tokens.length <= MAX_TOKEN_ARRAY_LENGTH, "Too many tokens");
        require(amounts.length <= MAX_AMOUNT_ARRAY_LENGTH, "Too many amounts");
        require(tokens.length == amounts.length, "Array length mismatch");
        
        // Check if we have enough tokens for the strategy
        for (uint i = 0; i < tokens.length; i++) {
            if (IERC20(tokens[i]).balanceOf(address(this)) < amounts[i]) {
                return (false, abi.encode("Insufficient token balance"));
            }
            
            // Check if amount exceeds max capital at risk
            uint256 tokenBalance = IERC20(tokens[i]).balanceOf(address(this));
            uint256 maxAmount = (tokenBalance * currentRiskParams.maxCapitalAtRisk) / 10000;
            if (amounts[i] > maxAmount) {
                return (false, abi.encode("Amount exceeds max capital at risk"));
            }
        }
        
        // Mock profit calculation
        uint256 mockProfit = 0;
        for (uint i = 0; i < amounts.length; i++) {
            mockProfit += amounts[i] / 100; // 1% profit on each token
        }
        
        // Check if profit meets minimum threshold
        if (mockProfit < (amounts[0] * currentRiskParams.minProfitThreshold) / 10000) {
            return (false, abi.encode("Profit below threshold"));
        }
        
        return (true, abi.encode(mockProfit));
    }
    
    /**
     * @dev Adjust risk parameters based on trust score
     * @param _trustScore Current trust score
     */
    function _adjustRiskParameters(uint256 _trustScore) internal {
        // Calculate adjustment factor (0.5 to 1.5) based on trust score (0 to 100)
        // At trust score 50, adjustment = 1.0 (base parameters)
        // At trust score 100, adjustment = 1.5 (50% more aggressive)
        // At trust score 0, adjustment = 0.5 (50% more conservative)
        uint256 adjustmentFactor = MIN_ADJUSTMENT_FACTOR + (_trustScore * (MAX_ADJUSTMENT_FACTOR - MIN_ADJUSTMENT_FACTOR) / 100);
        
        // Adjust risk parameters with safety floors
        currentRiskParams.maxCapitalAtRisk = (baseRiskParams.maxCapitalAtRisk * adjustmentFactor) / 10000;
        if (currentRiskParams.maxCapitalAtRisk > MAX_CAPITAL_LIMIT) {
            currentRiskParams.maxCapitalAtRisk = MAX_CAPITAL_LIMIT;
        }
        
        // For min profit threshold, higher trust score means lower threshold
        currentRiskParams.minProfitThreshold = (baseRiskParams.minProfitThreshold * (15000 - adjustmentFactor)) / 10000;
        if (currentRiskParams.minProfitThreshold < MIN_PROFIT_THRESHOLD) {
            currentRiskParams.minProfitThreshold = MIN_PROFIT_THRESHOLD;
        }
        
        // For max slippage, higher trust score means higher slippage tolerance
        currentRiskParams.maxSlippage = (baseRiskParams.maxSlippage * adjustmentFactor) / 10000;
        if (currentRiskParams.maxSlippage > MAX_SLIPPAGE_LIMIT) {
            currentRiskParams.maxSlippage = MAX_SLIPPAGE_LIMIT;
        }
        
        // Max gas price adjustment
        currentRiskParams.maxGasPrice = (baseRiskParams.maxGasPrice * adjustmentFactor) / 10000;
        
        // Emergency threshold remains constant
        currentRiskParams.emergencyThreshold = baseRiskParams.emergencyThreshold;
        
        emit RiskParametersAdjusted(
            _trustScore,
            currentRiskParams.maxCapitalAtRisk,
            currentRiskParams.minProfitThreshold,
            currentRiskParams.maxSlippage,
            adjustmentFactor
        );
    }
    
    /**
     * @dev Submit a ZK proof for verification
     * @param _publicInputs Public inputs for the ZK proof
     * @param _proof The ZK proof data
     */
    function submitZKProof(
        uint256[] calldata _publicInputs,
        bytes calldata _proof
    ) external onlyOwner whenNotPaused {
        // Generate proof hash from inputs and proof
        bytes32 proofHash = keccak256(abi.encodePacked(_publicInputs, _proof));
        
        // Set expiration time
        uint256 expirationTime = block.timestamp + PROOF_VALIDITY_PERIOD;
        
        // Store proof data
        latestProof = ZKProof({
            proofHash: proofHash,
            timestamp: block.timestamp,
            verified: false,
            verifier: address(0),
            expirationTime: expirationTime
        });
        
        emit ZKProofSubmitted(strategyId, proofHash, block.timestamp, expirationTime);
    }
    
    /**
     * @dev Verify a ZK proof
     * @param _publicInputs Public inputs for the ZK proof
     * @param _proof The ZK proof data
     */
    function verifyZKProof(
        uint256[] calldata _publicInputs,
        bytes calldata _proof
    ) external whenNotPaused {
        // Generate proof hash from inputs and proof
        bytes32 proofHash = keccak256(abi.encodePacked(_publicInputs, _proof));
        
        // Check that this matches the latest submitted proof
        require(latestProof.proofHash == proofHash, "Proof hash mismatch");
        
        // Verify the proof using the ZK verifier contract
        bool isValid = ZK_VERIFIER.verifyProof(_publicInputs, _proof);
        
        // Update proof verification status
        latestProof.verified = isValid;
        latestProof.verifier = msg.sender;
        
        // Update trust curve with verification result
        TRUST_CURVE.updateZKVerification(strategyId, isValid);
        
        // If proof is valid, also update the ZK-RL verification
        if (isValid && _publicInputs.length >= 2) {
            // Assuming _publicInputs[1] contains the intelligence score (0-100)
            uint256 intelligenceScore = _publicInputs[1];
            if (intelligenceScore <= 100) {
                TRUST_CURVE.updateZKRLVerification(strategyId, intelligenceScore, true);
            }
        }
        
        emit ZKProofVerified(strategyId, proofHash, isValid, msg.sender);
    }
    
    /**
     * @dev Initiate timelock for updating metadata
     * @param _name New name
     * @param _description New description
     */
    function initiateMetadataUpdate(
        string memory _name,
        string memory _description
    ) external onlyOwner whenNotPaused {
        require(bytes(_name).length > 0, "Name cannot be empty");
        
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateMetadata",
            _name,
            _description
        ));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "updateMetadata", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute timelock for updating metadata
     * @param _name New name
     * @param _description New description
     */
    function executeMetadataUpdate(
        string memory _name,
        string memory _description
    ) external onlyOwner whenNotPaused {
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateMetadata",
            _name,
            _description
        ));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        name = _name;
        description = _description;
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "updateMetadata");
    }
    
    /**
     * @dev Cancel timelock operation
     * @param _operationId Operation ID to cancel
     */
    function cancelTimelock(bytes32 _operationId) external onlyOwner {
        require(timelockExpirations[_operationId] > 0, "Timelock not initiated");
        
        delete timelockExpirations[_operationId];
        
        emit TimelockCancelled(_operationId, "Operation cancelled");
    }
    
    /**
     * @dev Initiate timelock for updating base risk parameters
     * @param _maxCapital New base maximum capital at risk
     * @param _minProfit New base minimum profit threshold
     * @param _maxSlippage New base maximum slippage
     * @param _maxGasPrice New base maximum gas price
     * @param _emergencyThreshold New base emergency threshold
     */
    function initiateRiskParametersUpdate(
        uint256 _maxCapital,
        uint256 _minProfit,
        uint256 _maxSlippage,
        uint256 _maxGasPrice,
        uint256 _emergencyThreshold
    ) external onlyOwner whenNotPaused {
        require(_maxCapital <= MAX_CAPITAL_LIMIT, "Max capital too high");
        require(_minProfit >= MIN_PROFIT_THRESHOLD, "Min profit too low");
        require(_maxSlippage <= MAX_SLIPPAGE_LIMIT, "Max slippage too high");
        
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateRiskParameters",
            _maxCapital,
            _minProfit,
            _maxSlippage,
            _maxGasPrice,
            _emergencyThreshold
        ));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "updateRiskParameters", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute timelock for updating base risk parameters
     * @param _maxCapital New base maximum capital at risk
     * @param _minProfit New base minimum profit threshold
     * @param _maxSlippage New base maximum slippage
     * @param _maxGasPrice New base maximum gas price
     * @param _emergencyThreshold New base emergency threshold
     */
    function executeRiskParametersUpdate(
        uint256 _maxCapital,
        uint256 _minProfit,
        uint256 _maxSlippage,
        uint256 _maxGasPrice,
        uint256 _emergencyThreshold
    ) external onlyOwner whenNotPaused {
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateRiskParameters",
            _maxCapital,
            _minProfit,
            _maxSlippage,
            _maxGasPrice,
            _emergencyThreshold
        ));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        baseRiskParams = RiskParameters({
            maxCapitalAtRisk: _maxCapital,
            minProfitThreshold: _minProfit,
            maxSlippage: _maxSlippage,
            maxGasPrice: _maxGasPrice,
            emergencyThreshold: _emergencyThreshold
        });
        
        // Re-adjust current parameters based on last trust score
        _adjustRiskParameters(lastTrustScore);
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "updateRiskParameters");
    }
    
    /**
     * @dev Initiate timelock for token withdrawal
     * @param _token The token to withdraw
     * @param _amount The amount to withdraw
     * @param _recipient The recipient of the tokens
     */
    function initiateTokenWithdrawal(
        address _token,
        uint256 _amount,
        address _recipient
    ) external onlyOwner whenNotPaused {
        require(_recipient != address(0), "Invalid recipient");
        require(_amount > 0, "Amount must be greater than 0");
        
        bytes32 operationId = keccak256(abi.encodePacked(
            "withdrawTokens",
            _token,
            _amount,
            _recipient
        ));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "withdrawTokens", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute timelock for token withdrawal
     * @param _token The token to withdraw
     * @param _amount The amount to withdraw
     * @param _recipient The recipient of the tokens
     */
    function executeTokenWithdrawal(
        address _token,
        uint256 _amount,
        address _recipient
    ) external onlyOwner {
        bytes32 operationId = keccak256(abi.encodePacked(
            "withdrawTokens",
            _token,
            _amount,
            _recipient
        ));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        // Check token balance
        uint256 balance = IERC20(_token).balanceOf(address(this));
        require(balance >= _amount, "Insufficient token balance");
        
        // Transfer tokens
        IERC20(_token).safeTransfer(_recipient, _amount);
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "withdrawTokens");
    }
    
    /**
     * @dev Emergency withdrawal of all tokens (only when paused)
     * @param _token The token to withdraw
     * @param _recipient The recipient of the tokens
     */
    function emergencyWithdraw(
        address _token,
        address _recipient
    ) external onlyOwner whenPaused {
        require(_recipient != address(0), "Invalid recipient");
        
        uint256 balance = IERC20(_token).balanceOf(address(this));
        require(balance > 0, "No tokens to withdraw");
        
        IERC20(_token).safeTransfer(_recipient, balance);
    }
    
    /**
     * @dev Trigger emergency shutdown
     * @param _reason Reason for emergency shutdown
     */
    function triggerEmergencyShutdown(string memory _reason) external onlyOwner {
        _pause();
        
        emit EmergencyShutdown(strategyId, msg.sender, _reason);
    }
    
    /**
     * @dev Resume after emergency shutdown (requires timelock)
     */
    function initiateEmergencyResume() external onlyOwner whenPaused {
        bytes32 operationId = keccak256(abi.encodePacked("emergencyResume"));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "emergencyResume", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute emergency resume
     */
    function executeEmergencyResume() external onlyOwner whenPaused {
        bytes32 operationId = keccak256(abi.encodePacked("emergencyResume"));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        _unpause();
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "emergencyResume");
    }
    
    /**
     * @dev Get strategy information
     * @return _strategyId Strategy ID
     * @return _name Strategy name
     * @return _description Strategy description
     */
    function getStrategyInfo() external view override returns (uint256 _strategyId, string memory _name, string memory _description) {
        return (strategyId, name, description);
    }
    
    /**
     * @dev Get current risk parameters
     * @return Risk parameters struct
     */
    function getRiskParameters() external view returns (RiskParameters memory) {
        return currentRiskParams;
    }
    
    /**
     * @dev Get strategy performance metrics
     * @return _totalExecutions Total number of executions
     * @return _successRate Success rate (basis points)
     * @return _totalProfit Total profit
     * @return _trustScore Current trust score
     */
    function getPerformanceMetrics() external view returns (
        uint256 _totalExecutions,
        uint256 _successRate,
        uint256 _totalProfit,
        uint256 _trustScore
    ) {
        uint256 successRate = totalExecutions > 0 
            ? (successfulExecutions * 10000) / totalExecutions 
            : 0;
            
        return (
            totalExecutions,
            successRate,
            totalProfit,
            TRUST_CURVE.getTrustScore(strategyId)
        );
    }
    
    /**
     * @dev Get ZK proof status
     * @return _proofHash Hash of the latest proof
     * @return _timestamp Timestamp of the latest proof
     * @return _verified Whether the proof is verified
     * @return _verifier Address of the verifier
     * @return _expirationTime Expiration time of the proof
     * @return _isValid Whether the proof is currently valid
     */
    function getZKProofStatus() external view returns (
        bytes32 _proofHash,
        uint256 _timestamp,
        bool _verified,
        address _verifier,
        uint256 _expirationTime,
        bool _isValid
    ) {
        bool isValid = latestProof.verified && block.timestamp <= latestProof.expirationTime;
        
        return (
            latestProof.proofHash,
            latestProof.timestamp,
            latestProof.verified,
            latestProof.verifier,
            latestProof.expirationTime,
            isValid
        );
    }
}