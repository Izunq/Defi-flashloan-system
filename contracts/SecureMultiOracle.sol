// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

/**
 * @title SecureMultiOracle
 * @notice Multi-oracle price feed system with manipulation protection
 * @dev Implements oracle consensus, deviation detection, and circuit breakers
 */
contract SecureMultiOracle is AccessControl, ReentrancyGuard, Pausable {
    using Math for uint256;

    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");

    // Oracle Configuration
    struct OracleConfig {
        address oracleAddress;
        uint256 weight;          // Weight in consensus (1-100)
        uint256 lastUpdateTime;
        bool isActive;
        uint256 successfulUpdates;
        uint256 failedUpdates;
        string source;           // e.g., "Chainlink", "Band", "API3"
    }

    // Price Data
    struct PriceData {
        uint256 price;
        uint256 timestamp;
        uint256 confidence;      // Confidence level (0-100)
        address oracle;
        bytes32 priceId;
    }

    // Consensus Data
    struct ConsensusPriceData {
        uint256 consensusPrice;
        uint256 timestamp;
        uint256 deviation;
        uint256 participatingOracles;
        bool isValid;
    }

    // Security Thresholds
    uint256 public constant MAX_PRICE_DEVIATION = 500; // 5% in basis points
    uint256 public constant MIN_ORACLES_REQUIRED = 3;
    uint256 public constant MAX_PRICE_AGE = 1 hours;
    uint256 public constant CIRCUIT_BREAKER_THRESHOLD = 1000; // 10% deviation
    uint256 public constant MIN_CONSENSUS_WEIGHT = 6000; // 60% of total weight

    // State Variables
    mapping(bytes32 => mapping(address => PriceData)) public priceData;
    mapping(bytes32 => ConsensusPriceData) public consensusPrices;
    mapping(address => OracleConfig) public oracles;
    mapping(bytes32 => bool) public circuitBreakerActive;
    
    address[] public oracleList;
    uint256 public totalOracleWeight;
    uint256 public emergencyShutdownTime;
    bool public globalCircuitBreaker = false;

    // Events
    event OracleAdded(address indexed oracle, uint256 weight, string source);
    event OracleRemoved(address indexed oracle, string reason);
    event OracleWeightUpdated(address indexed oracle, uint256 oldWeight, uint256 newWeight);
    event PriceUpdated(bytes32 indexed priceId, address indexed oracle, uint256 price, uint256 timestamp);
    event ConsensusPriceUpdated(bytes32 indexed priceId, uint256 price, uint256 deviation, uint256 timestamp);
    event PriceDeviationDetected(bytes32 indexed priceId, address indexed oracle, uint256 deviation);
    event CircuitBreakerTriggered(bytes32 indexed priceId, uint256 deviation);
    event CircuitBreakerReset(bytes32 indexed priceId, address indexed admin);
    event GlobalCircuitBreakerActivated(address indexed admin, uint256 timestamp);
    event OracleFailure(address indexed oracle, bytes32 priceId, string reason);

    // Custom Errors
    error OracleNotRegistered(address oracle);
    error InsufficientOracles(uint256 available, uint256 required);
    error PriceDataTooOld(uint256 age, uint256 maxAge);
    error ExcessivePriceDeviation(uint256 deviation, uint256 maxDeviation);
    error CircuitBreakerActive(bytes32 priceId);
    error GlobalCircuitBreakerActive();
    error InvalidOracleWeight(uint256 weight);
    error ConsensusNotReached(uint256 weight, uint256 required);

    modifier onlyRegisteredOracle() {
        if (!oracles[msg.sender].isActive) {
            revert OracleNotRegistered(msg.sender);
        }
        _;
    }

    modifier circuitBreakerCheck(bytes32 priceId) {
        if (globalCircuitBreaker) {
            revert GlobalCircuitBreakerActive();
        }
        if (circuitBreakerActive[priceId]) {
            revert CircuitBreakerActive(priceId);
        }
        _;
    }

    constructor(address admin) {
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), admin);
        _grantRole(ADMIN_ROLE, admin);
        _grantRole(EMERGENCY_ROLE, admin);
    }

    /**
     * @notice Add a new oracle to the system
     */
    function addOracle(
        address oracleAddress,
        uint256 weight,
        string calldata source
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(oracleAddress != address(0), "Invalid oracle address");
        require(weight > 0 && weight <= 100, "Invalid weight");
        require(!oracles[oracleAddress].isActive, "Oracle already registered");

        oracles[oracleAddress] = OracleConfig({
            oracleAddress: oracleAddress,
            weight: weight,
            lastUpdateTime: 0,
            isActive: true,
            successfulUpdates: 0,
            failedUpdates: 0,
            source: source
        });

        oracleList.push(oracleAddress);
        totalOracleWeight += weight;

        _grantRole(ORACLE_ROLE, oracleAddress);

        emit OracleAdded(oracleAddress, weight, source);
    }

    /**
     * @notice Remove an oracle from the system
     */
    function removeOracle(address oracleAddress, string calldata reason)
        external
        onlyRole(ADMIN_ROLE)
    {
        require(oracles[oracleAddress].isActive, "Oracle not registered");

        oracles[oracleAddress].isActive = false;
        totalOracleWeight -= oracles[oracleAddress].weight;

        _revokeRole(ORACLE_ROLE, oracleAddress);

        // Remove from oracle list
        for (uint256 i = 0; i < oracleList.length; i++) {
            if (oracleList[i] == oracleAddress) {
                oracleList[i] = oracleList[oracleList.length - 1];
                oracleList.pop();
                break;
            }
        }

        emit OracleRemoved(oracleAddress, reason);
    }

    /**
     * @notice Update oracle weight
     */
    function updateOracleWeight(address oracleAddress, uint256 newWeight)
        external
        onlyRole(ADMIN_ROLE)
    {
        require(oracles[oracleAddress].isActive, "Oracle not registered");
        require(newWeight > 0 && newWeight <= 100, "Invalid weight");

        uint256 oldWeight = oracles[oracleAddress].weight;
        oracles[oracleAddress].weight = newWeight;
        totalOracleWeight = totalOracleWeight - oldWeight + newWeight;

        emit OracleWeightUpdated(oracleAddress, oldWeight, newWeight);
    }

    /**
     * @notice Submit price data from oracle
     */
    function submitPrice(
        bytes32 priceId,
        uint256 price,
        uint256 confidence
    ) 
        external 
        onlyRegisteredOracle
        circuitBreakerCheck(priceId)
        nonReentrant
        whenNotPaused
    {
        require(price > 0, "Invalid price");
        require(confidence > 0 && confidence <= 100, "Invalid confidence");

        // Check for excessive deviation from previous consensus
        ConsensusPriceData memory currentConsensus = consensusPrices[priceId];
        if (currentConsensus.isValid && currentConsensus.timestamp > 0) {
            uint256 deviation = _calculateDeviation(price, currentConsensus.consensusPrice);
            
            if (deviation > CIRCUIT_BREAKER_THRESHOLD) {
                circuitBreakerActive[priceId] = true;
                emit CircuitBreakerTriggered(priceId, deviation);
                revert ExcessivePriceDeviation(deviation, CIRCUIT_BREAKER_THRESHOLD);
            }
            
            if (deviation > MAX_PRICE_DEVIATION) {
                emit PriceDeviationDetected(priceId, msg.sender, deviation);
            }
        }

        // Store price data
        priceData[priceId][msg.sender] = PriceData({
            price: price,
            timestamp: block.timestamp,
            confidence: confidence,
            oracle: msg.sender,
            priceId: priceId
        });

        // Update oracle stats
        oracles[msg.sender].lastUpdateTime = block.timestamp;
        oracles[msg.sender].successfulUpdates++;

        emit PriceUpdated(priceId, msg.sender, price, block.timestamp);

        // Calculate new consensus
        _calculateConsensus(priceId);
    }

    /**
     * @notice Calculate consensus price from all oracle submissions
     */
    function _calculateConsensus(bytes32 priceId) internal {
        uint256 totalWeight = 0;
        uint256 weightedSum = 0;
        uint256 validOracleCount = 0;
        uint256 maxDeviation = 0;

        // First pass: collect valid prices and calculate weighted average
        for (uint256 i = 0; i < oracleList.length; i++) {
            address oracleAddr = oracleList[i];
            if (!oracles[oracleAddr].isActive) continue;

            PriceData memory data = priceData[priceId][oracleAddr];
            
            // Check if price is recent enough
            if (block.timestamp - data.timestamp > MAX_PRICE_AGE) continue;
            if (data.price == 0) continue;

            uint256 oracleWeight = oracles[oracleAddr].weight;
            weightedSum += data.price * oracleWeight;
            totalWeight += oracleWeight;
            validOracleCount++;
        }

        // Check minimum requirements
        if (validOracleCount < MIN_ORACLES_REQUIRED) {
            revert InsufficientOracles(validOracleCount, MIN_ORACLES_REQUIRED);
        }

        if (totalWeight < MIN_CONSENSUS_WEIGHT) {
            revert ConsensusNotReached(totalWeight, MIN_CONSENSUS_WEIGHT);
        }

        uint256 consensusPrice = weightedSum / totalWeight;

        // Second pass: calculate maximum deviation
        for (uint256 i = 0; i < oracleList.length; i++) {
            address oracleAddr = oracleList[i];
            if (!oracles[oracleAddr].isActive) continue;

            PriceData memory data = priceData[priceId][oracleAddr];
            if (block.timestamp - data.timestamp > MAX_PRICE_AGE) continue;
            if (data.price == 0) continue;

            uint256 deviation = _calculateDeviation(data.price, consensusPrice);
            maxDeviation = Math.max(maxDeviation, deviation);
        }

        // Update consensus data
        consensusPrices[priceId] = ConsensusPriceData({
            consensusPrice: consensusPrice,
            timestamp: block.timestamp,
            deviation: maxDeviation,
            participatingOracles: validOracleCount,
            isValid: true
        });

        emit ConsensusPriceUpdated(priceId, consensusPrice, maxDeviation, block.timestamp);
    }

    /**
     * @notice Calculate percentage deviation between two prices
     */
    function _calculateDeviation(uint256 price1, uint256 price2) internal pure returns (uint256) {
        if (price1 == price2) return 0;
        
        uint256 diff = price1 > price2 ? price1 - price2 : price2 - price1;
        uint256 base = Math.max(price1, price2);
        
        return (diff * 10000) / base; // Return in basis points
    }

    /**
     * @notice Get the latest consensus price
     */
    function getPrice(bytes32 priceId) 
        external 
        view 
        circuitBreakerCheck(priceId)
        returns (
            uint256 price,
            uint256 timestamp,
            uint256 deviation,
            bool isValid
        )
    {
        ConsensusPriceData memory consensus = consensusPrices[priceId];
        
        // Check if price is too old
        if (block.timestamp - consensus.timestamp > MAX_PRICE_AGE) {
            revert PriceDataTooOld(
                block.timestamp - consensus.timestamp,
                MAX_PRICE_AGE
            );
        }

        return (
            consensus.consensusPrice,
            consensus.timestamp,
            consensus.deviation,
            consensus.isValid
        );
    }

    /**
     * @notice Get price with safety checks
     */
    function getSafePrice(bytes32 priceId, uint256 maxAge) 
        external 
        view 
        returns (uint256 price, bool isValid)
    {
        if (globalCircuitBreaker || circuitBreakerActive[priceId]) {
            return (0, false);
        }

        ConsensusPriceData memory consensus = consensusPrices[priceId];
        
        if (!consensus.isValid) {
            return (0, false);
        }

        if (block.timestamp - consensus.timestamp > maxAge) {
            return (0, false);
        }

        if (consensus.deviation > MAX_PRICE_DEVIATION) {
            return (0, false);
        }

        return (consensus.consensusPrice, true);
    }

    /**
     * @notice Reset circuit breaker for specific price feed
     */
    function resetCircuitBreaker(bytes32 priceId)
        external
        onlyRole(EMERGENCY_ROLE)
    {
        circuitBreakerActive[priceId] = false;
        emit CircuitBreakerReset(priceId, msg.sender);
    }

    /**
     * @notice Activate global circuit breaker
     */
    function activateGlobalCircuitBreaker()
        external
        onlyRole(EMERGENCY_ROLE)
    {
        globalCircuitBreaker = true;
        emergencyShutdownTime = block.timestamp;
        _pause();
        emit GlobalCircuitBreakerActivated(msg.sender, block.timestamp);
    }

    /**
     * @notice Deactivate global circuit breaker
     */
    function deactivateGlobalCircuitBreaker()
        external
        onlyRole(EMERGENCY_ROLE)
    {
        require(
            block.timestamp >= emergencyShutdownTime + 1 hours,
            "Emergency cooldown period not elapsed"
        );
        
        globalCircuitBreaker = false;
        _unpause();
    }

    /**
     * @notice Report oracle failure
     */
    function reportOracleFailure(address oracleAddress, bytes32 priceId, string calldata reason)
        external
        onlyRole(ORACLE_ROLE)
    {
        require(oracles[oracleAddress].isActive, "Oracle not registered");
        
        oracles[oracleAddress].failedUpdates++;
        
        emit OracleFailure(oracleAddress, priceId, reason);
        
        // Auto-deactivate oracle if too many failures
        if (oracles[oracleAddress].failedUpdates > 10) {
            oracles[oracleAddress].isActive = false;
            _revokeRole(ORACLE_ROLE, oracleAddress);
            emit OracleRemoved(oracleAddress, "Excessive failures");
        }
    }

    /**
     * @notice Get oracle statistics
     */
    function getOracleStats(address oracleAddress)
        external
        view
        returns (
            uint256 weight,
            uint256 successfulUpdates,
            uint256 failedUpdates,
            uint256 lastUpdateTime,
            bool isActive,
            string memory source
        )
    {
        OracleConfig memory config = oracles[oracleAddress];
        return (
            config.weight,
            config.successfulUpdates,
            config.failedUpdates,
            config.lastUpdateTime,
            config.isActive,
            config.source
        );
    }

    /**
     * @notice Get system health status
     */
    function getSystemHealth()
        external
        view
        returns (
            uint256 activeOracles,
            uint256 totalWeight,
            bool globalCircuitBreakerStatus,
            bool systemPaused
        )
    {
        uint256 active = 0;
        for (uint256 i = 0; i < oracleList.length; i++) {
            if (oracles[oracleList[i]].isActive) {
                active++;
            }
        }

        return (
            active,
            totalOracleWeight,
            globalCircuitBreaker,
            paused()
        );
    }

    /**
     * @notice Get consensus price from multiple oracles
     * @param token Token address to get price for
     * @return price Consensus price
     * @return valid Whether the price is valid and within deviation limits
     */
    function getConsensusPrice(address token) external view returns (uint256 price, bool valid)  {
        // TODO: Add nonReentrant modifier
        require(oracleList.length >= MIN_ORACLES_REQUIRED, "Insufficient oracles");
        
        uint256[] memory prices = new uint256[](oracleList.length);
        uint256 validPrices = 0;
        
        // Collect prices from all oracles
        for (uint256 i = 0; i < oracleList.length; i++) {
            address oracleAddr = oracleList[i];
            if (!oracles[oracleAddr].isActive) continue;

            PriceData memory data = priceData[token][oracleAddr];
            // Check if price is recent enough
            if (block.timestamp - data.timestamp > MAX_PRICE_AGE) continue;
            if (data.price == 0) continue;

            prices[validPrices] = data.price;
            validPrices++;
        }
        
        if (validPrices < MIN_ORACLES_REQUIRED) {
            return (0, false);
        }
        
        // Calculate median price
        price = _calculateMedian(prices, validPrices);
        
        // Check for price manipulation
        valid = _validatePriceDeviation(prices, validPrices, price);
        
        return (price, valid);
    }

    /**
     * @notice Calculate median value from an array
     */
    function _calculateMedian(uint256[] memory values, uint256 count) internal pure returns (uint256) {
        require(count > 0, "No values provided");
        
        uint256[] memory sortedValues = values;
        // Sort the array (simple bubble sort for small arrays)
        for (uint256 i = 0; i < count - 1; i++) {
            for (uint256 j = 0; j < count - i - 1; j++) {
                if (sortedValues[j] > sortedValues[j + 1]) {
                    (sortedValues[j], sortedValues[j + 1]) = (sortedValues[j + 1], sortedValues[j]);
                }
            }
        }
        
        if (count % 2 == 0) {
            // Even number of elements, return average of middle two
            return (sortedValues[count / 2 - 1] + sortedValues[count / 2]) / 2;
        } else {
            // Odd number of elements, return middle element
            return sortedValues[count / 2];
        }
    }

    /**
     * @notice Validate price deviation against oracle consensus
     */
    function _validatePriceDeviation(uint256[] memory prices, uint256 count, uint256 consensusPrice) internal view returns (bool) {
        uint256 maxDeviation = 0;
        
        for (uint256 i = 0; i < count; i++) {
            uint256 deviation = _calculateDeviation(prices[i], consensusPrice);
            if (deviation > maxDeviation) {
                maxDeviation = deviation;
            }
        }
        
        return maxDeviation <= MAX_PRICE_DEVIATION;
    }
}
