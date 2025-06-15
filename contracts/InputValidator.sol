// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title InputValidator
 * @notice Universal input validation library for enhanced security
 * @dev Provides comprehensive validation functions to prevent malicious data injection
 */
library InputValidator {
    // =================
    // CONSTANTS
    // =================
    
    uint256 public constant MAX_ARRAY_LENGTH = 100;
    uint256 public constant MIN_ARRAY_LENGTH = 1;
    uint256 public constant MAX_TOKEN_AMOUNT = 10**30; // 1 trillion tokens with 18 decimals
    uint256 public constant MIN_TOKEN_AMOUNT = 1; // 1 wei minimum
    uint256 public constant MAX_PERCENTAGE_BPS = 10000; // 100% in basis points
    uint256 public constant MAX_SLIPPAGE_BPS = 1000; // 10% max slippage
    uint256 public constant MIN_PERCENTAGE_BPS = 1; // 0.01% minimum
    uint256 public constant MAX_ORACLE_STALENESS = 3600; // 1 hour
    uint256 public constant MIN_ORACLE_STALENESS = 60; // 1 minute
    uint256 public constant MAX_GAS_PRICE = 1000 * 10**9; // 1000 Gwei
    uint256 public constant MIN_GAS_PRICE = 1 * 10**9; // 1 Gwei
    uint256 public constant MAX_DEADLINE_FUTURE = 7200; // 2 hours in future
    uint256 public constant MIN_DEADLINE_FUTURE = 300; // 5 minutes in future
    
    // =================
    // CUSTOM ERRORS
    // =================
    
    error InvalidArrayLength(uint256 actual, uint256 min, uint256 max);
    error InvalidAddress(address addr);
    error AddressNotWhitelisted(address addr);
    error ValueOutOfRange(uint256 value, uint256 min, uint256 max);
    error InvalidTokenAmount(uint256 amount, address token);
    error StaleOracleData(uint256 age, uint256 maxAge);
    error InvalidOraclePrice(uint256 price);
    error ArrayLengthMismatch(uint256 length1, uint256 length2);
    error InvalidPercentage(uint256 percentage);
    error InvalidDeadline(uint256 deadline, uint256 current);
    error InvalidGasPrice(uint256 gasPrice);
    error EmptyStringInput();
    error StringTooLong(uint256 length, uint256 maxLength);
    
    // =================
    // ARRAY VALIDATION
    // =================
    
    /**
     * @notice Validate array length within specified bounds
     * @param length Array length to validate
     * @param min Minimum allowed length
     * @param max Maximum allowed length
     */
    function requireValidArrayLength(uint256 length, uint256 min, uint256 max) internal pure {
        if (length < min || length > max) {
            revert InvalidArrayLength(length, min, max);
        }
    }
    
    /**
     * @notice Validate array length with default bounds
     * @param length Array length to validate
     */
    function requireValidArrayLength(uint256 length) internal pure {
        requireValidArrayLength(length, MIN_ARRAY_LENGTH, MAX_ARRAY_LENGTH);
    }
    
    /**
     * @notice Validate that two arrays have matching lengths
     * @param length1 First array length
     * @param length2 Second array length
     */
    function requireMatchingArrayLengths(uint256 length1, uint256 length2) internal pure {
        if (length1 != length2) {
            revert ArrayLengthMismatch(length1, length2);
        }
    }
    
    // =================
    // ADDRESS VALIDATION
    // =================
    
    /**
     * @notice Validate address is not zero
     * @param addr Address to validate
     */
    function requireValidAddress(address addr) internal pure {
        if (addr == address(0)) {
            revert InvalidAddress(addr);
        }
    }
    
    /**
     * @notice Validate address against whitelist
     * @param addr Address to validate
     * @param whitelist Mapping of whitelisted addresses
     */
    function requireWhitelistedAddress(
        address addr, 
        mapping(address => bool) storage whitelist
    ) internal view {
        requireValidAddress(addr);
        if (!whitelist[addr]) {
            revert AddressNotWhitelisted(addr);
        }
    }
    
    /**
     * @notice Validate multiple addresses
     * @param addresses Array of addresses to validate
     */
    function requireValidAddresses(address[] calldata addresses) internal pure {
        requireValidArrayLength(addresses.length);
        for (uint256 i = 0; i < addresses.length; i++) {
            requireValidAddress(addresses[i]);
        }
    }
    
    // =================
    // NUMERIC VALIDATION
    // =================
    
    /**
     * @notice Validate value is within specified range
     * @param value Value to validate
     * @param min Minimum allowed value
     * @param max Maximum allowed value
     */
    function requireInRange(uint256 value, uint256 min, uint256 max) internal pure {
        if (value < min || value > max) {
            revert ValueOutOfRange(value, min, max);
        }
    }
    
    /**
     * @notice Validate percentage in basis points
     * @param percentage Percentage in basis points (100% = 10000)
     */
    function requireValidPercentage(uint256 percentage) internal pure {
        if (percentage > MAX_PERCENTAGE_BPS) {
            revert InvalidPercentage(percentage);
        }
    }
    
    /**
     * @notice Validate slippage percentage
     * @param slippage Slippage in basis points
     */
    function requireValidSlippage(uint256 slippage) internal pure {
        requireInRange(slippage, MIN_PERCENTAGE_BPS, MAX_SLIPPAGE_BPS);
    }
    
    /**
     * @notice Validate gas price
     * @param gasPrice Gas price in wei
     */
    function requireValidGasPrice(uint256 gasPrice) internal pure {
        if (gasPrice < MIN_GAS_PRICE || gasPrice > MAX_GAS_PRICE) {
            revert InvalidGasPrice(gasPrice);
        }
    }
    
    // =================
    // TOKEN VALIDATION
    // =================
    
    /**
     * @notice Validate token amount
     * @param amount Token amount to validate
     * @param token Token address (for context)
     */
    function requireValidTokenAmount(uint256 amount, address token) internal pure {
        requireValidAddress(token);
        if (amount == 0 || amount > MAX_TOKEN_AMOUNT) {
            revert InvalidTokenAmount(amount, token);
        }
    }
    
    /**
     * @notice Validate multiple token amounts
     * @param amounts Array of token amounts
     * @param tokens Array of token addresses
     */
    function requireValidTokenAmounts(
        uint256[] calldata amounts,
        address[] calldata tokens
    ) internal pure {
        requireMatchingArrayLengths(amounts.length, tokens.length);
        
        for (uint256 i = 0; i < amounts.length; i++) {
            requireValidTokenAmount(amounts[i], tokens[i]);
        }
    }
    
    // =================
    // TIME VALIDATION
    // =================
    
    /**
     * @notice Validate deadline is in acceptable future range
     * @param deadline Deadline timestamp
     */
    function requireValidDeadline(uint256 deadline) internal view {
        uint256 current = block.timestamp;
        uint256 minDeadline = current + MIN_DEADLINE_FUTURE;
        uint256 maxDeadline = current + MAX_DEADLINE_FUTURE;
        
        if (deadline < minDeadline || deadline > maxDeadline) {
            revert InvalidDeadline(deadline, current);
        }
    }
    
    /**
     * @notice Validate timestamp is not too old
     * @param timestamp Timestamp to validate
     * @param maxAge Maximum allowed age in seconds
     */
    function requireFreshTimestamp(uint256 timestamp, uint256 maxAge) internal view {
        uint256 age = block.timestamp - timestamp;
        if (age > maxAge) {
            revert StaleOracleData(age, maxAge);
        }
    }
    
    // =================
    // ORACLE VALIDATION
    // =================
    
    /**
     * @notice Validate oracle data freshness and price
     * @param price Oracle price
     * @param timestamp Price timestamp
     * @param maxStaleness Maximum allowed staleness in seconds
     */
    function requireValidOracleData(
        uint256 price,
        uint256 timestamp,
        uint256 maxStaleness
    ) internal view {
        if (price == 0) {
            revert InvalidOraclePrice(price);
        }
        
        requireFreshTimestamp(timestamp, maxStaleness);
    }
    
    /**
     * @notice Validate oracle data with default staleness
     * @param price Oracle price
     * @param timestamp Price timestamp
     */
    function requireValidOracleData(uint256 price, uint256 timestamp) internal view {
        requireValidOracleData(price, timestamp, MAX_ORACLE_STALENESS);
    }
    
    // =================
    // STRING VALIDATION
    // =================
    
    /**
     * @notice Validate string is not empty
     * @param str String to validate
     */
    function requireNonEmptyString(string calldata str) internal pure {
        if (bytes(str).length == 0) {
            revert EmptyStringInput();
        }
    }
    
    /**
     * @notice Validate string length
     * @param str String to validate
     * @param maxLength Maximum allowed length
     */
    function requireValidStringLength(string calldata str, uint256 maxLength) internal pure {
        uint256 length = bytes(str).length;
        if (length == 0) {
            revert EmptyStringInput();
        }
        if (length > maxLength) {
            revert StringTooLong(length, maxLength);
        }
    }
    
    // =================
    // COMPLEX VALIDATION
    // =================
    
    /**
     * @notice Validate arbitrage parameters
     * @param tokenA First token address
     * @param tokenB Second token address
     * @param amountIn Input amount
     * @param minAmountOut Minimum output amount
     * @param deadline Transaction deadline
     */
    function requireValidArbitrageParams(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        uint256 minAmountOut,
        uint256 deadline
    ) internal view {
        requireValidAddress(tokenA);
        requireValidAddress(tokenB);
        require(tokenA != tokenB, "InputValidator: Identical tokens");
        
        requireValidTokenAmount(amountIn, tokenA);
        requireValidTokenAmount(minAmountOut, tokenB);
        requireValidDeadline(deadline);
    }
    
    /**
     * @notice Validate strategy execution parameters
     * @param strategy Strategy address
     * @param tokens Array of token addresses
     * @param amounts Array of token amounts
     * @param deadline Execution deadline
     */
    function requireValidStrategyParams(
        address strategy,
        address[] calldata tokens,
        uint256[] calldata amounts,
        uint256 deadline
    ) internal view {
        requireValidAddress(strategy);
        requireValidAddresses(tokens);
        requireValidTokenAmounts(amounts, tokens);
        requireValidDeadline(deadline);
    }
    
    /**
     * @notice Validate flash loan parameters
     * @param asset Asset to borrow
     * @param amount Amount to borrow
     * @param premium Premium to pay
     * @param data Additional data
     */
    function requireValidFlashLoanParams(
        address asset,
        uint256 amount,
        uint256 premium,
        bytes calldata data
    ) internal pure {
        requireValidAddress(asset);
        requireValidTokenAmount(amount, asset);
        requireValidTokenAmount(premium, asset);
        requireValidArrayLength(data.length, 0, 1024); // Max 1KB data
    }
}
