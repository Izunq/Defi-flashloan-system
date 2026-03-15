// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "./TrustCurve.sol";
import "./StrategyIncubatorV33.sol";

/**
 * @title StrategyGeneratorV37
 * @notice Manages the autonomous generation and deployment of new strategies
 * @dev Part of the V37 Autonomous Self-Rewriter architecture
 */
contract StrategyGeneratorV37 is Ownable, AccessControl {
    using ECDSA for bytes32;
    
    // Role definitions
    bytes32 public constant GENERATOR_ROLE = keccak256("GENERATOR_ROLE");
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");
    bytes32 public constant DEPLOYER_ROLE = keccak256("DEPLOYER_ROLE");
    
    // Contract references
    TrustCurve public immutable TRUST_CURVE;
    StrategyIncubatorV33 public immutable STRATEGY_INCUBATOR;
    
    // Strategy generation parameters
    struct GenerationParameters {
        uint256 minPerformanceThreshold;   // Minimum performance score required for generation
        uint256 minExecutions;             // Minimum number of executions required
        uint256 minSuccessRate;            // Minimum success rate required (basis points)
        uint256 cooldownPeriod;            // Cooldown period between generations (seconds)
        uint256 maxDailyGenerations;       // Maximum number of generations per day
    }
    
    GenerationParameters public generationParams;
    
    // Strategy bytecode verification
    struct BytecodeVerification {
        bytes32 bytecodeHash;              // Hash of the bytecode
        address[] validators;              // Addresses of validators who approved
        bool deployed;                     // Whether the bytecode has been deployed
        uint256 timestamp;                 // Timestamp of verification
    }
    
    // Mapping from generation ID to bytecode verification
    mapping(uint256 => BytecodeVerification) public verifications;
    
    // Generation statistics
    uint256 public generationCounter;
    uint256 public successfulDeployments;
    uint256 public lastGenerationTimestamp;
    uint256 public dailyGenerationCount;
    uint256 public dailyCounterResetTime;
    
    // Reincarnation tracking
    mapping(uint256 => uint256) public reincarnationAttempts; // strategyId => number of attempts
    mapping(uint256 => uint256[]) public reincarnatedVariants; // failedStrategyId => array of variant strategyIds
    
    // Events
    event StrategyGenerated(
        uint256 indexed generationId,
        bytes32 bytecodeHash,
        string metadataURI,
        uint256 timestamp
    );
    
    event BytecodeVerified(
        uint256 indexed generationId,
        address indexed validator,
        bytes32 bytecodeHash,
        uint256 timestamp
    );
    
    event StrategyDeployed(
        uint256 indexed generationId,
        address indexed strategyAddress,
        uint256 indexed strategyId,
        uint256 timestamp
    );
    
    event GenerationParametersUpdated(
        uint256 minPerformanceThreshold,
        uint256 minExecutions,
        uint256 minSuccessRate,
        uint256 cooldownPeriod,
        uint256 maxDailyGenerations
    );
    
    event StrategyReincarnated(
        uint256 indexed failedStrategyId,
        uint256 indexed generationId,
        uint256 attemptNumber,
        uint256 timestamp
    );
    
    /**
     * @dev Constructor
     * @param _trustCurveAddress Address of the TrustCurve contract
     * @param _incubatorAddress Address of the StrategyIncubator contract
     */
    constructor(
        address _trustCurveAddress,
        address _incubatorAddress
    ) Ownable(msg.sender) {
        require(_trustCurveAddress != address(0), "Invalid TrustCurve address");
        require(_incubatorAddress != address(0), "Invalid Incubator address");
        
        TRUST_CURVE = TrustCurve(_trustCurveAddress);
        STRATEGY_INCUBATOR = StrategyIncubatorV33(_incubatorAddress);
        
        // Setup roles
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), msg.sender);
        _grantRole(GENERATOR_ROLE, msg.sender);
        _grantRole(VALIDATOR_ROLE, msg.sender);
        _grantRole(DEPLOYER_ROLE, msg.sender);
        
        // Initialize generation parameters
        generationParams = GenerationParameters({
            minPerformanceThreshold: 80,   // 80/100 performance score
            minExecutions: 50,             // At least 50 executions
            minSuccessRate: 9000,          // 90% success rate
            cooldownPeriod: 1 days,        // 1 day between generations
            maxDailyGenerations: 3         // Max 3 generations per day
        });
        
        // Initialize counters
        generationCounter = 0;
        successfulDeployments = 0;
        lastGenerationTimestamp = 0;
        dailyGenerationCount = 0;
        dailyCounterResetTime = block.timestamp + 1 days;
    }
    
    /**
     * @dev Generate a new strategy
     * @param _baseStrategyId ID of the base strategy to improve
     * @param _bytecodeHash Hash of the generated bytecode
     * @param _metadataURI URI pointing to the strategy metadata
     * @return generationId ID of the generated strategy
     */
    function generateStrategy(
        uint256 _baseStrategyId,
        bytes32 _bytecodeHash,
        string memory _metadataURI
    ) external onlyRole(GENERATOR_ROLE) returns (uint256 generationId)  {
        // TODO: Add nonReentrant modifier
        // Check if generation is allowed
        require(_canGenerateStrategy(_baseStrategyId), "Generation not allowed");
        
        // Reset daily counter if needed
        if (block.timestamp >= dailyCounterResetTime) {
            dailyGenerationCount = 0;
            dailyCounterResetTime = block.timestamp + 1 days;
        }
        
        // Check daily generation limit
        require(dailyGenerationCount < generationParams.maxDailyGenerations, "Daily generation limit reached");
        
        // Increment counters
        generationCounter++;
        dailyGenerationCount++;
        lastGenerationTimestamp = block.timestamp;
        
        // Create new generation ID
        generationId = generationCounter;
        
        // Initialize verification
        verifications[generationId] = BytecodeVerification({
            bytecodeHash: _bytecodeHash,
            validators: new address[](0),
            deployed: false,
            timestamp: block.timestamp
        });
        
        // Emit event
        emit StrategyGenerated(
            generationId,
            _bytecodeHash,
            _metadataURI,
            block.timestamp
        );
        
        return generationId;
    }
    
    /**
     * @dev Verify bytecode for a generated strategy
     * @param _generationId ID of the generated strategy
     * @param _bytecodeHash Hash of the bytecode to verify
     */
    function verifyBytecode(
        uint256 _generationId,
        bytes32 _bytecodeHash
    ) external onlyRole(VALIDATOR_ROLE)  {
        // TODO: Add nonReentrant modifier
        // Check if generation exists
        require(_generationId > 0 && _generationId <= generationCounter, "Invalid generation ID");
        
        // Get verification
        BytecodeVerification storage verification = verifications[_generationId];
        
        // Check if bytecode hash matches
        require(verification.bytecodeHash == _bytecodeHash, "Bytecode hash mismatch");
        
        // Check if already verified by this validator
        for (uint i = 0; i < verification.validators.length; i++) {
            require(verification.validators[i] != msg.sender, "Already verified by this validator");
        }
        
        // Add validator
        verification.validators.push(msg.sender);
        
        // Emit event
        emit BytecodeVerified(
            _generationId,
            msg.sender,
            _bytecodeHash,
            block.timestamp
        );
    }
    
    /**
     * @dev Deploy a verified strategy
     * @param _generationId ID of the generated strategy
     * @param _strategyAddress Address of the deployed strategy
     * @param _baseStrategyId ID of the base strategy
     * @return strategyId ID of the deployed strategy in the incubator
     */
    function deployStrategy(
        uint256 _generationId,
        address _strategyAddress,
        uint256 _baseStrategyId
    ) external onlyRole(DEPLOYER_ROLE) returns (uint256 strategyId)  {
        // TODO: Add nonReentrant modifier
        // Check if generation exists
        require(_generationId > 0 && _generationId <= generationCounter, "Invalid generation ID");
        
        // Get verification
        BytecodeVerification storage verification = verifications[_generationId];
        
        // Check if not already deployed
        require(!verification.deployed, "Already deployed");
        
        // Check if enough validators
        require(verification.validators.length >= 2, "Not enough validators");
        
        // Mark as deployed
        verification.deployed = true;
        
        // Propose strategy to incubator
        strategyId = STRATEGY_INCUBATOR.proposeStrategy(
            _strategyAddress,
            _baseStrategyId,
            true // isVariant
        );
        
        // Update counter
        successfulDeployments++;
        
        // Emit event
        emit StrategyDeployed(
            _generationId,
            _strategyAddress,
            strategyId,
            block.timestamp
        );
        
        return strategyId;
    }
    
    /**
     * @dev Check if a strategy can be generated
     * @param _baseStrategyId ID of the base strategy
     * @return canGenerate Whether a strategy can be generated
     */
    function _canGenerateStrategy(uint256 _baseStrategyId) internal view returns (bool) {
        // Check cooldown period
        if (block.timestamp - lastGenerationTimestamp < generationParams.cooldownPeriod) {
            return false;
        }
        
        // Get strategy scorecard
        TrustCurve.StrategyScorecard memory scorecard = TRUST_CURVE.getStrategyScorecard(_baseStrategyId);
        
        // Check minimum executions
        if (scorecard.totalExecutions < generationParams.minExecutions) {
            return false;
        }
        
        // Check minimum success rate
        uint256 successRate = scorecard.totalExecutions > 0
            ? (scorecard.successfulExecutions * 10000) / scorecard.totalExecutions
            : 0;
            
        if (successRate < generationParams.minSuccessRate) {
            return false;
        }
        
        // Check minimum performance threshold
        if (scorecard.trustScore < generationParams.minPerformanceThreshold) {
            return false;
        }
        
        return true;
    }
    
    /**
     * @dev Update generation parameters
     * @param _minPerformanceThreshold New minimum performance threshold
     * @param _minExecutions New minimum executions
     * @param _minSuccessRate New minimum success rate
     * @param _cooldownPeriod New cooldown period
     * @param _maxDailyGenerations New maximum daily generations
     */
    function updateGenerationParameters(
        uint256 _minPerformanceThreshold,
        uint256 _minExecutions,
        uint256 _minSuccessRate,
        uint256 _cooldownPeriod,
        uint256 _maxDailyGenerations
    ) external onlyOwner nonReentrant{
        generationParams = GenerationParameters({
            minPerformanceThreshold: _minPerformanceThreshold,
            minExecutions: _minExecutions,
            minSuccessRate: _minSuccessRate,
            cooldownPeriod: _cooldownPeriod,
            maxDailyGenerations: _maxDailyGenerations
        });
        
        emit GenerationParametersUpdated(
            _minPerformanceThreshold,
            _minExecutions,
            _minSuccessRate,
            _cooldownPeriod,
            _maxDailyGenerations
        );
    }
    
    /**
     * @dev Get verification details
     * @param _generationId ID of the generated strategy
     * @return bytecodeHash Hash of the bytecode
     * @return validatorCount Number of validators
     * @return deployed Whether the bytecode has been deployed
     * @return timestamp Timestamp of verification
     */
    function getVerificationDetails(uint256 _generationId) external view returns (
        bytes32 bytecodeHash,
        uint256 validatorCount,
        bool deployed,
        uint256 timestamp
    ) {
        require(_generationId > 0 && _generationId <= generationCounter, "Invalid generation ID");
        
        BytecodeVerification storage verification = verifications[_generationId];
        
        return (
            verification.bytecodeHash,
            verification.validators.length,
            verification.deployed,
            verification.timestamp
        );
    }
    
    /**
     * @dev Check if a validator has verified a generation
     * @param _generationId ID of the generated strategy
     * @param _validator Address of the validator
     * @return hasVerified Whether the validator has verified the generation
     */
    function hasValidatorVerified(uint256 _generationId, address _validator) external view returns (bool)  {
        // TODO: Add nonReentrant modifier
        require(_generationId > 0 && _generationId <= generationCounter, "Invalid generation ID");
        
        BytecodeVerification storage verification = verifications[_generationId];
        
        for (uint i = 0; i < verification.validators.length; i++) {
            if (verification.validators[i] == _validator) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * @dev Get generation statistics
     * @return totalGenerations Total number of generations
     * @return totalDeployments Total number of successful deployments
     * @return dailyCount Daily generation count
     * @return nextResetTime Next reset time for daily counter
     */
    function getGenerationStats() external view returns (
        uint256 totalGenerations,
        uint256 totalDeployments,
        uint256 dailyCount,
        uint256 nextResetTime
    ) {
        return (
            generationCounter,
            successfulDeployments,
            dailyGenerationCount,
            dailyCounterResetTime
        );
    }
    
    /**
     * @dev Reincarnate a failed strategy with improved parameters
     * @param _failedStrategyId ID of the failed strategy
     * @return generationId ID of the new generation
     */
    function reincarnate(
        uint256 _failedStrategyId
    ) external onlyRole(GENERATOR_ROLE) returns (uint256 generationId)  {
        // TODO: Add nonReentrant modifier
        // Check if the strategy exists
        require(
            STRATEGY_INCUBATOR.getStrategy(_failedStrategyId).strategyAddress != address(0),
            "Strategy does not exist"
        );
        
        // Check if we've exceeded the maximum reincarnation attempts
        // This is a safety measure to prevent infinite reincarnation loops
        uint256 attempts = reincarnationAttempts[_failedStrategyId];
        require(attempts < 10, "Maximum reincarnation attempts reached");
        
        // Increment reincarnation attempts counter
        reincarnationAttempts[_failedStrategyId] = attempts + 1;
        
        // Reset daily counter if needed
        if (block.timestamp >= dailyCounterResetTime) {
            dailyGenerationCount = 0;
            dailyCounterResetTime = block.timestamp + 1 days;
        }
        
        // Check daily generation limit
        require(dailyGenerationCount < generationParams.maxDailyGenerations, "Daily generation limit reached");
        
        // Increment counters
        generationCounter++;
        dailyGenerationCount++;
        lastGenerationTimestamp = block.timestamp;
        
        // Create new generation ID
        generationId = generationCounter;
        
        // Initialize verification with empty bytecode hash
        // The actual bytecode hash will be set by the RL agent later
        verifications[generationId] = BytecodeVerification({
            bytecodeHash: bytes32(0),
            validators: new address[](0),
            deployed: false,
            timestamp: block.timestamp
        });
        
        // Track the variant in the reincarnatedVariants mapping
        reincarnatedVariants[_failedStrategyId].push(generationId);
        
        // Emit event
        emit StrategyReincarnated(
            _failedStrategyId,
            generationId,
            attempts + 1,
            block.timestamp
        );
        
        return generationId;
    }
    
    /**
     * @dev Get reincarnated variants of a strategy
     * @param _failedStrategyId ID of the failed strategy
     * @return variants Array of variant generation IDs
     */
    function getReincarnatedVariants(uint256 _failedStrategyId) external view returns (uint256[] memory)  {
        // TODO: Add nonReentrant modifier
        return reincarnatedVariants[_failedStrategyId];
    }
}
