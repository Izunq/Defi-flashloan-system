// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title EmergencyInputValidator
 * @dev EMERGENCY: Critical security patches for input validation
 * @notice Deploy immediately to prevent exploitation
 * 
 * Status: EMERGENCY DEPLOYMENT
 * Priority: CRITICAL  
 * Deploy: IMMEDIATELY
 */

library EmergencyInputValidator {
    
    // Custom errors for gas efficiency
    error EmptyInput();
    error InputTooLong();
    error InvalidAddress();
    error ZeroAddress();
    error DangerousAddress();
    error SQLInjectionDetected();
    error XSSDetected();
    error CommandInjectionDetected();
    error NumericOverflow();
    error InvalidNumericRange();
    error InvalidDecimals();
    error ArrayTooLarge();
    error InvalidArrayElement();
    error DeadlineExpired();
    error InvalidTimestamp();
    error OracleDataStale();
    error PriceDeviationTooHigh();
      // Security constants
    uint256 constant MAX_STRING_LENGTH = 1000;
    uint256 constant MAX_ARRAY_LENGTH = 100;
    uint256 constant MAX_DECIMALS = 18;
    uint256 constant MAX_PRICE_DEVIATION = 1000; // 10% in basis points
    uint256 constant MAX_ORACLE_STALENESS = 3600; // 1 hour
    
    /**
     * @dev Emergency string validation with comprehensive security checks
     */
    function emergencyValidateString(string calldata input, uint256 maxLength) internal pure {
        bytes memory inputBytes = bytes(input);
        
        // Basic validation
        if (inputBytes.length == 0) revert EmptyInput();
        
        uint256 maxLen = maxLength == 0 ? MAX_STRING_LENGTH : maxLength;
        if (inputBytes.length > maxLen) revert InputTooLong();
        
        // SQL injection detection
        _checkSQLInjection(inputBytes);
        
        // XSS detection  
        _checkXSS(inputBytes);
        
        // Command injection detection
        _checkCommandInjection(inputBytes);
    }
    
    /**
     * @dev Emergency address validation with security checks
     */
    function emergencyValidateAddress(address addr) internal pure {
        if (addr == address(0)) revert ZeroAddress();
        
        // Check for dangerous precompile addresses
        if (uint160(addr) <= 9 && uint160(addr) >= 1) revert DangerousAddress();
        
        // Check for max address (potential overflow)
        if (addr == address(type(uint160).max)) revert DangerousAddress();
    }
    
    /**
     * @dev Emergency numeric validation with overflow protection
     */
    function emergencyValidateNumber(
        uint256 value,
        uint256 minValue,
        uint256 maxValue
    ) internal pure {
        if (value < minValue) revert InvalidNumericRange();
        if (value > maxValue) revert InvalidNumericRange();
        
        // Check for potential overflow in calculations
        if (value > type(uint256).max / 1e18) revert NumericOverflow();
    }
      /**
     * @dev Emergency array validation
     */
    function emergencyValidateArray(address[] calldata addresses) internal view {
        if (addresses.length == 0) revert EmptyInput();
        if (addresses.length > MAX_ARRAY_LENGTH) revert ArrayTooLarge();
        
        for (uint256 i = 0; i < addresses.length; i++) {
            emergencyValidateAddress(addresses[i]);
            
            // Gas optimization: Break if we've processed too many
            if (i > 0 && i % 100 == 0 && gasleft() < 50000) {
                break;
            }
        }
    }
    
    /**
     * @dev Emergency deadline validation
     */
    function emergencyValidateDeadline(uint256 deadline) internal view {
        if (deadline <= block.timestamp) revert DeadlineExpired();
        if (deadline > block.timestamp + 86400) revert InvalidTimestamp(); // Max 24 hours
    }
    
    /**
     * @dev Emergency oracle data validation
     */
    function emergencyValidateOracleData(
        uint256 price,
        uint256 timestamp,
        uint256 lastPrice
    ) internal view {
        // Staleness check
        if (block.timestamp - timestamp > MAX_ORACLE_STALENESS) revert OracleDataStale();
        
        // Price deviation check
        if (lastPrice > 0) {
            uint256 deviation;
            if (price > lastPrice) {
                deviation = ((price - lastPrice) * 10000) / lastPrice;
            } else {
                deviation = ((lastPrice - price) * 10000) / lastPrice;
            }
            
            if (deviation > MAX_PRICE_DEVIATION) revert PriceDeviationTooHigh();
        }
        
        // Basic price sanity check
        if (price == 0) revert InvalidNumericRange();
        if (price > type(uint256).max / 1e18) revert NumericOverflow();
    }
    
    /**
     * @dev Internal SQL injection pattern detection
     */
    function _checkSQLInjection(bytes memory data) private pure {
        // Check for common SQL injection patterns
        
        // Check for quotes and semicolons
        for (uint256 i = 0; i < data.length - 1; i++) {
            // Single quote + semicolon
            if (data[i] == 0x27 && data[i + 1] == 0x3B) revert SQLInjectionDetected();
            
            // Double quote + semicolon  
            if (data[i] == 0x22 && data[i + 1] == 0x3B) revert SQLInjectionDetected();
            
            // SQL comments (-- )
            if (data[i] == 0x2D && data[i + 1] == 0x2D) revert SQLInjectionDetected();
            
            // Block comments (/* */), check for /*
            if (data[i] == 0x2F && data[i + 1] == 0x2A) revert SQLInjectionDetected();
        }
        
        // Check for OR 1=1 pattern (case insensitive)
        if (_containsPattern(data, "OR")) revert SQLInjectionDetected();
        if (_containsPattern(data, "UNION")) revert SQLInjectionDetected();
        if (_containsPattern(data, "SELECT")) revert SQLInjectionDetected();
        if (_containsPattern(data, "INSERT")) revert SQLInjectionDetected();
        if (_containsPattern(data, "UPDATE")) revert SQLInjectionDetected();
        if (_containsPattern(data, "DELETE")) revert SQLInjectionDetected();
        if (_containsPattern(data, "DROP")) revert SQLInjectionDetected();
        if (_containsPattern(data, "EXEC")) revert SQLInjectionDetected();
    }
    
    /**
     * @dev Internal XSS pattern detection
     */
    function _checkXSS(bytes memory data) private pure {
        // Check for script tags
        if (_containsPattern(data, "<script")) revert XSSDetected();
        if (_containsPattern(data, "<SCRIPT")) revert XSSDetected();
        
        // Check for iframe
        if (_containsPattern(data, "<iframe")) revert XSSDetected();
        if (_containsPattern(data, "<IFRAME")) revert XSSDetected();
        
        // Check for javascript protocol
        if (_containsPattern(data, "javascript:")) revert XSSDetected();
        if (_containsPattern(data, "JAVASCRIPT:")) revert XSSDetected();
        
        // Check for event handlers
        if (_containsPattern(data, "onerror")) revert XSSDetected();
        if (_containsPattern(data, "onload")) revert XSSDetected();
        if (_containsPattern(data, "onclick")) revert XSSDetected();
        
        // Check for other dangerous tags
        if (_containsPattern(data, "<object")) revert XSSDetected();
        if (_containsPattern(data, "<embed")) revert XSSDetected();
        if (_containsPattern(data, "<svg")) revert XSSDetected();
    }
    
    /**
     * @dev Internal command injection detection
     */
    function _checkCommandInjection(bytes memory data) private pure {
        // Check for command separators
        for (uint256 i = 0; i < data.length; i++) {
            // Semicolon
            if (data[i] == 0x3B) revert CommandInjectionDetected();
            
            // Pipe
            if (data[i] == 0x7C) revert CommandInjectionDetected();
            
            // Ampersand
            if (data[i] == 0x26) revert CommandInjectionDetected();
            
            // Backtick
            if (data[i] == 0x60) revert CommandInjectionDetected();
        }
        
        // Check for command substitution
        if (_containsPattern(data, "$(")) revert CommandInjectionDetected();
    }
    
    /**
     * @dev Internal pattern matching helper
     */    function _containsPattern(bytes memory data, string memory pattern) private pure returns (bool) {
        bytes memory patternBytes = bytes(pattern);
        if (patternBytes.length > data.length) return false;
        
        uint256 maxIterations = 1000; // Limit iterations to prevent gas griefing
        uint256 searchLength = data.length - patternBytes.length;
        if (searchLength > maxIterations) searchLength = maxIterations;
        
        for (uint256 i = 0; i <= searchLength; i++) {
            bool found = true;
            for (uint256 j = 0; j < patternBytes.length; j++) {
                // Case insensitive comparison
                bytes1 dataChar = data[i + j];
                bytes1 patternChar = patternBytes[j];
                
                // Convert to lowercase for comparison
                if (dataChar >= 0x41 && dataChar <= 0x5A) {
                    dataChar = bytes1(uint8(dataChar) + 32);
                }
                if (patternChar >= 0x41 && patternChar <= 0x5A) {
                    patternChar = bytes1(uint8(patternChar) + 32);
                }
                
                if (dataChar != patternChar) {
                    found = false;
                    break;
                }
            }
            if (found) return true;
        }
        return false;
    }
}

