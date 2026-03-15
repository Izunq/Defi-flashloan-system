// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

/**
 * @title TrustCurve
 * @notice Calculates a dynamic "Trust Score" for strategies.
 * @dev This score is a function of ZK proof validity, age, and historical performance.
 */
contract TrustCurve is Ownable, ReentrancyGuard {
    struct StrategyScorecard {
        uint256 lastVerifiedAt; // Timestamp of last valid ZK proof
        uint256 totalProfitVerified; // Sum of all zk-verified profits
        uint8 winRate; // Based on on-chain execution results
        uint256 trustScore;
        uint256 totalExecutions;
        uint256 successfulExecutions;
        uint256 verifiedIntelligenceScore; // Score based on ZK-RL proof verification
        bool hasZKRLProof; // Whether the strategy has a valid ZK-RL proof
    }

    mapping(uint256 => StrategyScorecard) public scorecards; // strategyId -> Scorecard

    // Constants for trust score calculation
    uint256 public constant MAX_PROOF_AGE = 30 days;
    uint256 public constant RECENCY_WEIGHT = 30; // 30% weight for recency
    uint256 public constant PERFORMANCE_WEIGHT = 70; // 70% weight for performance
    uint256 public constant INTELLIGENCE_WEIGHT = 20; // 20% weight for verified intelligence

    event TrustScoreUpdated(uint256 indexed strategyId, uint256 newScore);
    event StrategyPerformanceUpdated(uint256 indexed strategyId, bool success, int256 profit);
    event ZKVerificationUpdated(uint256 indexed strategyId, bool isValid);
    event ZKRLProofVerified(uint256 indexed strategyId, uint256 intelligenceScore, bool isValid);

    constructor() Ownable(msg.sender) {}

    /**
     * @dev Update strategy performance based on execution results
     * @param _strategyId The ID of the strategy
     * @param _isSuccess Whether the execution was successful
     * @param _profit The profit (or loss if negative) from the execution
     */
    function updateOnChainPerformance(uint256 _strategyId, bool _isSuccess, int256 _profit) external onlyOwner nonReentrant{
        StrategyScorecard storage card = scorecards[_strategyId];
        
        // Update execution stats
        card.totalExecutions += 1;
        
        if (_isSuccess) {
            card.successfulExecutions += 1;
            
            // Only add positive profits to the total
            if (_profit > 0) {
                card.totalProfitVerified += uint256(_profit);
            }
        }
        
        // Update win rate
        if (card.totalExecutions > 0) {
            card.winRate = uint8((card.successfulExecutions * 100) / card.totalExecutions);
        }
        
        _recalculateTrustScore(_strategyId);
        
        emit StrategyPerformanceUpdated(_strategyId, _isSuccess, _profit);
    }
    
    /**
     * @dev Update ZK verification status for a strategy
     * @param _strategyId The ID of the strategy
     * @param _isValid Whether the ZK proof is valid
     */
    function updateZKVerification(uint256 _strategyId, bool _isValid) external onlyOwner nonReentrant{
        if (_isValid) {
            scorecards[_strategyId].lastVerifiedAt = block.timestamp;
        }
        _recalculateTrustScore(_strategyId);
        
        emit ZKVerificationUpdated(_strategyId, _isValid);
    }
    
    /**
     * @dev Update ZK-RL proof verification status for a strategy
     * @param _strategyId The ID of the strategy
     * @param _intelligenceScore The verified intelligence score (0-100)
     * @param _isValid Whether the ZK-RL proof is valid
     */
    function updateZKRLVerification(
        uint256 _strategyId, 
        uint256 _intelligenceScore, 
        bool _isValid
    ) external onlyOwner nonReentrant{
        require(_intelligenceScore <= 100, "Intelligence score must be 0-100");
        
        StrategyScorecard storage card = scorecards[_strategyId];
        
        if (_isValid) {
            card.verifiedIntelligenceScore = _intelligenceScore;
            card.hasZKRLProof = true;
            card.lastVerifiedAt = block.timestamp; // Also update the last verification time
        }
        
        _recalculateTrustScore(_strategyId);
        
        emit ZKRLProofVerified(_strategyId, _intelligenceScore, _isValid);
    }

    /**
     * @dev Recalculate the trust score for a strategy
     * @param _strategyId The ID of the strategy
     */
    function _recalculateTrustScore(uint256 _strategyId) internal {
        StrategyScorecard storage card = scorecards[_strategyId];
        
        // Calculate recency score (0-100)
        uint256 timeSinceProof = block.timestamp - card.lastVerifiedAt;
        uint256 recencyBonus = 0;
        
        if (card.lastVerifiedAt > 0) {
            recencyBonus = (MAX_PROOF_AGE - Math.min(timeSinceProof, MAX_PROOF_AGE)) * 100 / MAX_PROOF_AGE;
        }
        
        // Calculate performance score based on win rate and total profit
        uint256 performanceScore = 0;
        if (card.totalExecutions > 0) {
            // Normalize profit to a 0-100 scale (assuming 1e18 is a reasonable max profit)
            uint256 normalizedProfit = Math.min(card.totalProfitVerified, 1e18) * 100 / 1e18;
            performanceScore = (uint256(card.winRate) + normalizedProfit) / 2;
        }
        
        // Calculate final trust score
        uint256 newTrustScore;
        
        if (card.hasZKRLProof) {
            // If the strategy has a verified intelligence score, include it in the calculation
            // Adjust weights to include intelligence: recency (25%), performance (55%), intelligence (20%)
            newTrustScore = (
                recencyBonus * 25 + 
                performanceScore * 55 + 
                card.verifiedIntelligenceScore * 20
            ) / 100;
            
            // Add a bonus for having a verified ZK-RL proof
            newTrustScore = Math.min(100, newTrustScore + 5);
        } else {
            // Original calculation without intelligence score
            newTrustScore = (recencyBonus * RECENCY_WEIGHT + performanceScore * PERFORMANCE_WEIGHT) / 100;
        }
        
        // Update trust score
        card.trustScore = newTrustScore;
        
        emit TrustScoreUpdated(_strategyId, newTrustScore);
    }

    /**
     * @dev Get the trust score for a strategy
     * @param _strategyId The ID of the strategy
     * @return The trust score (0-100)
     */
    function getTrustScore(uint256 _strategyId) external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return scorecards[_strategyId].trustScore;
    }
    
    /**
     * @dev Get the full scorecard for a strategy
     * @param _strategyId The ID of the strategy
     * @return The strategy scorecard
     */
    function getStrategyScorecard(uint256 _strategyId) external view returns (StrategyScorecard memory)  {
        // TODO: Add nonReentrant modifier
        return scorecards[_strategyId];
    }
}
