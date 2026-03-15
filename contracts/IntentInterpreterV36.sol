// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "./TrustCurve.sol";
import "./interfaces/IGenericStrategy.sol";

/**
 * @title IntentInterpreterV36
 * @notice Interprets high-level intents and translates them into strategy execution parameters
 * @dev Part of the V36 Intent-Aware Kernel architecture
 */
contract IntentInterpreterV36 is Ownable {
    // Trust curve contract for strategy scoring
    TrustCurve public immutable TRUST_CURVE;
    
    // Intent types
    enum IntentType {
        MaximizeProfit,      // Maximize profit with standard risk
        MinimizeRisk,        // Minimize risk, accept lower profits
        BalancedApproach,    // Balance risk and reward
        AggressiveGrowth,    // Maximize profit with higher risk tolerance
        PreserveCapital,     // Focus on capital preservation
        Custom               // Custom intent with specific parameters
    }
    
    // Intent parameters
    struct IntentParameters {
        uint256 maxCapitalAtRisk;     // Maximum capital that can be used (basis points of total)
        uint256 minProfitThreshold;   // Minimum profit required to execute (basis points)
        uint256 maxSlippage;          // Maximum allowed slippage (basis points)
        uint256 maxGasPrice;          // Maximum gas price willing to pay (gwei)
        uint256 timeHorizon;          // Time horizon for the strategy (seconds)
        uint256 confidenceThreshold;  // Minimum confidence required (basis points)
    }
    
    // Default parameters for each intent type
    mapping(IntentType => IntentParameters) public defaultIntentParameters;
    
    // Strategy rankings based on intent type
    struct StrategyRanking {
        uint256 strategyId;
        uint256 score;
    }
    
    // Events
    event IntentInterpreted(
        address indexed user,
        IntentType intentType,
        bytes32 intentHash,
        uint256 timestamp
    );
    
    event StrategyRecommended(
        bytes32 indexed intentHash,
        uint256 indexed strategyId,
        uint256 score,
        uint256 rank
    );
    
    event DefaultParametersUpdated(
        IntentType indexed intentType,
        IntentParameters parameters
    );
    
    /**
     * @dev Constructor
     * @param _trustCurveAddress Address of the TrustCurve contract
     */
    constructor(address _trustCurveAddress) Ownable(msg.sender) {
        require(_trustCurveAddress != address(0), "Invalid TrustCurve address");
        TRUST_CURVE = TrustCurve(_trustCurveAddress);
        
        // Initialize default parameters for each intent type
        _initializeDefaultParameters();
    }
    
    /**
     * @dev Initialize default parameters for each intent type
     */
    function _initializeDefaultParameters() internal {
        // MaximizeProfit
        defaultIntentParameters[IntentType.MaximizeProfit] = IntentParameters({
            maxCapitalAtRisk: 5000,    // 50% of capital
            minProfitThreshold: 50,    // 0.5% minimum profit
            maxSlippage: 100,          // 1% max slippage
            maxGasPrice: 50,           // 50 gwei
            timeHorizon: 1 hours,      // 1 hour time horizon
            confidenceThreshold: 7000  // 70% confidence
        });
        
        // MinimizeRisk
        defaultIntentParameters[IntentType.MinimizeRisk] = IntentParameters({
            maxCapitalAtRisk: 1000,    // 10% of capital
            minProfitThreshold: 100,   // 1% minimum profit
            maxSlippage: 50,           // 0.5% max slippage
            maxGasPrice: 30,           // 30 gwei
            timeHorizon: 4 hours,      // 4 hour time horizon
            confidenceThreshold: 9000  // 90% confidence
        });
        
        // BalancedApproach
        defaultIntentParameters[IntentType.BalancedApproach] = IntentParameters({
            maxCapitalAtRisk: 3000,    // 30% of capital
            minProfitThreshold: 75,    // 0.75% minimum profit
            maxSlippage: 75,           // 0.75% max slippage
            maxGasPrice: 40,           // 40 gwei
            timeHorizon: 2 hours,      // 2 hour time horizon
            confidenceThreshold: 8000  // 80% confidence
        });
        
        // AggressiveGrowth
        defaultIntentParameters[IntentType.AggressiveGrowth] = IntentParameters({
            maxCapitalAtRisk: 8000,    // 80% of capital
            minProfitThreshold: 25,    // 0.25% minimum profit
            maxSlippage: 200,          // 2% max slippage
            maxGasPrice: 100,          // 100 gwei
            timeHorizon: 30 minutes,   // 30 minute time horizon
            confidenceThreshold: 6000  // 60% confidence
        });
        
        // PreserveCapital
        defaultIntentParameters[IntentType.PreserveCapital] = IntentParameters({
            maxCapitalAtRisk: 500,     // 5% of capital
            minProfitThreshold: 150,   // 1.5% minimum profit
            maxSlippage: 25,           // 0.25% max slippage
            maxGasPrice: 20,           // 20 gwei
            timeHorizon: 6 hours,      // 6 hour time horizon
            confidenceThreshold: 9500  // 95% confidence
        });
        
        // Custom - initialized with balanced defaults
        defaultIntentParameters[IntentType.Custom] = defaultIntentParameters[IntentType.BalancedApproach];
    }
    
    /**
     * @dev Interpret a high-level intent and return execution parameters
     * @param _intentType Type of intent
     * @param _customParameters Custom parameters (only used if intentType is Custom)
     * @param _availableStrategies Array of available strategy IDs
     * @return intentHash Hash of the intent
     * @return parameters Execution parameters
     * @return rankedStrategies Ranked strategies based on intent
     */
    function interpretIntent(
        IntentType _intentType,
        IntentParameters memory _customParameters,
        uint256[] memory _availableStrategies
    ) external returns (
        bytes32 intentHash,
        IntentParameters memory parameters,
        StrategyRanking[] memory rankedStrategies
    ) {
        // Get parameters based on intent type
        parameters = _intentType == IntentType.Custom
            ? _customParameters
            : defaultIntentParameters[_intentType];
        
        // Generate intent hash
        intentHash = keccak256(abi.encode(
            msg.sender,
            _intentType,
            parameters,
            block.timestamp
        ));
        
        // Rank strategies based on intent
        rankedStrategies = _rankStrategies(_intentType, parameters, _availableStrategies);
        
        // Emit event
        emit IntentInterpreted(
            msg.sender,
            _intentType,
            intentHash,
            block.timestamp
        );
        
        // Emit events for strategy recommendations
        for (uint i = 0; i < rankedStrategies.length; i++) {
            emit StrategyRecommended(
                intentHash,
                rankedStrategies[i].strategyId,
                rankedStrategies[i].score,
                i + 1
            );
        }
        
        return (intentHash, parameters, rankedStrategies);
    }
    
    /**
     * @dev Rank strategies based on intent
     * @param _intentType Type of intent
     * @param _parameters Intent parameters
     * @param _availableStrategies Array of available strategy IDs
     * @return rankedStrategies Ranked strategies based on intent
     */
    function _rankStrategies(
        IntentType _intentType,
        IntentParameters memory _parameters,
        uint256[] memory _availableStrategies
    ) internal view returns (StrategyRanking[] memory rankedStrategies) {
        uint256 strategyCount = _availableStrategies.length;
        rankedStrategies = new StrategyRanking[](strategyCount);
        
        // Calculate score for each strategy
        for (uint i = 0; i < strategyCount; i++) {
            uint256 strategyId = _availableStrategies[i];
            uint256 trustScore = TRUST_CURVE.getTrustScore(strategyId);
            
            // Get strategy scorecard
            TrustCurve.StrategyScorecard memory scorecard = TRUST_CURVE.getStrategyScorecard(strategyId);
            
            // Calculate intent-specific score
            uint256 intentScore = _calculateIntentScore(
                _intentType,
                _parameters,
                trustScore,
                scorecard
            );
            
            rankedStrategies[i] = StrategyRanking({
                strategyId: strategyId,
                score: intentScore
            });
        }
        
        // Sort strategies by score (descending)
        _sortStrategiesByScore(rankedStrategies);
        
        return rankedStrategies;
    }
    
    /**
     * @dev Calculate intent-specific score for a strategy
     * @param _intentType Type of intent
     * @param _parameters Intent parameters
     * @param _trustScore Trust score from TrustCurve
     * @param _scorecard Strategy scorecard
     * @return score Intent-specific score
     */
    function _calculateIntentScore(
        IntentType _intentType,
        IntentParameters memory _parameters,
        uint256 _trustScore,
        TrustCurve.StrategyScorecard memory _scorecard
    ) internal pure returns (uint256 score) {
        // Base score is the trust score
        score = _trustScore;
        
        // Adjust score based on intent type
        if (_intentType == IntentType.MaximizeProfit) {
            // Prioritize profit over safety
            score = score * 70 / 100 + (_scorecard.totalProfitVerified * 30 / 1e18);
        } else if (_intentType == IntentType.MinimizeRisk) {
            // Prioritize win rate over profit
            score = score * 30 / 100 + (_scorecard.winRate * 70 / 100);
        } else if (_intentType == IntentType.BalancedApproach) {
            // Equal weight to trust score, win rate, and profit
            score = score * 40 / 100 + (_scorecard.winRate * 30 / 100) + (_scorecard.totalProfitVerified * 30 / 1e18);
        } else if (_intentType == IntentType.AggressiveGrowth) {
            // Heavily prioritize profit
            score = score * 20 / 100 + (_scorecard.totalProfitVerified * 80 / 1e18);
        } else if (_intentType == IntentType.PreserveCapital) {
            // Heavily prioritize win rate
            score = score * 20 / 100 + (_scorecard.winRate * 80 / 100);
        } else if (_intentType == IntentType.Custom) {
            // Custom weighting based on parameters
            uint256 riskWeight = _parameters.maxCapitalAtRisk / 100; // 0-100 scale
            score = score * (100 - riskWeight) / 100 + (_scorecard.totalProfitVerified * riskWeight / 1e18);
        }
        
        return score;
    }
    
    /**
     * @dev Sort strategies by score (descending)
     * @param _strategies Array of strategy rankings
     */
    function _sortStrategiesByScore(StrategyRanking[] memory _strategies) internal pure {
        uint256 length = _strategies.length;
        
        for (uint i = 0; i < length; i++) {
            for (uint j = i + 1; j < length; j++) {
                if (_strategies[i].score < _strategies[j].score) {
                    StrategyRanking memory temp = _strategies[i];
                    _strategies[i] = _strategies[j];
                    _strategies[j] = temp;
                }
            }
        }
    }
    
    /**
     * @dev Update default parameters for an intent type
     * @param _intentType Type of intent
     * @param _parameters New default parameters
     */
    function updateDefaultParameters(
        IntentType _intentType,
        IntentParameters memory _parameters
    ) external onlyOwner nonReentrant{
        defaultIntentParameters[_intentType] = _parameters;
        
        emit DefaultParametersUpdated(_intentType, _parameters);
    }
    
    /**
     * @dev Get default parameters for an intent type
     * @param _intentType Type of intent
     * @return parameters Default parameters
     */
    function getDefaultParameters(IntentType _intentType) external view returns (IntentParameters memory)  {
        // TODO: Add nonReentrant modifier
        return defaultIntentParameters[_intentType];
    }
    
    /**
     * @dev Get ranked strategies for an intent
     * @param _intentType Type of intent
     * @param _parameters Intent parameters
     * @param _availableStrategies Array of available strategy IDs
     * @return rankedStrategies Ranked strategies based on intent
     */
    function getRankedStrategies(
        IntentType _intentType,
        IntentParameters memory _parameters,
        uint256[] memory _availableStrategies
    ) external view returns (StrategyRanking[] memory)  {
        // TODO: Add nonReentrant modifier
        return _rankStrategies(_intentType, _parameters, _availableStrategies);
    }
}