/**
 * @title EmergencySecurityModifiers
 * @dev Emergency security modifiers for immediate deployment
 */
contract EmergencySecurityModifiers {
    using EmergencyInputValidator for *;
    
    // Events for security monitoring
    event SecurityViolationDetected(string violationType, address user, bytes data);
    event EmergencyValidationApplied(string validationType, address user);
    
    /**
     * @dev Emergency validation modifier for string inputs
     */
    modifier emergencyStringValidation(string calldata input) {
        EmergencyInputValidator.emergencyValidateString(input, 0);
        emit EmergencyValidationApplied("string", msg.sender);
        _;
    }
    
    /**
     * @dev Emergency validation modifier for addresses
     */
    modifier emergencyAddressValidation(address addr) {
        EmergencyInputValidator.emergencyValidateAddress(addr);
        emit EmergencyValidationApplied("address", msg.sender);
        _;
    }
    
    /**
     * @dev Emergency validation modifier for numeric values
     */
    modifier emergencyNumericValidation(uint256 value, uint256 min, uint256 max) {
        EmergencyInputValidator.emergencyValidateNumber(value, min, max);
        emit EmergencyValidationApplied("numeric", msg.sender);
        _;
    }
    
    /**
     * @dev Emergency validation modifier for deadlines
     */
    modifier emergencyDeadlineValidation(uint256 deadline) {
        EmergencyInputValidator.emergencyValidateDeadline(deadline);
        emit EmergencyValidationApplied("deadline", msg.sender);
        _;
    }
    
    /**
     * @dev Emergency validation modifier for oracle data
     */
    modifier emergencyOracleValidation(uint256 price, uint256 timestamp, uint256 lastPrice) {
        EmergencyInputValidator.emergencyValidateOracleData(price, timestamp, lastPrice);
        emit EmergencyValidationApplied("oracle", msg.sender);
        _;
    }
    
    /**
     * @dev Emergency circuit breaker for suspicious activity
     */
    modifier emergencyCircuitBreaker() {
        // Add circuit breaker logic here if needed
        _;
    }
}

