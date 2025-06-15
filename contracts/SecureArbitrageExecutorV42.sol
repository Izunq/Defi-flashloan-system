// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "./interfaces/IFlashLoanSimpleReceiver.sol";
import "./interfaces/IAavePool.sol";
import "./SecureMultiOracle.sol";
import "./PreCognitiveOracle.sol";

/**
 * @title SecureArbitrageExecutorV42
 * @notice Oracle-hardened arbitrage executor with manipulation protection
 * @dev Integrates SecureMultiOracle for price validation and manipulation detection
 */
contract SecureArbitrageExecutorV42 is AccessControl, ReentrancyGuard, Pausable, IFlashLoanSimpleReceiver {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;

    // =================
    // CONSTANTS & ROLES
    // =================
    
    bytes32 public constant STRATEGY_EXECUTOR_ROLE = keccak256("STRATEGY_EXECUTOR_ROLE");
    bytes32 public constant EMERGENCY_ADMIN_ROLE = keccak256("EMERGENCY_ADMIN_ROLE");
    bytes32 public constant ORACLE_MANAGER_ROLE = keccak256("ORACLE_MANAGER_ROLE");
    bytes32 public constant TREASURY_ADMIN_ROLE = keccak256("TREASURY_ADMIN_ROLE");
    
    // Security Constants
    uint256 public constant MAX_SLIPPAGE_BPS = 50; // 0.5% max slippage (reduced from 1%)
    uint256 public constant EXECUTION_TIMEOUT = 3 minutes; // Reduced timeout
    uint256 public constant ORACLE_STALENESS_THRESHOLD = 30 minutes;
    uint256 public constant MIN_ORACLE_CONFIDENCE = 80; // 80% minimum confidence
    uint256 public constant MAX_PRICE_IMPACT = 200; // 2% max price impact
    
    // Oracle Manipulation Protection
    uint256 public constant ORACLE_DEVIATION_THRESHOLD = 300; // 3% max deviation
    uint256 public constant MIN_ORACLES_FOR_EXECUTION = 3;
    uint256 public constant PRICE_VALIDATION_WINDOW = 60; // 1 minute validation window

    // =================
    // STATE VARIABLES
    // =================
    
    IAavePool public immutable aavePool;
    SecureMultiOracle public immutable priceOracle;
    PreCognitiveOracle public immutable predictiveOracle;
    address public immutable treasury;
    
    // Execution tracking
    mapping(bytes32 => ExecutionDetails) public executionRegistry;
    mapping(address => bool) public approvedStrategies;
    mapping(address => TokenConfig) public tokenConfigs;
    
    // Oracle security state
    mapping(bytes32 => uint256) public lastPriceUpdateTime;
    mapping(bytes32 => uint256) public priceValidationCount;
    mapping(address => uint256) public tokenLastOracleCheck;
    
    // Circuit breaker and emergency controls
    uint256 public failedExecutionsCount;
    uint256 public lastResetTime;
    uint256 public circuitBreakerThreshold = 3; // Reduced threshold
    bool public oracleEmergencyMode = false;
    
    // MEV and manipulation protection
    uint256 public maxGasPrice = 300 gwei; // Reduced gas price limit
    mapping(address => uint256) public tokenMaxTradeSize;
    
    // Flash loan execution state
    bool private _flashLoanInProgress;
    mapping(bytes32 => bool) private _executionLocked;

    // =================
    // STRUCTS & ENUMS
    // =================
    
    struct ExecutionDetails {
        address strategy;
        address initiator;
        uint256 startTime;
        uint256 endTime;
        bool successful;
        uint256 profit;
        bytes32 executionHash;
        ExecutionStatus status;
        PriceValidationData priceValidation;
    }
    
    struct PriceValidationData {
        uint256 preExecutionPrice;
        uint256 postExecutionPrice;
        uint256 oracleConsensusPrice;
        uint256 priceDeviation;
        bool priceManipulationDetected;
        uint256 validationTimestamp;
    }
    
    struct TokenConfig {
        bool isActive;
        uint256 maxTradeSize;
        uint256 minLiquidity;
        bytes32 priceId;
        address[] approvedDEXes;
        uint256 lastHealthCheck;
    }
    
    enum ExecutionStatus {
        NotStarted,
        OracleValidation,
        InProgress,
        PriceValidation,
        Completed,
        Failed,
        OracleManipulationDetected,
        EmergencyHalted
    }

    // =================
    // EVENTS
    // =================
    
    event ArbitrageExecuted(
        bytes32 indexed executionId,
        address indexed strategy,
        address[] assets,
        uint256[] amounts,
        uint256 profit,
        uint256 executionTime,
        PriceValidationData priceValidation
    );
    
    event OracleManipulationDetected(
        bytes32 indexed executionId,
        address indexed asset,
        uint256 expectedPrice,
        uint256 actualPrice,
        uint256 deviation,
        uint256 timestamp
    );
    
    event EmergencyOracleMode(
        bool enabled,
        address triggeredBy,
        string reason,
        uint256 timestamp
    );
    
    event PriceValidationFailed(
        bytes32 indexed executionId,
        address indexed asset,
        uint256 consensusPrice,
        uint256 marketPrice,
        uint256 deviation
    );

    // =================
    // CUSTOM ERRORS
    // =================
    
    error OracleManipulationDetected(address asset, uint256 deviation);
    error InsufficientOracleConsensus(uint256 available, uint256 required);
    error StalePriceData(address asset, uint256 age);
    error PriceDeviationTooHigh(uint256 deviation, uint256 threshold);
    error EmergencyOracleModeActive();
    error InvalidTokenConfiguration(address token);

    // =================
    // MODIFIERS
    // =================
    
    modifier oracleValidationRequired(address[] calldata assets) {
        if (oracleEmergencyMode) {
            revert EmergencyOracleModeActive();
        }
        
        for (uint256 i = 0; i < assets.length; i++) {
            _validateOracleData(assets[i]);
        }
        _;
    }
    
    modifier flashLoanGuard() {
        require(!_flashLoanInProgress, "Flash loan already in progress");
        _flashLoanInProgress = true;
        _;
        _flashLoanInProgress = false;
    }
    
    modifier gasGuard() {
        require(tx.gasprice <= maxGasPrice, "Gas price too high - MEV protection");
        _;
    }

    // =================
    // CONSTRUCTOR
    // =================
    
    constructor(
        address _aavePool,
        address _priceOracle,
        address _predictiveOracle,
        address _treasury,
        address _admin
    ) {
        require(_aavePool != address(0), "Invalid Aave pool address");
        require(_priceOracle != address(0), "Invalid price oracle address");
        require(_predictiveOracle != address(0), "Invalid predictive oracle address");
        require(_treasury != address(0), "Invalid treasury address");
        require(_admin != address(0), "Invalid admin address");
        
        aavePool = IAavePool(_aavePool);
        priceOracle = SecureMultiOracle(_priceOracle);
        predictiveOracle = PreCognitiveOracle(_predictiveOracle);
        treasury = _treasury;
        
        // Setup roles
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(EMERGENCY_ADMIN_ROLE, _admin);
        _grantRole(ORACLE_MANAGER_ROLE, _admin);
        _grantRole(TREASURY_ADMIN_ROLE, _admin);
        
        lastResetTime = block.timestamp;
    }

    // =================
    // ORACLE VALIDATION FUNCTIONS
    // =================
    
    /**
     * @notice Validate oracle data for a specific asset
     * @param asset Asset address to validate
     */
    function _validateOracleData(address asset) internal view {
        TokenConfig memory config = tokenConfigs[asset];
        require(config.isActive, "Token not configured for trading");
        
        // Get consensus price with safety checks
        (uint256 price, bool isValid) = priceOracle.getSafePrice(
            config.priceId, 
            ORACLE_STALENESS_THRESHOLD
        );
        
        if (!isValid) {
            revert StalePriceData(asset, block.timestamp - tokenLastOracleCheck[asset]);
        }
        
        // Check oracle health
        (uint256 activeOracles,,,) = priceOracle.getSystemHealth();
        if (activeOracles < MIN_ORACLES_FOR_EXECUTION) {
            revert InsufficientOracleConsensus(activeOracles, MIN_ORACLES_FOR_EXECUTION);
        }
    }
    
    /**
     * @notice Pre-execution oracle validation
     * @param assets Assets involved in the arbitrage
     * @return priceData Validated price data for each asset
     */
    function _preExecutionOracleCheck(address[] calldata assets) 
        internal 
        returns (uint256[] memory priceData) 
    {
        priceData = new uint256[](assets.length);
        
        for (uint256 i = 0; i < assets.length; i++) {
            TokenConfig memory config = tokenConfigs[assets[i]];
            
            // Get consensus price
            (uint256 consensusPrice, uint256 timestamp, uint256 deviation, bool isValid) = 
                priceOracle.getPrice(config.priceId);
            
            require(isValid, "Invalid oracle price");
            require(
                block.timestamp - timestamp <= ORACLE_STALENESS_THRESHOLD,
                "Oracle price too old"
            );
            require(
                deviation <= ORACLE_DEVIATION_THRESHOLD,
                "Oracle deviation too high"
            );
            
            priceData[i] = consensusPrice;
            tokenLastOracleCheck[assets[i]] = block.timestamp;
        }
        
        return priceData;
    }
    
    /**
     * @notice Post-execution price validation to detect manipulation
     * @param assets Assets that were traded
     * @param preExecutionPrices Prices before execution
     * @return manipulationDetected Whether price manipulation was detected
     */
    function _postExecutionPriceValidation(
        address[] calldata assets,
        uint256[] memory preExecutionPrices
    ) internal returns (bool manipulationDetected) {
        for (uint256 i = 0; i < assets.length; i++) {
            TokenConfig memory config = tokenConfigs[assets[i]];
            
            // Get current consensus price
            (uint256 currentPrice, , uint256 deviation,) = 
                priceOracle.getPrice(config.priceId);
            
            // Calculate price impact
            uint256 priceImpact = _calculatePriceImpact(
                preExecutionPrices[i],
                currentPrice
            );
            
            // Check for excessive price impact (potential manipulation)
            if (priceImpact > MAX_PRICE_IMPACT || deviation > ORACLE_DEVIATION_THRESHOLD) {
                manipulationDetected = true;
                
                emit OracleManipulationDetected(
                    keccak256(abi.encodePacked(block.timestamp, assets[i])),
                    assets[i],
                    preExecutionPrices[i],
                    currentPrice,
                    priceImpact,
                    block.timestamp
                );
                
                // Activate emergency mode if severe manipulation detected
                if (priceImpact > MAX_PRICE_IMPACT * 2) {
                    _activateEmergencyOracleMode("Severe price manipulation detected");
                }
            }
        }
        
        return manipulationDetected;
    }

    // =================
    // EXECUTION FUNCTIONS
    // =================
    
    /**
     * @notice Execute flash loan arbitrage with enhanced oracle security
     * @param assets Assets to flash loan
     * @param amounts Amounts to flash loan
     * @param params Encoded strategy parameters
     */
    function executeFlashLoanArbitrage(
        address[] calldata assets,
        uint256[] calldata amounts,
        bytes calldata params
    )
        external
        nonReentrant
        whenNotPaused
        gasGuard
        oracleValidationRequired(assets)
        flashLoanGuard
        onlyRole(STRATEGY_EXECUTOR_ROLE)
    {
        // Generate execution ID
        bytes32 executionId = keccak256(
            abi.encodePacked(
                msg.sender,
                assets,
                amounts,
                block.timestamp,
                params
            )
        );
        
        // Check execution lock
        require(!_executionLocked[executionId], "Execution already locked");
        _executionLocked[executionId] = true;
        
        // Pre-execution oracle validation
        uint256[] memory preExecutionPrices = _preExecutionOracleCheck(assets);
        
        // Initialize execution details
        executionRegistry[executionId] = ExecutionDetails({
            strategy: address(0), // Will be set by strategy
            initiator: msg.sender,
            startTime: block.timestamp,
            endTime: 0,
            successful: false,
            profit: 0,
            executionHash: executionId,
            status: ExecutionStatus.OracleValidation,
            priceValidation: PriceValidationData({
                preExecutionPrice: preExecutionPrices.length > 0 ? preExecutionPrices[0] : 0,
                postExecutionPrice: 0,
                oracleConsensusPrice: 0,
                priceDeviation: 0,
                priceManipulationDetected: false,
                validationTimestamp: block.timestamp
            })
        });
        
        // Update status
        executionRegistry[executionId].status = ExecutionStatus.InProgress;
        
        // Encode execution parameters with oracle data
        bytes memory enhancedParams = abi.encode(
            params,
            preExecutionPrices,
            executionId,
            block.timestamp
        );
        
        // Execute flash loan
        uint256[] memory interestRateModes = new uint256[](assets.length);
        
        aavePool.flashLoan(
            address(this),
            assets,
            amounts,
            interestRateModes,
            address(this),
            enhancedParams,
            0
        );
        
        // Post-execution validation
        bool manipulationDetected = _postExecutionPriceValidation(
            assets,
            preExecutionPrices
        );
        
        if (manipulationDetected) {
            executionRegistry[executionId].status = ExecutionStatus.OracleManipulationDetected;
            _handleOracleManipulation(executionId, assets);
        } else {
            executionRegistry[executionId].status = ExecutionStatus.Completed;
            executionRegistry[executionId].successful = true;
        }
        
        // Clean up
        _executionLocked[executionId] = false;
        executionRegistry[executionId].endTime = block.timestamp;
    }

    /**
     * @notice Flash loan callback with oracle-enhanced security
     */
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(aavePool), "Invalid flash loan caller");
        require(initiator == address(this), "Invalid flash loan initiator");
        
        // Decode enhanced parameters
        (bytes memory originalParams, uint256[] memory preExecutionPrices, bytes32 executionId, uint256 startTime) = 
            abi.decode(params, (bytes, uint256[], bytes32, uint256));
        
        // Timeout check
        require(
            block.timestamp <= startTime + EXECUTION_TIMEOUT,
            "Execution timeout exceeded"
        );
        
        // Update execution status
        executionRegistry[executionId].status = ExecutionStatus.InProgress;
        
        // Additional oracle check during execution
        for (uint256 i = 0; i < assets.length; i++) {
            _validateOracleData(assets[i]);
        }
        
        // Execute the actual arbitrage strategy
        bool success = _executeArbitrageStrategy(
            assets,
            amounts,
            premiums,
            originalParams,
            executionId
        );
        
        require(success, "Arbitrage strategy execution failed");
        
        // Repay flash loans
        for (uint256 i = 0; i < assets.length; i++) {
            uint256 amountToRepay = amounts[i] + premiums[i];
            IERC20(assets[i]).safeTransfer(address(aavePool), amountToRepay);
        }
        
        return true;
    }

    // =================
    // SECURITY FUNCTIONS
    // =================
    
    /**
     * @notice Handle detected oracle manipulation
     */
    function _handleOracleManipulation(bytes32 executionId, address[] calldata assets) internal {
        // Increment failed execution count
        failedExecutionsCount++;
        
        // Activate circuit breaker if threshold reached
        if (failedExecutionsCount >= circuitBreakerThreshold) {
            _activateEmergencyOracleMode("Circuit breaker threshold reached");
        }
        
        // Report to predictive oracle for future prevention
        for (uint256 i = 0; i < assets.length; i++) {
            // This would integrate with the PreCognitiveOracle to report manipulation events
            // Implementation would depend on the specific predictive oracle interface
        }
    }
    
    /**
     * @notice Activate emergency oracle mode
     */
    function _activateEmergencyOracleMode(string memory reason) internal {
        oracleEmergencyMode = true;
        _pause();
        
        emit EmergencyOracleMode(true, msg.sender, reason, block.timestamp);
    }
    
    /**
     * @notice Calculate price impact between two prices
     */
    function _calculatePriceImpact(uint256 priceBefore, uint256 priceAfter) 
        internal 
        pure 
        returns (uint256) 
    {
        if (priceBefore == 0) return 0;
        
        uint256 difference = priceBefore > priceAfter 
            ? priceBefore - priceAfter 
            : priceAfter - priceBefore;
            
        return (difference * 10000) / priceBefore; // Return in basis points
    }

    // =================
    // ADMIN FUNCTIONS
    // =================
    
    /**
     * @notice Configure token for oracle-secured trading
     */
    function configureToken(
        address token,
        bytes32 priceId,
        uint256 maxTradeSize,
        uint256 minLiquidity,
        address[] calldata approvedDEXes
    ) external onlyRole(ORACLE_MANAGER_ROLE) {
        require(token != address(0), "Invalid token address");
        require(maxTradeSize > 0, "Invalid max trade size");
        
        tokenConfigs[token] = TokenConfig({
            isActive: true,
            maxTradeSize: maxTradeSize,
            minLiquidity: minLiquidity,
            priceId: priceId,
            approvedDEXes: approvedDEXes,
            lastHealthCheck: block.timestamp
        });
        
        tokenMaxTradeSize[token] = maxTradeSize;
    }
    
    /**
     * @notice Emergency deactivation of oracle mode
     */
    function deactivateEmergencyOracleMode() 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
    {
        require(oracleEmergencyMode, "Emergency mode not active");
        
        oracleEmergencyMode = false;
        failedExecutionsCount = 0;
        lastResetTime = block.timestamp;
        
        _unpause();
        
        emit EmergencyOracleMode(false, msg.sender, "Manual deactivation", block.timestamp);
    }

    // =================
    // VIEW FUNCTIONS
    // =================
    
    /**
     * @notice Get execution details with oracle validation data
     */
    function getExecutionDetails(bytes32 executionId) 
        external 
        view 
        returns (ExecutionDetails memory) 
    {
        return executionRegistry[executionId];
    }
    
    /**
     * @notice Check if token is safe for trading based on oracle data
     */
    function isTokenSafeForTrading(address token) external view returns (bool safe, string memory reason) {
        TokenConfig memory config = tokenConfigs[token];
        
        if (!config.isActive) {
            return (false, "Token not configured");
        }
        
        if (oracleEmergencyMode) {
            return (false, "Emergency oracle mode active");
        }
        
        // Check oracle health
        (uint256 activeOracles,,,) = priceOracle.getSystemHealth();
        if (activeOracles < MIN_ORACLES_FOR_EXECUTION) {
            return (false, "Insufficient oracle consensus");
        }
        
        // Check price staleness
        (uint256 price, bool isValid) = priceOracle.getSafePrice(
            config.priceId,
            ORACLE_STALENESS_THRESHOLD
        );
        
        if (!isValid) {
            return (false, "Oracle price not valid");
        }
        
        return (true, "Token safe for trading");
    }

    // =================
    // INTERNAL FUNCTIONS
    // =================
    
    /**
     * @notice Execute the actual arbitrage strategy
     * @dev This function would be implemented based on specific strategy requirements
     */
    function _executeArbitrageStrategy(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        bytes memory params,
        bytes32 executionId
    ) internal returns (bool) {
        // This is a placeholder for the actual arbitrage execution logic
        // Implementation would depend on the specific arbitrage strategies being used
        
        // The strategy should:
        // 1. Decode params to get strategy-specific parameters
        // 2. Execute the arbitrage logic
        // 3. Ensure sufficient profit to cover flash loan premiums
        // 4. Update execution registry with results
        
        return true; // Placeholder return
    }
}
