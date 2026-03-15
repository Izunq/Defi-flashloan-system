// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title StrategyProposalRateLimiter
 * @notice Enhanced rate limiting for strategy proposals with cooling periods
 * @dev Implements multiple rate limiting mechanisms to prevent spam and abuse
 */
contract StrategyProposalRateLimiter is AccessControl, ReentrancyGuard, Pausable {
    
    bytes32 public constant STRATEGY_PROPOSER_ROLE = keccak256("STRATEGY_PROPOSER_ROLE");
    bytes32 public constant RATE_LIMIT_ADMIN_ROLE = keccak256("RATE_LIMIT_ADMIN_ROLE");      // Rate limiting configuration - ENHANCED FOR SECURITY
    struct RateLimitConfig {
        uint256 maxProposalsPerHour;            // 3 (reduced from 5)
        uint256 maxProposalsPerDay;             // 15 (reduced from 20)
        uint256 maxProposalsPerWeek;            // 50 (reduced from 100)
        uint256 coolingPeriodAfterRejection;    // 1 hour
        uint256 coolingPeriodAfterSpam;         // 24 hours
        uint256 minimumTimeBetweenProposals;    // 10 minutes (increased from 5)
        uint256 spamDetectionThreshold;         // 3 proposals in 1 minute
        uint256 blacklistDuration;              // 7 days
    }
    
    // Individual rate limits for backward compatibility
    uint256 public hourlyLimit = 3;
    uint256 public dailyLimit = 15;
    uint256 public weeklyLimit = 50;
    uint256 public coolingPeriod = 1 hours;
      // Proposal tracking - ENHANCED FOR SECURITY
    struct ProposerStats {
        uint256 hourlyProposals;
        uint256 dailyProposals;
        uint256 weeklyProposals;
        uint256 lastProposalTime;
        uint256 lastHourReset;
        uint256 lastDayReset;
        uint256 lastWeekReset;
        uint256 rejectionCount;
        uint256 lastRejectionTime;
        bool isInCoolingPeriod;
        uint256 coolingPeriodEnd;
        uint256 spamDetectionScore;
        uint256 successfulProposals;            // New: track successful proposals
        uint256 totalProposals;                 // New: track total proposals
        uint256 blacklistCount;                 // New: track blacklist incidents
        uint256 lastSpamDetectionTime;          // New: track spam detection timing
    }
    
    // Configuration
    RateLimitConfig public rateLimitConfig;
    
    // State
    mapping(address => ProposerStats) public proposerStats;
    mapping(address => bool) public blacklistedProposers;
    
    // Events
    event ProposalRateLimited(address indexed proposer, string reason, uint256 coolingPeriodEnd);
    event ProposerBlacklisted(address indexed proposer, string reason);
    event RateLimitConfigUpdated(address indexed admin);
    event CoolingPeriodActivated(address indexed proposer, uint256 duration);
    event SpamDetected(address indexed proposer, uint256 spamScore);
    
    constructor() {
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), msg.sender);
        _grantRole(RATE_LIMIT_ADMIN_ROLE, msg.sender);
        
        // Initialize default rate limits
        rateLimitConfig = RateLimitConfig({
            maxProposalsPerHour: 3,
            maxProposalsPerDay: 10,
            maxProposalsPerWeek: 25,
            coolingPeriodAfterRejection: 2 hours,
            coolingPeriodAfterSpam: 24 hours,
            minimumTimeBetweenProposals: 20 minutes
        });
    }
    
    /**
     * @notice Check if proposer can submit a proposal (MAIN RATE LIMITING FUNCTION)
     * @param proposer Address of the proposer
     * @return canPropose Whether the proposer can submit
     * @return reason Reason if cannot propose
     * @return waitTime Time to wait in seconds
     */
    function canProposeStrategy(address proposer) 
        external 
        view 
        returns (bool canPropose, string memory reason, uint256 waitTime) 
    {
        // Check if blacklisted
        if (blacklistedProposers[proposer]) {
            return (false, "Proposer is blacklisted", 0);
        }
        
        ProposerStats memory stats = proposerStats[proposer];
        
        // Check cooling period
        if (stats.isInCoolingPeriod && block.timestamp < stats.coolingPeriodEnd) {
            return (false, "In cooling period", stats.coolingPeriodEnd - block.timestamp);
        }
        
        // Update time windows (simulated for view function)
        (uint256 hourlyCount, uint256 dailyCount, uint256 weeklyCount) = _getUpdatedCounts(proposer);
        
        // Check hourly limit
        if (hourlyCount >= rateLimitConfig.maxProposalsPerHour) {
            uint256 nextHourReset = stats.lastHourReset + 1 hours;
            return (false, "Hourly limit exceeded", nextHourReset - block.timestamp);
        }
        
        // Check daily limit
        if (dailyCount >= rateLimitConfig.maxProposalsPerDay) {
            uint256 nextDayReset = stats.lastDayReset + 1 days;
            return (false, "Daily limit exceeded", nextDayReset - block.timestamp);
        }
        
        // Check weekly limit
        if (weeklyCount >= rateLimitConfig.maxProposalsPerWeek) {
            uint256 nextWeekReset = stats.lastWeekReset + 1 weeks;
            return (false, "Weekly limit exceeded", nextWeekReset - block.timestamp);
        }
        
        // Check minimum time between proposals
        uint256 timeSinceLastProposal = block.timestamp - stats.lastProposalTime;
        if (timeSinceLastProposal < rateLimitConfig.minimumTimeBetweenProposals) {
            uint256 waitTime = rateLimitConfig.minimumTimeBetweenProposals - timeSinceLastProposal;
            return (false, "Too soon after last proposal", waitTime);
        }
        
        return (true, "", 0);
    }
    
    /**
     * @notice Record a strategy proposal (called by strategy contracts)
     * @param proposer Address of the proposer
     */
    function recordProposal(address proposer) 
        external 
        onlyRole(STRATEGY_PROPOSER_ROLE) 
        nonReentrant 
        whenNotPaused 
    {
        require(!blacklistedProposers[proposer], "Proposer is blacklisted");
        
        ProposerStats storage stats = proposerStats[proposer];
        
        // Check rate limits
        (bool canPropose, string memory reason, uint256 waitTime) = this.canProposeStrategy(proposer);
        require(canPropose, reason);
        
        // Update time windows
        _updateTimeWindows(proposer);
        
        // Increment counters
        stats.hourlyProposals++;
        stats.dailyProposals++;
        stats.weeklyProposals++;
        stats.lastProposalTime = block.timestamp;
        
        // Check for spam patterns
        _checkSpamPattern(proposer);
    }
    
    /**
     * @notice Record a proposal rejection
     * @param proposer Address of the proposer
     */
    function recordRejection(address proposer) 
        external 
        onlyRole(STRATEGY_PROPOSER_ROLE) 
        nonReentrant 
    {
        ProposerStats storage stats = proposerStats[proposer];
        stats.rejectionCount++;
        stats.lastRejectionTime = block.timestamp;
        
        // Activate cooling period after multiple rejections
        if (stats.rejectionCount >= 3) {
            _activateCoolingPeriod(proposer, rateLimitConfig.coolingPeriodAfterRejection);
            stats.rejectionCount = 0; // Reset counter
        }
    }
    
    /**
     * @notice Blacklist a proposer
     * @param proposer Address to blacklist
     * @param reason Reason for blacklisting
     */
    function blacklistProposer(address proposer, string calldata reason) 
        external 
        onlyRole(RATE_LIMIT_ADMIN_ROLE) 
    {
        blacklistedProposers[proposer] = true;
        emit ProposerBlacklisted(proposer, reason);
    }
    
    /**
     * @notice Remove proposer from blacklist
     * @param proposer Address to unblacklist
     */
    function unblacklistProposer(address proposer) 
        external 
        onlyRole(RATE_LIMIT_ADMIN_ROLE) 
    {
        blacklistedProposers[proposer] = false;
    }
    
    /**
     * @notice Update rate limit configuration
     * @param newConfig New rate limit configuration
     */
    function updateRateLimitConfig(RateLimitConfig calldata newConfig) 
        external 
        onlyRole(RATE_LIMIT_ADMIN_ROLE) 
    {
        require(newConfig.maxProposalsPerHour > 0, "Invalid hourly limit");
        require(newConfig.maxProposalsPerDay > newConfig.maxProposalsPerHour, "Invalid daily limit");
        require(newConfig.maxProposalsPerWeek > newConfig.maxProposalsPerDay, "Invalid weekly limit");
        
        rateLimitConfig = newConfig;
        emit RateLimitConfigUpdated(msg.sender);
    }
    
    /**
     * @notice Get proposer statistics
     * @param proposer Address of the proposer
     */
    function getProposerStats(address proposer) 
        external 
        view 
        returns (ProposerStats memory) 
    {
        return proposerStats[proposer];
    }
    
    // Internal functions
    
    function _updateTimeWindows(address proposer) internal {
        ProposerStats storage stats = proposerStats[proposer];
        uint256 currentTime = block.timestamp;
        
        // Reset hourly counter if hour has passed
        if (currentTime >= stats.lastHourReset + 1 hours) {
            stats.hourlyProposals = 0;
            stats.lastHourReset = currentTime;
        }
        
        // Reset daily counter if day has passed
        if (currentTime >= stats.lastDayReset + 1 days) {
            stats.dailyProposals = 0;
            stats.lastDayReset = currentTime;
        }
        
        // Reset weekly counter if week has passed
        if (currentTime >= stats.lastWeekReset + 1 weeks) {
            stats.weeklyProposals = 0;
            stats.lastWeekReset = currentTime;
        }
    }
    
    function _getUpdatedCounts(address proposer) 
        internal 
        view 
        returns (uint256 hourlyCount, uint256 dailyCount, uint256 weeklyCount) 
    {
        ProposerStats memory stats = proposerStats[proposer];
        uint256 currentTime = block.timestamp;
        
        // Calculate current counts based on time windows
        hourlyCount = (currentTime >= stats.lastHourReset + 1 hours) ? 0 : stats.hourlyProposals;
        dailyCount = (currentTime >= stats.lastDayReset + 1 days) ? 0 : stats.dailyProposals;
        weeklyCount = (currentTime >= stats.lastWeekReset + 1 weeks) ? 0 : stats.weeklyProposals;
    }
    
    function _checkSpamPattern(address proposer) internal {
        ProposerStats storage stats = proposerStats[proposer];
        
        // Increase spam score based on rapid proposals
        if (block.timestamp - stats.lastProposalTime < 5 minutes) {
            stats.spamDetectionScore += 10;
        } else if (block.timestamp - stats.lastProposalTime < 15 minutes) {
            stats.spamDetectionScore += 5;
        } else {
            // Decay spam score over time
            if (stats.spamDetectionScore > 0) {
                stats.spamDetectionScore = (stats.spamDetectionScore > 1) ? stats.spamDetectionScore - 1 : 0;
            }
        }
        
        // Trigger spam protection
        if (stats.spamDetectionScore >= 50) {
            _activateCoolingPeriod(proposer, rateLimitConfig.coolingPeriodAfterSpam);
            stats.spamDetectionScore = 0;
            emit SpamDetected(proposer, stats.spamDetectionScore);
        }
    }
    
    function _activateCoolingPeriod(address proposer, uint256 duration) internal {
        ProposerStats storage stats = proposerStats[proposer];
        stats.isInCoolingPeriod = true;
        stats.coolingPeriodEnd = block.timestamp + duration;
        
        emit CoolingPeriodActivated(proposer, duration);
    }
}