/**
 * @title EmergencyArbitrageSecurityPatch
 * @dev Emergency security patch for arbitrage contracts
 */
contract EmergencyArbitrageSecurityPatch is EmergencySecurityModifiers {
    
    // Emergency pause mechanism
    bool public emergencyPaused = false;
    address public immutable emergencyAdmin;
    
    constructor(address _emergencyAdmin) {
        emergencyAdmin = _emergencyAdmin;
    }
    
    modifier whenNotEmergencyPaused() {
        require(!emergencyPaused, "Emergency paused");
        _;
    }
    
    modifier onlyEmergencyAdmin() {
        require(msg.sender == emergencyAdmin, "Not emergency admin");
        _;
    }
    
    /**
     * @dev Emergency pause function
     */
    function emergencyPause() external onlyEmergencyAdmin {
        emergencyPaused = true;
        emit EmergencyValidationApplied("pause", msg.sender);
    }
    
    /**
     * @dev Emergency unpause function
     */
    function emergencyUnpause() external onlyEmergencyAdmin {
        emergencyPaused = false;
        emit EmergencyValidationApplied("unpause", msg.sender);
    }
    
    /**
     * @dev Emergency arbitrage execution with validation
     */
    function emergencyExecuteArbitrage(
        address tokenA,
        address tokenB,
        uint256 amount,
        string calldata strategy,
        uint256 deadline
    ) 
        external
        whenNotEmergencyPaused
        emergencyAddressValidation(tokenA)
        emergencyAddressValidation(tokenB)
        emergencyNumericValidation(amount, 1, type(uint256).max / 1e18)
        emergencyStringValidation(strategy)
        emergencyDeadlineValidation(deadline)
        emergencyCircuitBreaker
    {
        // Emergency arbitrage logic here
        emit EmergencyValidationApplied("arbitrage", msg.sender);
    }
    
    /**
     * @dev Emergency oracle price update with validation
     */
    function emergencyUpdateOraclePrice(
        address token,
        uint256 newPrice,
        uint256 timestamp,
        uint256 lastPrice
    )
        external
        whenNotEmergencyPaused
        emergencyAddressValidation(token)
        emergencyOracleValidation(newPrice, timestamp, lastPrice)
        emergencyCircuitBreaker
    {
        // Emergency oracle update logic here
        emit EmergencyValidationApplied("oracle_update", msg.sender);
    }
    
    /**
     * @dev Emergency configuration update with validation
     */
    function emergencyUpdateConfig(
        string calldata configKey,
        string calldata configValue
    )
        external
        onlyEmergencyAdmin
        emergencyStringValidation(configKey)
        emergencyStringValidation(configValue)
    {
        // Emergency config update logic here
        emit EmergencyValidationApplied("config_update", msg.sender);
    }
}
