// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "./HalalAssetRegistry.sol";

/**
 * @title MudarabahInvestmentPool
 * @dev Shariah-compliant investment pool based on Mudarabah principles
 * 
 * ISLAMIC FINANCE FEATURES:
 * 🕌 Fully Shariah-compliant structure
 * 💰 Profit-sharing based on Mudarabah principles
 * 🛡️ Risk-sharing between investors and manager
 * ⚡ Halal-only asset universe
 * 📊 Transparent profit distribution
 * 🔒 Ethical investment guidelines
 */
contract MudarabahInvestmentPool is 
    AccessControlEnumerable, 
    ReentrancyGuard, 
    Pausable 
{
    using SafeERC20 for IERC20;
    using Math for uint256;

    // Islamic Finance Roles
    bytes32 public constant MUDARIB_ROLE = keccak256("MUDARIB_ROLE"); // Manager
    bytes32 public constant SHARIAH_ADVISOR_ROLE = keccak256("SHARIAH_ADVISOR_ROLE");
    bytes32 public constant RISK_MANAGER_ROLE = keccak256("RISK_MANAGER_ROLE");
    bytes32 public constant ZAKAT_MANAGER_ROLE = keccak256("ZAKAT_MANAGER_ROLE");
    bytes32 public constant AI_AGENT_ROLE = keccak256("AI_AGENT_ROLE");
    bytes32 public constant EXECUTION_ROLE = keccak256("EXECUTION_ROLE");

    // Halal asset registry
    HalalAssetRegistry public immutable HALAL_REGISTRY;

    // Performance Targets
    struct PerformanceTargets {
        uint256 targetDailyProfitUSD;   // Target daily profit in USD
        uint256 maxDailyLossUSD;        // Maximum daily loss in USD
        uint256 minSuccessRate;         // Minimum success rate (basis points)
        uint256 maxDrawdown;            // Maximum drawdown (basis points)
    }

    // Capital Management
    struct CapitalLimits {
        uint256 totalCapitalUSD;        // Total managed capital
        uint256 maxPositionSizePct;     // Max position size percentage
        uint256 reserveCapitalPct;      // Reserve capital percentage
        uint256 singleAssetLimit;       // Single asset concentration limit
        uint256 singleStrategyLimit;    // Single strategy limit
    }

    // Risk Management
    struct RiskMetrics {
        uint256 valueAtRisk99;          // 99% VaR
        uint256 expectedShortfall;      // Expected shortfall
        uint256 portfolioVolatility;    // Portfolio volatility
        uint256 maxCorrelation;         // Maximum correlation allowed
        uint256 stressTestResult;       // Latest stress test result
        uint256 liquidityRisk;          // Liquidity risk score
        uint256 lastVaRUpdateTime;      // Last time VaR was updated
        uint256 stressTestScenarioId;   // ID of the last stress test scenario
    }
    
    // Correlation Matrix
    struct CorrelationData {
        address asset1;
        address asset2;
        int256 correlation;  // Correlation in basis points (-10000 to 10000)
        uint256 updateTime;
    }
    
    // Stress Test Scenario
    struct StressTestScenario {
        string name;
        string description;
        mapping(address => int256) assetImpacts;  // Impact on each asset in basis points
        uint256 creationTime;
        address creator;
        bool isActive;
    }

    // Execution Statistics
    struct ExecutionStats {
        uint256 totalExecutions;
        uint256 successfulExecutions;
        uint256 totalProfitUSD;
        uint256 totalLossUSD;
        uint256 averageExecutionTime;
        uint256 averageProfitPerTrade;
        uint256 maxSingleProfit;
        uint256 maxSingleLoss;
    }

    // AI Prediction Data
    struct AIPrediction {
        uint256 profitProbability;      // Probability of profit (basis points)
        uint256 expectedProfitUSD;      // Expected profit in USD
        uint256 confidenceScore;        // AI confidence score
        uint256 riskScore;              // Risk assessment score
        uint256 executionUrgency;       // Execution urgency score
        uint256 timestamp;              // Prediction timestamp
        bytes32 modelVersion;           // AI model version hash
    }

    // Investor Data
    struct InvestorData {
        uint256 capitalInvested;        // Total capital invested
        uint256 profitShare;            // Accumulated profit share
        uint256 lossShare;              // Accumulated loss share
        uint256 lastDepositTime;        // Timestamp of last deposit
        uint256 lastWithdrawalTime;     // Timestamp of last withdrawal
    }

    // Profit Distribution
    struct ProfitDistribution {
        uint256 investorShare;          // Investor share (basis points)
        uint256 mudaribShare;           // Mudarib share (basis points)
        uint256 zakatShare;             // Zakat share (basis points)
        uint256 reserveShare;           // Reserve share (basis points)
    }

    // State Variables
    PerformanceTargets public performanceTargets;
    CapitalLimits public capitalLimits;
    RiskMetrics public riskMetrics;
    ExecutionStats public executionStats;
    ProfitDistribution public profitDistribution;

    // Daily tracking
    mapping(uint256 => uint256) public dailyProfits;  // day => profit
    mapping(uint256 => uint256) public dailyLosses;   // day => losses
    mapping(uint256 => uint256) public dailyExecutions; // day => execution count
    
    // Asset management
    mapping(address => uint256) public assetBalances;
    mapping(address => uint256) public assetLimits;
    address[] public supportedAssets;
      // Strategy tracking
    mapping(bytes32 => bool) public approvedStrategies;
    mapping(bytes32 => uint256) public strategyAllocations;
    mapping(bytes32 => ExecutionStats) public strategyStats;
    
    // Blacklist and security
    mapping(address => bool) public blacklistedInvestors;
    mapping(address => uint256) public investorViolations;
    
    // AI integration
    mapping(bytes32 => AIPrediction) public aiPredictions;
    address public aiAgent;
    uint256 public minAIConfidence = 8500; // 85% minimum confidence
    
    // V55: On-chain safeguards against malicious AI agent actions
    uint256 public maxDailyTransactionLimit = 10; // Maximum number of transactions per day
    uint256 public maxTransactionValueUSD = 100000 * 1e6; // $100,000 maximum per transaction
    uint256 public aiActionTimelock = 4 hours; // Time delay for AI-proposed actions
    mapping(bytes32 => uint256) public pendingAIActions; // actionId => timestamp
    mapping(uint256 => uint256) public dailyTransactionCount; // day => count
    
    // Investor tracking
    mapping(address => InvestorData) public investors;
    address[] public investorList;
    uint256 public totalInvestorCapital;
    
    // Zakat tracking
    uint256 public zakatCollected;
    uint256 public lastZakatDistribution;
    address public zakatTreasury;
    
    // Emergency systems
    bool public emergencyShutdown;
    uint256 public emergencyWithdrawalDelay = 24 hours;
    mapping(address => uint256) public emergencyWithdrawalRequests;
    
    // Performance tracking
    uint256 public inceptionTimestamp;
    uint256 public totalReturnBasisPoints;
    uint256 public maxDrawdownBasisPoints;
    
    // Risk management enhancements
    mapping(bytes32 => CorrelationData) public correlationMatrix;
    bytes32[] public correlationPairs;
    mapping(uint256 => StressTestScenario) public stressTestScenarios;
    uint256 public nextStressTestScenarioId = 1;
    uint256 public lastStressTestTimestamp;
    
    // Events
    event PerformanceTargetSet(string target, uint256 value);
    event CapitalLimitUpdated(string limit, uint256 value);
    event RiskMetricUpdated(string metric, uint256 value);
    event StrategyExecuted(
        bytes32 indexed strategyId,
        address indexed executor,
        uint256 profitUSD,
        uint256 executionTime,
        uint256 aiConfidence
    );
    event AIPredictionReceived(
        bytes32 indexed predictionId,
        uint256 profitProbability,
        uint256 expectedProfit,
        uint256 confidence
    );
    event RiskLimitBreached(
        string riskType,
        uint256 currentValue,
        uint256 limitValue,
        uint256 timestamp
    );
    event CapitalInvested(
        address indexed investor,
        address indexed token,
        uint256 amount,
        uint256 timestamp
    );
    event CapitalWithdrawn(
        address indexed investor,
        address indexed token,
        uint256 amount,
        uint256 timestamp
    );
    event ProfitDistributed(
        uint256 totalProfit,
        uint256 investorShare,
        uint256 mudaribShare,
        uint256 zakatShare,
        uint256 reserveShare,
        uint256 timestamp
    );
    event LossDistributed(
        uint256 totalLoss,
        uint256 investorShare,
        uint256 timestamp
    );
    event ZakatCollected(
        uint256 amount,
        uint256 timestamp
    );
    event ZakatDistributed(
        address recipient,
        uint256 amount,
        uint256 timestamp
    );
    event EmergencyShutdownActivated(
        address indexed triggeredBy,
        string reason,
        uint256 timestamp
    );
    event EmergencyShutdownDeactivated(
        address indexed triggeredBy,
        uint256 timestamp
    );
    event DailyPerformanceReport(
        uint256 indexed day,
        uint256 profit,
        uint256 loss,
        uint256 netReturn,
        uint256 executionCount
    );
    
    // V51 Risk Management Events
    event VaRUpdated(
        uint256 valueAtRisk99,
        uint256 expectedShortfall,
        uint256 timestamp
    );
    
    event CorrelationUpdated(
        address indexed asset1,
        address indexed asset2,
        int256 correlation,
        uint256 timestamp
    );
    
    event StressTestScenarioCreated(
        uint256 indexed scenarioId,
        string name,
        address creator,
        uint256 timestamp
    );
    
    event StressTestExecuted(
        uint256 indexed scenarioId,
        uint256 portfolioValueBefore,
        uint256 portfolioValueAfter,
        int256 impactPercentage,
        uint256 timestamp
    );
    
    event ProfitDistributionUpdated(
        uint256 investorShare,
        uint256 mudaribShare,
        uint256 zakatShare,
        uint256 reserveShare
    );
    
    // V55: Events for AI action safeguards
    event AIActionProposed(
        bytes32 indexed actionId,
        address indexed proposer,
        bytes32 strategyId,
        uint256 valueUSD,
        uint256 executionTime
    );
    
    event AIActionCancelled(
        bytes32 indexed actionId,
        address indexed canceller,
        string reason
    );
    
    event AIActionExecuted(
        bytes32 indexed actionId,
        address indexed executor,
        bytes32 strategyId,
        uint256 valueUSD
    );
    
    event SafeguardLimitUpdated(
        string limitName,
        uint256 oldValue,
        uint256 newValue,
        address updater
    );

    // Modifiers
    modifier onlyMudarib() {
        require(hasRole(MUDARIB_ROLE, msg.sender), "Not mudarib");
        _;
    }
    
    modifier onlyShariahAdvisor() {
        require(hasRole(SHARIAH_ADVISOR_ROLE, msg.sender), "Not Shariah advisor");
        _;
    }
    
    modifier onlyRiskManager() {
        require(hasRole(RISK_MANAGER_ROLE, msg.sender), "Not risk manager");
        _;
    }
    
    modifier onlyZakatManager() {
        require(hasRole(ZAKAT_MANAGER_ROLE, msg.sender), "Not Zakat manager");
        _;
    }
    
    modifier onlyAIAgent() {
        require(hasRole(AI_AGENT_ROLE, msg.sender), "Not AI agent");
        _;
    }
    
    modifier onlyExecution() {
        require(hasRole(EXECUTION_ROLE, msg.sender), "Not execution engine");
        _;
    }
    
    modifier notEmergencyShutdown() {
        require(!emergencyShutdown, "Emergency shutdown active");
        _;
    }
    
    modifier riskLimitsCheck() {
        _;
        _checkRiskLimits();
    }

    /**
     * @dev Modifier to ensure only halal-compliant assets are used
     */
    modifier onlyHalalAsset(address token) {
        require(HALAL_REGISTRY.isHalalCompliant(token), "Asset not Shariah-compliant");
        _;
    }
    
    /**
     * @dev Modifier to ensure the asset pair is valid
     */
    modifier validAssetPair(address asset1, address asset2) {
        require(asset1 != address(0) && asset2 != address(0), "Invalid asset address");
        require(asset1 != asset2, "Assets must be different");
        require(HALAL_REGISTRY.isHalalCompliant(asset1) && HALAL_REGISTRY.isHalalCompliant(asset2), 
                "Both assets must be Shariah-compliant");
        _;
    }

    constructor(
        address _halalRegistry,
        address _admin,
        address _mudarib,
        address _shariahAdvisor,
        address _riskManager,
        address _zakatManager,
        address _aiAgent,
        address _zakatTreasury
    ) {
        require(_halalRegistry != address(0), "Invalid registry address");
        require(_admin != address(0), "Invalid admin address");
        require(_mudarib != address(0), "Invalid mudarib address");
        require(_shariahAdvisor != address(0), "Invalid Shariah advisor address");
        require(_riskManager != address(0), "Invalid risk manager address");
        require(_zakatManager != address(0), "Invalid Zakat manager address");
        require(_aiAgent != address(0), "Invalid AI agent address");
        require(_zakatTreasury != address(0), "Invalid Zakat treasury address");

        HALAL_REGISTRY = HalalAssetRegistry(_halalRegistry);
        aiAgent = _aiAgent;
        zakatTreasury = _zakatTreasury;
        inceptionTimestamp = block.timestamp;

        // Setup roles
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(MUDARIB_ROLE, _mudarib);
        _grantRole(SHARIAH_ADVISOR_ROLE, _shariahAdvisor);
        _grantRole(RISK_MANAGER_ROLE, _riskManager);
        _grantRole(ZAKAT_MANAGER_ROLE, _zakatManager);
        _grantRole(AI_AGENT_ROLE, _aiAgent);
        _grantRole(EXECUTION_ROLE, _admin);

        // Initialize performance targets
        performanceTargets = PerformanceTargets({
            targetDailyProfitUSD: 15000 * 1e6,   // $15,000
            maxDailyLossUSD: 1000 * 1e6,         // $1,000
            minSuccessRate: 9500,                 // 95%
            maxDrawdown: 200                      // 2%
        });

        // Initialize capital limits
        capitalLimits = CapitalLimits({
            totalCapitalUSD: 1000000 * 1e6,      // $1M
            maxPositionSizePct: 1000,             // 10%
            reserveCapitalPct: 2000,              // 20%
            singleAssetLimit: 2500,               // 25%
            singleStrategyLimit: 1500             // 15%
        });

        // Initialize profit distribution
        profitDistribution = ProfitDistribution({
            investorShare: 8000,                  // 80%
            mudaribShare: 1750,                   // 17.5%
            zakatShare: 250,                      // 2.5% (standard Zakat rate)
            reserveShare: 0                       // 0%
        });

        // Ensure profit distribution adds up to 100%
        require(
            profitDistribution.investorShare + 
            profitDistribution.mudaribShare + 
            profitDistribution.zakatShare + 
            profitDistribution.reserveShare == 10000,
            "Profit distribution must total 100%"
        );
    }

    /**
     * @dev Invest capital into the Mudarabah pool
     * @param token The token to invest
     * @param amount The amount to invest
     */
    function invest(
        address token,
        uint256 amount
    ) external nonReentrant whenNotPaused notEmergencyShutdown onlyHalalAsset(token) {
        require(amount > 0, "Amount must be greater than 0");
        
        // Transfer tokens from investor to contract
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);
        
        // Update investor data
        if (investors[msg.sender].capitalInvested == 0) {
            investorList.push(msg.sender);
        }
        
        investors[msg.sender].capitalInvested += amount;
        investors[msg.sender].lastDepositTime = block.timestamp;
        
        // Update asset balance
        assetBalances[token] += amount;
        
        // Add to supported assets if not already added
        bool assetExists = false;
        for (uint256 i = 0; i < supportedAssets.length; i++) {
            if (supportedAssets[i] == token) {
                assetExists = true;
                break;
            }
        }
        
        if (!assetExists) {
            supportedAssets.push(token);
        }
        
        // Update total investor capital
        totalInvestorCapital += amount;
        
        emit CapitalInvested(msg.sender, token, amount, block.timestamp);
    }

    /**
     * @dev Withdraw capital from the Mudarabah pool
     * @param token The token to withdraw
     * @param amount The amount to withdraw
     */
    function withdraw(
        address token,
        uint256 amount
    ) external nonReentrant whenNotPaused onlyHalalAsset(token) {
        require(amount > 0, "Amount must be greater than 0");
        require(investors[msg.sender].capitalInvested >= amount, "Insufficient investment");
        
        // Check if emergency withdrawal request is needed
        if (emergencyShutdown) {
            require(
                emergencyWithdrawalRequests[msg.sender] > 0 && 
                block.timestamp >= emergencyWithdrawalRequests[msg.sender],
                "Emergency withdrawal not approved or delay not passed"
            );
        }
        
        // Update investor data
        investors[msg.sender].capitalInvested -= amount;
        investors[msg.sender].lastWithdrawalTime = block.timestamp;
        
        // Update asset balance
        assetBalances[token] -= amount;
        
        // Update total investor capital
        totalInvestorCapital -= amount;
        
        // Transfer tokens to investor
        IERC20(token).safeTransfer(msg.sender, amount);
        
        emit CapitalWithdrawn(msg.sender, token, amount, block.timestamp);
    }

    /**
     * @dev Withdraw profit share
     * @param token The token to withdraw profit in
     */
    function withdrawProfitShare(
        address token
    ) external nonReentrant whenNotPaused onlyHalalAsset(token) {
        uint256 profitShare = investors[msg.sender].profitShare;
        require(profitShare > 0, "No profit to withdraw");
        
        // Reset profit share
        investors[msg.sender].profitShare = 0;
        
        // Transfer profit to investor
        IERC20(token).safeTransfer(msg.sender, profitShare);
        
        emit CapitalWithdrawn(msg.sender, token, profitShare, block.timestamp);
    }

    /**
     * @dev Execute Shariah-compliant strategy
     */
    function executeStrategy(
        bytes32 strategyId,
        address[] calldata assets,
        uint256[] calldata amounts,
        bytes[] calldata executionData,
        bytes32 aiPredictionId
    ) 
        external 
        onlyExecution 
        nonReentrant 
        whenNotPaused 
        notEmergencyShutdown
        riskLimitsCheck
    {
        require(approvedStrategies[strategyId], "Strategy not approved");
        require(assets.length == amounts.length, "Array length mismatch");
        require(assets.length == executionData.length, "Execution data mismatch");
        
        // Check all assets are Halal-compliant
        for (uint256 i = 0; i < assets.length; i++) {
            require(HALAL_REGISTRY.isHalalCompliant(assets[i]), "Non-compliant asset");
        }
        
        // Validate AI prediction
        AIPrediction memory prediction = aiPredictions[aiPredictionId];
        require(prediction.timestamp > 0, "Invalid AI prediction");
        require(prediction.confidenceScore >= minAIConfidence, "AI confidence too low");
        require(block.timestamp <= prediction.timestamp + 300, "Prediction expired"); // 5 min expiry

        uint256 startTime = block.timestamp;
        uint256 totalCapitalRequired = _calculateRequiredCapital(amounts);
        
        // Check capital limits
        require(
            totalCapitalRequired <= (capitalLimits.totalCapitalUSD * capitalLimits.maxPositionSizePct) / 10000,
            "Position size exceeds limit"
        );

        // Execute strategy
        uint256 profitUSD = _executeStrategyLogic(strategyId, assets, amounts, executionData);
        uint256 executionTime = block.timestamp - startTime;

        // Update statistics
        _updateExecutionStats(strategyId, profitUSD, executionTime, prediction.confidenceScore);
        _updateDailyTracking(profitUSD);

        emit StrategyExecuted(
            strategyId,
            msg.sender,
            profitUSD,
            executionTime,
            prediction.confidenceScore
        );

        // Check if daily targets are met
        _checkDailyTargets();
    }

    /**
     * @dev Submit AI prediction for strategy execution
     */
    function submitAIPrediction(
        bytes32 predictionId,
        uint256 profitProbability,
        uint256 expectedProfitUSD,
        uint256 confidenceScore,
        uint256 riskScore,
        uint256 executionUrgency,
        bytes32 modelVersion
    ) external onlyAIAgent {
        require(profitProbability <= 10000, "Invalid profit probability");
        require(confidenceScore <= 10000, "Invalid confidence score");
        require(riskScore <= 10000, "Invalid risk score");

        aiPredictions[predictionId] = AIPrediction({
            profitProbability: profitProbability,
            expectedProfitUSD: expectedProfitUSD,
            confidenceScore: confidenceScore,
            riskScore: riskScore,
            executionUrgency: executionUrgency,
            timestamp: block.timestamp,
            modelVersion: modelVersion
        });

        emit AIPredictionReceived(
            predictionId,
            profitProbability,
            expectedProfitUSD,
            confidenceScore
        );
    }

    /**
     * @dev Distribute profit according to Mudarabah principles
     * @param token The token in which profit is realized
     * @param amount The amount of profit to distribute
     */
    function distributeProfit(
        address token,
        uint256 amount
    ) external onlyMudarib nonReentrant whenNotPaused onlyHalalAsset(token) {
        require(amount > 0, "Amount must be greater than 0");
        
        // Calculate shares
        uint256 investorShare = (amount * profitDistribution.investorShare) / 10000;
        uint256 mudaribShare = (amount * profitDistribution.mudaribShare) / 10000;
        uint256 zakatShare = (amount * profitDistribution.zakatShare) / 10000;
        uint256 reserveShare = (amount * profitDistribution.reserveShare) / 10000;
        
        // Distribute investor share proportionally
        if (investorShare > 0 && totalInvestorCapital > 0) {
            _distributeInvestorProfit(investorShare);
        }
        
        // Add to Zakat collection
        if (zakatShare > 0) {
            zakatCollected += zakatShare;
            emit ZakatCollected(zakatShare, block.timestamp);
        }
        
        // Update execution stats
        executionStats.totalProfitUSD += amount;
        
        emit ProfitDistributed(
            amount,
            investorShare,
            mudaribShare,
            zakatShare,
            reserveShare,
            block.timestamp
        );
    }

    /**
     * @dev Distribute loss according to Mudarabah principles (investors bear financial loss)
     * @param token The token in which loss is realized
     * @param amount The amount of loss to distribute
     */
    function distributeLoss(
        address token,
        uint256 amount
    ) external onlyMudarib nonReentrant whenNotPaused onlyHalalAsset(token) {
        require(amount > 0, "Amount must be greater than 0");
        
        // In Mudarabah, financial losses are borne by the capital providers (investors)
        // The Mudarib (manager) loses their time and effort
        if (totalInvestorCapital > 0) {
            _distributeInvestorLoss(amount);
        }
        
        // Update execution stats
        executionStats.totalLossUSD += amount;
        
        emit LossDistributed(
            amount,
            amount, // All loss goes to investors in Mudarabah
            block.timestamp
        );
    }

    /**
     * @dev Distribute Zakat to designated recipients
     * @param recipient The recipient of the Zakat
     * @param amount The amount to distribute
     */
    function distributeZakat(
        address recipient,
        uint256 amount
    ) external onlyZakatManager nonReentrant {
        require(recipient != address(0), "Invalid recipient");
        require(amount > 0, "Amount must be greater than 0");
        require(zakatCollected >= amount, "Insufficient Zakat collected");
        
        // Update Zakat collection
        zakatCollected -= amount;
        lastZakatDistribution = block.timestamp;
        
        // Transfer Zakat to recipient
        IERC20(supportedAssets[0]).safeTransfer(recipient, amount);
        
        emit ZakatDistributed(recipient, amount, block.timestamp);
    }

    /**
     * @dev Approve new Shariah-compliant strategy
     */
    function approveStrategy(
        bytes32 strategyId,
        uint256 allocation
    ) external onlyShariahAdvisor {
        require(!approvedStrategies[strategyId], "Strategy already approved");
        require(allocation <= capitalLimits.singleStrategyLimit, "Allocation exceeds limit");
        
        approvedStrategies[strategyId] = true;
        strategyAllocations[strategyId] = allocation;
        
        // Initialize strategy stats
        strategyStats[strategyId] = ExecutionStats({
            totalExecutions: 0,
            successfulExecutions: 0,
            totalProfitUSD: 0,
            totalLossUSD: 0,
            averageExecutionTime: 0,
            averageProfitPerTrade: 0,
            maxSingleProfit: 0,
            maxSingleLoss: 0
        });
    }

    /**
     * @dev Revoke approval for a strategy
     */
    function revokeStrategy(
        bytes32 strategyId
    ) external onlyShariahAdvisor {
        require(approvedStrategies[strategyId], "Strategy not approved");
        
        approvedStrategies[strategyId] = false;
        strategyAllocations[strategyId] = 0;
    }

    /**
     * @dev Update risk metrics
     */
    function updateRiskMetrics(
        uint256 valueAtRisk99,
        uint256 expectedShortfall,
        uint256 portfolioVolatility,
        uint256 maxCorrelation,
        uint256 stressTestResult,
        uint256 liquidityRisk
    ) external onlyRiskManager {
        riskMetrics.valueAtRisk99 = valueAtRisk99;
        riskMetrics.expectedShortfall = expectedShortfall;
        riskMetrics.portfolioVolatility = portfolioVolatility;
        riskMetrics.maxCorrelation = maxCorrelation;
        riskMetrics.stressTestResult = stressTestResult;
        riskMetrics.liquidityRisk = liquidityRisk;

        emit RiskMetricUpdated("VaR99", valueAtRisk99);
        emit RiskMetricUpdated("ExpectedShortfall", expectedShortfall);
        emit RiskMetricUpdated("PortfolioVolatility", portfolioVolatility);
    }

    /**
     * @dev Update profit distribution ratios
     */
    function updateProfitDistribution(
        uint256 _investorShare,
        uint256 _mudaribShare,
        uint256 _zakatShare,
        uint256 _reserveShare
    ) external onlyMudarib {
        require(
            _investorShare + _mudaribShare + _zakatShare + _reserveShare == 10000,
            "Shares must total 100%"
        );
        
        profitDistribution.investorShare = _investorShare;
        profitDistribution.mudaribShare = _mudaribShare;
        profitDistribution.zakatShare = _zakatShare;
        profitDistribution.reserveShare = _reserveShare;
    }

    /**
     * @dev Activate emergency shutdown
     */
    function activateEmergencyShutdown(
        string calldata reason
    ) external onlyMudarib {
        require(!emergencyShutdown, "Already in emergency shutdown");
        
        emergencyShutdown = true;
        
        emit EmergencyShutdownActivated(msg.sender, reason, block.timestamp);
    }

    /**
     * @dev Deactivate emergency shutdown
     */
    function deactivateEmergencyShutdown() external onlyMudarib {
        require(emergencyShutdown, "Not in emergency shutdown");
        
        emergencyShutdown = false;
        
        emit EmergencyShutdownDeactivated(msg.sender, block.timestamp);
    }    /**
     * @dev Request emergency withdrawal
     * @dev SECURITY FIX: Added role-based access control for emergency procedures
     */
    function requestEmergencyWithdrawal() 
        external 
        onlyRole(EMERGENCY_ROLE) 
        whenPaused 
        nonReentrant 
    {
        require(emergencyShutdown, "Not in emergency shutdown");
        require(investors[msg.sender].capitalInvested > 0, "No investment to withdraw");
        require(emergencyWithdrawalRequests[msg.sender] == 0, "Request already submitted");
        
        // Additional validation for emergency withdrawals
        require(
            block.timestamp >= emergencyShutdown + 1 hours, 
            "Emergency withdrawal cooling period not elapsed"
        );
        
        // Validate investor is in good standing
        require(
            !blacklistedInvestors[msg.sender], 
            "Investor is blacklisted"
        );
        
        emergencyWithdrawalRequests[msg.sender] = block.timestamp + emergencyWithdrawalDelay;
    }

    /**
     * @dev Calculate required capital for a strategy
     */
    function _calculateRequiredCapital(
        uint256[] memory amounts
    ) internal pure returns (uint256) {
        uint256 total = 0;
        for (uint256 i = 0; i < amounts.length; i++) {
            total += amounts[i];
        }
        return total;
    }

    /**
     * @dev Execute strategy logic
     */
    function _executeStrategyLogic(
        bytes32 strategyId,
        address[] memory assets,
        uint256[] memory amounts,
        bytes[] memory executionData
    ) internal returns (uint256) {
        // This would be implemented with actual trading logic
        // For now, we'll just return a simulated profit
        return 1000 * 1e6; // $1,000
    }

    /**
     * @dev Update execution statistics
     */
    function _updateExecutionStats(
        bytes32 strategyId,
        uint256 profitUSD,
        uint256 executionTime,
        uint256 confidenceScore
    ) internal {
        // Update global stats
        executionStats.totalExecutions++;
        if (profitUSD > 0) {
            executionStats.successfulExecutions++;
            executionStats.totalProfitUSD += profitUSD;
            
            if (profitUSD > executionStats.maxSingleProfit) {
                executionStats.maxSingleProfit = profitUSD;
            }
        } else {
            uint256 lossUSD = profitUSD == 0 ? 0 : uint256(-int256(profitUSD));
            executionStats.totalLossUSD += lossUSD;
            
            if (lossUSD > executionStats.maxSingleLoss) {
                executionStats.maxSingleLoss = lossUSD;
            }
        }
        
        // Update average execution time
        executionStats.averageExecutionTime = (
            (executionStats.averageExecutionTime * (executionStats.totalExecutions - 1)) + 
            executionTime
        ) / executionStats.totalExecutions;
        
        // Update average profit per trade
        if (executionStats.successfulExecutions > 0) {
            executionStats.averageProfitPerTrade = 
                executionStats.totalProfitUSD / executionStats.successfulExecutions;
        }
        
        // Update strategy-specific stats
        strategyStats[strategyId].totalExecutions++;
        if (profitUSD > 0) {
            strategyStats[strategyId].successfulExecutions++;
            strategyStats[strategyId].totalProfitUSD += profitUSD;
            
            if (profitUSD > strategyStats[strategyId].maxSingleProfit) {
                strategyStats[strategyId].maxSingleProfit = profitUSD;
            }
        } else {
            uint256 lossUSD = profitUSD == 0 ? 0 : uint256(-int256(profitUSD));
            strategyStats[strategyId].totalLossUSD += lossUSD;
            
            if (lossUSD > strategyStats[strategyId].maxSingleLoss) {
                strategyStats[strategyId].maxSingleLoss = lossUSD;
            }
        }
    }

    /**
     * @dev Update daily tracking
     */
    function _updateDailyTracking(uint256 profitUSD) internal {
        uint256 today = block.timestamp / 1 days;
        
        if (profitUSD > 0) {
            dailyProfits[today] += profitUSD;
        } else {
            uint256 lossUSD = profitUSD == 0 ? 0 : uint256(-int256(profitUSD));
            dailyLosses[today] += lossUSD;
        }
        
        dailyExecutions[today]++;
        
        emit DailyPerformanceReport(
            today,
            dailyProfits[today],
            dailyLosses[today],
            dailyProfits[today] > dailyLosses[today] ? 
                dailyProfits[today] - dailyLosses[today] : 
                0,
            dailyExecutions[today]
        );
    }

    /**
     * @dev Check if daily targets are met
     */
    function _checkDailyTargets() internal view {
        uint256 today = block.timestamp / 1 days;
        
        // Check if daily loss limit is exceeded
        if (dailyLosses[today] > performanceTargets.maxDailyLossUSD) {
            revert("Daily loss limit exceeded");
        }
        
        // Check success rate
        if (dailyExecutions[today] > 10) {
            uint256 successRate = (dailyProfits[today] * 10000) / 
                (dailyProfits[today] + dailyLosses[today]);
            
            if (successRate < performanceTargets.minSuccessRate) {
                revert("Success rate below target");
            }
        }
    }

    /**
     * @dev Check risk limits
     */
    function _checkRiskLimits() internal view {
        // Check VaR limit
        if (riskMetrics.valueAtRisk99 > capitalLimits.totalCapitalUSD / 20) { // 5% VaR limit
            revert("VaR limit exceeded");
        }
        
        // Check portfolio volatility
        if (riskMetrics.portfolioVolatility > 2000) { // 20% volatility limit
            revert("Volatility limit exceeded");
        }
        
        // Check liquidity risk
        if (riskMetrics.liquidityRisk > 7000) { // 70% liquidity risk limit
            revert("Liquidity risk limit exceeded");
        }
    }

    /**
     * @dev Distribute profit to investors proportionally
     */
    function _distributeInvestorProfit(uint256 amount) internal {
        if (amount == 0 || totalInvestorCapital == 0) {
            return;
        }
        
        for (uint256 i = 0; i < investorList.length; i++) {
            address investor = investorList[i];
            uint256 investorCapital = investors[investor].capitalInvested;
            
            if (investorCapital > 0) {
                // Calculate proportional profit share
                uint256 investorProfit = (amount * investorCapital) / totalInvestorCapital;
                
                // Update investor's profit share
                investors[investor].profitShare += investorProfit;
            }
        }
    }

    /**
     * @dev Distribute loss to investors proportionally
     */
    function _distributeInvestorLoss(uint256 amount) internal {
        if (amount == 0 || totalInvestorCapital == 0) {
            return;
        }
        
        for (uint256 i = 0; i < investorList.length; i++) {
            address investor = investorList[i];
            uint256 investorCapital = investors[investor].capitalInvested;
            
            if (investorCapital > 0) {
                // Calculate proportional loss share
                uint256 investorLoss = (amount * investorCapital) / totalInvestorCapital;
                
                // Update investor's loss share
                investors[investor].lossShare += investorLoss;
            }
        }
    }

    /**
     * @dev Pause the contract
     */
    function pause() external onlyMudarib {
        _pause();
    }

    /**
     * @dev Unpause the contract
     */
    function unpause() external onlyMudarib {
        _unpause();
    }
    
    /**
     * @dev Update profit distribution ratios
     * @param _investorShare Investor share (basis points)
     * @param _mudaribShare Mudarib share (basis points)
     * @param _zakatShare Zakat share (basis points)
     * @param _reserveShare Reserve share (basis points)
     */
    function updateProfitDistribution(
        uint256 _investorShare,
        uint256 _mudaribShare,
        uint256 _zakatShare,
        uint256 _reserveShare
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        // Ensure investor share is at least 50% to maintain Shariah compliance
        require(_investorShare >= 5000, "Investor share must be at least 50%");
        
        // Ensure Zakat share is at least 2.5% to maintain Shariah compliance
        require(_zakatShare >= 250, "Zakat share must be at least 2.5%");
        
        // Ensure total is 100%
        require(
            _investorShare + _mudaribShare + _zakatShare + _reserveShare == 10000,
            "Profit distribution must total 100%"
        );
        
        // Update profit distribution
        profitDistribution.investorShare = _investorShare;
        profitDistribution.mudaribShare = _mudaribShare;
        profitDistribution.zakatShare = _zakatShare;
        profitDistribution.reserveShare = _reserveShare;
        
        emit ProfitDistributionUpdated(
            _investorShare,
            _mudaribShare,
            _zakatShare,
            _reserveShare
        );
    }

    // ==================== V51: Advanced Risk & Portfolio Console ====================

    /**
     * @dev Update Value-at-Risk (VaR) metrics
     * @param _valueAtRisk99 99% VaR value
     * @param _expectedShortfall Expected shortfall value
     */
    function updateVaRMetrics(
        uint256 _valueAtRisk99,
        uint256 _expectedShortfall
    ) external onlyRiskManager {
        riskMetrics.valueAtRisk99 = _valueAtRisk99;
        riskMetrics.expectedShortfall = _expectedShortfall;
        riskMetrics.lastVaRUpdateTime = block.timestamp;
        
        emit VaRUpdated(
            _valueAtRisk99,
            _expectedShortfall,
            block.timestamp
        );
        
        emit RiskMetricUpdated("valueAtRisk99", _valueAtRisk99);
        emit RiskMetricUpdated("expectedShortfall", _expectedShortfall);
    }
    
    /**
     * @dev Update portfolio volatility
     * @param _portfolioVolatility New portfolio volatility value
     */
    function updatePortfolioVolatility(
        uint256 _portfolioVolatility
    ) external onlyRiskManager {
        riskMetrics.portfolioVolatility = _portfolioVolatility;
        
        emit RiskMetricUpdated("portfolioVolatility", _portfolioVolatility);
    }
    
    /**
     * @dev Update correlation between two assets
     * @param _asset1 First asset address
     * @param _asset2 Second asset address
     * @param _correlation Correlation value in basis points (-10000 to 10000)
     */
    function updateCorrelation(
        address _asset1,
        address _asset2,
        int256 _correlation
    ) external onlyRiskManager validAssetPair(_asset1, _asset2) {
        require(_correlation >= -10000 && _correlation <= 10000, "Correlation out of range");
        
        // Ensure consistent ordering of assets
        (address asset1, address asset2) = _asset1 < _asset2 ? (_asset1, _asset2) : (_asset2, _asset1);
        
        // Generate unique key for the asset pair
        bytes32 correlationKey = keccak256(abi.encodePacked(asset1, asset2));
        
        // Check if this pair already exists
        bool pairExists = false;
        if (correlationMatrix[correlationKey].asset1 != address(0)) {
            pairExists = true;
        }
        
        // Update correlation data
        correlationMatrix[correlationKey] = CorrelationData({
            asset1: asset1,
            asset2: asset2,
            correlation: _correlation,
            updateTime: block.timestamp
        });
        
        // Add to correlation pairs if new
        if (!pairExists) {
            correlationPairs.push(correlationKey);
        }
        
        emit CorrelationUpdated(
            asset1,
            asset2,
            _correlation,
            block.timestamp
        );
    }
    
    /**
     * @dev Create a new stress test scenario
     * @param _name Scenario name
     * @param _description Scenario description
     * @return scenarioId The ID of the created scenario
     */
    function createStressTestScenario(
        string calldata _name,
        string calldata _description
    ) external onlyRiskManager returns (uint256) {
        require(bytes(_name).length > 0, "Name cannot be empty");
        
        uint256 scenarioId = nextStressTestScenarioId++;
        
        StressTestScenario storage scenario = stressTestScenarios[scenarioId];
        scenario.name = _name;
        scenario.description = _description;
        scenario.creationTime = block.timestamp;
        scenario.creator = msg.sender;
        scenario.isActive = true;
        
        emit StressTestScenarioCreated(
            scenarioId,
            _name,
            msg.sender,
            block.timestamp
        );
        
        return scenarioId;
    }
    
    /**
     * @dev Set asset impact for a stress test scenario
     * @param _scenarioId Scenario ID
     * @param _asset Asset address
     * @param _impactBasisPoints Impact in basis points (can be negative)
     */
    function setStressTestAssetImpact(
        uint256 _scenarioId,
        address _asset,
        int256 _impactBasisPoints
    ) external onlyRiskManager onlyHalalAsset(_asset) {
        require(_scenarioId > 0 && _scenarioId < nextStressTestScenarioId, "Invalid scenario ID");
        require(_impactBasisPoints >= -10000 && _impactBasisPoints <= 10000, "Impact out of range");
        
        StressTestScenario storage scenario = stressTestScenarios[_scenarioId];
        require(scenario.isActive, "Scenario not active");
        
        scenario.assetImpacts[_asset] = _impactBasisPoints;
    }
    
    /**
     * @dev Execute a stress test and record the results
     * @param _scenarioId Scenario ID
     * @param _portfolioValueBefore Portfolio value before stress test
     * @param _portfolioValueAfter Portfolio value after stress test
     */
    function recordStressTestResults(
        uint256 _scenarioId,
        uint256 _portfolioValueBefore,
        uint256 _portfolioValueAfter
    ) external onlyRiskManager {
        require(_scenarioId > 0 && _scenarioId < nextStressTestScenarioId, "Invalid scenario ID");
        require(_portfolioValueBefore > 0, "Invalid portfolio value");
        
        // Calculate impact percentage
        int256 impactPercentage;
        if (_portfolioValueAfter >= _portfolioValueBefore) {
            impactPercentage = int256((_portfolioValueAfter - _portfolioValueBefore) * 10000 / _portfolioValueBefore);
        } else {
            impactPercentage = -int256((_portfolioValueBefore - _portfolioValueAfter) * 10000 / _portfolioValueBefore);
        }
        
        // Update risk metrics
        riskMetrics.stressTestResult = _portfolioValueAfter;
        riskMetrics.stressTestScenarioId = _scenarioId;
        lastStressTestTimestamp = block.timestamp;
        
        emit StressTestExecuted(
            _scenarioId,
            _portfolioValueBefore,
            _portfolioValueAfter,
            impactPercentage,
            block.timestamp
        );
        
        emit RiskMetricUpdated("stressTestResult", _portfolioValueAfter);
    }
    
    /**
     * @dev Get all correlation pairs
     * @return Array of correlation keys
     */
    function getCorrelationPairs() external view returns (bytes32[] memory) {
        return correlationPairs;
    }
    
    /**
     * @dev Get correlation data for a specific asset pair
     * @param _asset1 First asset address
     * @param _asset2 Second asset address
     * @return Correlation data
     */
    function getAssetCorrelation(
        address _asset1,
        address _asset2
    ) external view returns (CorrelationData memory) {
        // Ensure consistent ordering of assets
        (address asset1, address asset2) = _asset1 < _asset2 ? (_asset1, _asset2) : (_asset2, _asset1);
        
        // Generate unique key for the asset pair
        bytes32 correlationKey = keccak256(abi.encodePacked(asset1, asset2));
        
        return correlationMatrix[correlationKey];
    }
    
    /**
     * @dev Get stress test scenario details
     * @param _scenarioId Scenario ID
     * @return name Scenario name
     * @return description Scenario description
     * @return creationTime Creation timestamp
     * @return creator Creator address
     * @return isActive Whether the scenario is active
     */
    function getStressTestScenario(
        uint256 _scenarioId
    ) external view returns (
        string memory name,
        string memory description,
        uint256 creationTime,
        address creator,
        bool isActive
    ) {
        require(_scenarioId > 0 && _scenarioId < nextStressTestScenarioId, "Invalid scenario ID");
        
        StressTestScenario storage scenario = stressTestScenarios[_scenarioId];
        
        return (
            scenario.name,
            scenario.description,
            scenario.creationTime,
            scenario.creator,
            scenario.isActive
        );
    }
    
    /**
     * @dev Get asset impact for a stress test scenario
     * @param _scenarioId Scenario ID
     * @param _asset Asset address
     * @return Impact in basis points
     */
    function getStressTestAssetImpact(
        uint256 _scenarioId,
        address _asset
    ) external view returns (int256) {
        require(_scenarioId > 0 && _scenarioId < nextStressTestScenarioId, "Invalid scenario ID");
        
        return stressTestScenarios[_scenarioId].assetImpacts[_asset];
    }
    
    // ==================== V55: AI Action Safeguards ====================
    
    /**
     * @dev Propose an AI action with timelock
     * @param strategyId The strategy ID
     * @param valueUSD The value of the transaction in USD
     * @param executionData The execution data
     * @return actionId The ID of the proposed action
     */
    function proposeAIAction(
        bytes32 strategyId,
        uint256 valueUSD,
        bytes calldata executionData
    ) external onlyAIAgent returns (bytes32 actionId) {
        // Check if strategy is approved
        require(approvedStrategies[strategyId], "Strategy not approved");
        
        // Check value limit
        require(valueUSD <= maxTransactionValueUSD, "Transaction value exceeds limit");
        
        // Check daily transaction limit
        uint256 today = block.timestamp / 1 days;
        require(dailyTransactionCount[today] < maxDailyTransactionLimit, "Daily transaction limit reached");
        
        // Generate action ID
        actionId = keccak256(abi.encodePacked(
            strategyId,
            valueUSD,
            executionData,
            block.timestamp,
            msg.sender
        ));
        
        // Set execution time with timelock
        uint256 executionTime = block.timestamp + aiActionTimelock;
        pendingAIActions[actionId] = executionTime;
        
        // Increment daily transaction count
        dailyTransactionCount[today]++;
        
        emit AIActionProposed(
            actionId,
            msg.sender,
            strategyId,
            valueUSD,
            executionTime
        );
        
        return actionId;
    }
    
    /**
     * @dev Cancel a pending AI action
     * @param actionId The ID of the action to cancel
     * @param reason The reason for cancellation
     */
    function cancelAIAction(
        bytes32 actionId,
        string calldata reason
    ) external {
        // Only allow cancellation by AI agent, risk manager, or Shariah advisor
        require(
            hasRole(AI_AGENT_ROLE, msg.sender) ||
            hasRole(RISK_MANAGER_ROLE, msg.sender) ||
            hasRole(SHARIAH_ADVISOR_ROLE, msg.sender),
            "Not authorized to cancel"
        );
        
        // Check if action exists and is pending
        require(pendingAIActions[actionId] > 0, "Action not found");
        require(pendingAIActions[actionId] > block.timestamp, "Action already executable");
        
        // Cancel action
        delete pendingAIActions[actionId];
        
        emit AIActionCancelled(
            actionId,
            msg.sender,
            reason
        );
    }
    
    /**
     * @dev Execute a pending AI action after timelock
     * @param actionId The ID of the action to execute
     * @param strategyId The strategy ID
     * @param valueUSD The value of the transaction in USD
     * @param executionData The execution data
     */
    function executeAIAction(
        bytes32 actionId,
        bytes32 strategyId,
        uint256 valueUSD,
        bytes calldata executionData
    ) external onlyExecution nonReentrant {
        // Check if action exists and timelock has passed
        require(pendingAIActions[actionId] > 0, "Action not found");
        require(pendingAIActions[actionId] <= block.timestamp, "Timelock not expired");
        
        // Verify action parameters match
        bytes32 calculatedActionId = keccak256(abi.encodePacked(
            strategyId,
            valueUSD,
            executionData,
            pendingAIActions[actionId] - aiActionTimelock,
            aiAgent
        ));
        
        require(calculatedActionId == actionId, "Action parameters mismatch");
        
        // Remove from pending actions
        delete pendingAIActions[actionId];
        
        // Execute the action
        // This is a simplified implementation - in a real system, this would
        // execute the strategy with the provided parameters
        
        emit AIActionExecuted(
            actionId,
            msg.sender,
            strategyId,
            valueUSD
        );
    }
    
    /**
     * @dev Update AI action safeguard limits
     * @param _maxDailyTransactionLimit Maximum number of transactions per day
     * @param _maxTransactionValueUSD Maximum value per transaction in USD
     * @param _aiActionTimelock Time delay for AI-proposed actions
     */
    function updateAISafeguardLimits(
        uint256 _maxDailyTransactionLimit,
        uint256 _maxTransactionValueUSD,
        uint256 _aiActionTimelock
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        // Store old values for events
        uint256 oldMaxDailyTransactionLimit = maxDailyTransactionLimit;
        uint256 oldMaxTransactionValueUSD = maxTransactionValueUSD;
        uint256 oldAIActionTimelock = aiActionTimelock;
        
        // Update limits
        maxDailyTransactionLimit = _maxDailyTransactionLimit;
        maxTransactionValueUSD = _maxTransactionValueUSD;
        aiActionTimelock = _aiActionTimelock;
        
        // Emit events
        emit SafeguardLimitUpdated(
            "maxDailyTransactionLimit",
            oldMaxDailyTransactionLimit,
            _maxDailyTransactionLimit,
            msg.sender
        );
        
        emit SafeguardLimitUpdated(
            "maxTransactionValueUSD",
            oldMaxTransactionValueUSD,
            _maxTransactionValueUSD,
            msg.sender
        );
        
        emit SafeguardLimitUpdated(
            "aiActionTimelock",
            oldAIActionTimelock,
            _aiActionTimelock,
            msg.sender
        );
    }
    
    /**
     * @dev Get pending AI action details
     * @param actionId The ID of the action
     * @return executionTime The time when the action can be executed
     * @return isPending Whether the action is still pending
     */
    function getPendingAIAction(
        bytes32 actionId
    ) external view returns (uint256 executionTime, bool isPending) {
        executionTime = pendingAIActions[actionId];
        isPending = (executionTime > 0 && executionTime > block.timestamp);
        return (executionTime, isPending);
    }
    
    /**
     * @dev Get daily transaction count
     * @param day The day to check (timestamp / 1 days)
     * @return count The number of transactions for the day
     */
    function getDailyTransactionCount(
        uint256 day
    ) external view returns (uint256 count) {
        return dailyTransactionCount[day];
    }
}