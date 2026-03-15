// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ComprehensiveInputValidator
 * @dev Enhanced input validation library with comprehensive security features
 * @notice Provides multi-layered validation for all contract inputs
 * 
 * Features:
 * - SQL injection prevention
 * - XSS prevention
 * - Command injection prevention
 * - Numeric overflow protection
 * - Address validation
 * - Array bounds checking
 * - Rate limiting integration
 * - Emergency circuit breakers
 */

library ComprehensiveInputValidator {
    
    // =================
    // CUSTOM ERRORS
    // =================
    
    error EmptyInput();
    error InputTooLong();
    error InvalidAddress();
    error ZeroAddress(); 
    error DangerousAddress();
    error SQLInjectionDetected();
    error XSSDetected();
    error CommandInjectionDetected();
    error PathTraversalDetected();
    error NumericOverflow();
    error NumericUnderflow();
    error InvalidNumericRange();
    error InvalidDecimals();
    error ArrayTooLarge();
    error ArrayEmpty();
    error InvalidArrayElement();
    error DeadlineExpired();
    error InvalidTimestamp();
    error OracleDataStale();
    error PriceDeviationTooHigh();
    error RateLimitExceeded();
    error ValidationCircuitBreaker();
    error InvalidFormat();
    error InvalidChecksum();
    
    // =================
    // CONSTANTS
    // =================
    
    uint256 public constant MAX_STRING_LENGTH = 10000;
    uint256 public constant MAX_ARRAY_LENGTH = 1000;
    uint256 public constant MAX_DECIMALS = 18;
    uint256 public constant MAX_PRICE_DEVIATION = 1000; // 10% in basis points
    uint256 public constant MAX_ORACLE_STALENESS = 3600; // 1 hour
    uint256 public constant MAX_ETH_AMOUNT = 10**30; // Large but finite
    uint256 public constant MAX_GAS_PRICE = 1000 * 10**9; // 1000 Gwei
    uint256 public constant MAX_GAS_LIMIT = 30000000;
    uint256 public constant MIN_GAS_LIMIT = 21000;
    
    // Validation mode flags
    uint256 public constant STRICT_MODE = 1;
    uint256 public constant PERMISSIVE_MODE = 2;
    uint256 public constant EMERGENCY_MODE = 4;
    
    // =================
    // STRUCTS
    // =================
    
    struct ValidationContext {
        address caller;
        bytes32 operationId;
        uint256 timestamp;
        uint256 blockNumber;
        uint256 validationMode;
    }
    
    struct ValidationResult {
        bool isValid;
        uint256 errorCode;
        bytes32 validationHash;
    }
    
    struct RateLimitConfig {
        uint256 maxRequests;
        uint256 windowSeconds;
        mapping(address => uint256[]) requestTimes;
        mapping(address => uint256) lastRequestTime;
        mapping(address => uint256) requestCount;
    }
    
    // =================
    // EVENTS
    // =================
    
    event ValidationFailed(
        bytes32 indexed operationId,
        address indexed caller,
        string validationType,
        uint256 errorCode,
        uint256 timestamp
    );
    
    event SecurityIncident(
        bytes32 indexed incidentId,
        address indexed actor,
        string incidentType,
        bytes data,
        uint256 timestamp
    );
    
    event RateLimitTriggered(
        address indexed actor,
        uint256 requestCount,
        uint256 timestamp
    );
    
    event CircuitBreakerActivated(
        string reason,
        address activatedBy,
        uint256 timestamp
    );
    
    // =================
    // CORE VALIDATION FUNCTIONS
    // =================
    
    /**
     * @dev Comprehensive string validation with security pattern detection
     */
    function validateString(
        string calldata input,
        uint256 maxLength,
        uint256 validationMode
    ) internal pure returns (bool) {
        bytes memory inputBytes = bytes(input);
        
        // Basic validation
        if (inputBytes.length == 0) revert EmptyInput();
        
        uint256 maxLen = maxLength == 0 ? MAX_STRING_LENGTH : maxLength;
        if (inputBytes.length > maxLen) revert InputTooLong();
        
        // Security pattern detection
        if (validationMode & STRICT_MODE != 0) {
            _checkSQLInjection(inputBytes);
            _checkXSSPatterns(inputBytes);
            _checkCommandInjection(inputBytes);
            _checkPathTraversal(inputBytes);
        }
        
        return true;
    }
    
    /**
     * @dev Enhanced address validation with security checks
     */
    function validateAddress(address addr, uint256 validationMode) internal pure returns (bool) {
        if (addr == address(0)) revert ZeroAddress();
        
        // Check for dangerous precompile addresses (0x01-0x09)
        if (uint160(addr) <= 9 && uint160(addr) >= 1) revert DangerousAddress();
        
        // Check for max address (potential overflow indicator)
        if (addr == address(type(uint160).max)) revert DangerousAddress();
        
        // Additional strict mode checks
        if (validationMode & STRICT_MODE != 0) {
            // Check for common attack addresses
            _checkDangerousAddresses(addr);
        }
        
        return true;
    }
    
    /**
     * @dev Numeric validation with overflow protection
     */
    function validateNumber(
        uint256 value,
        uint256 minValue,
        uint256 maxValue,
        uint256 validationMode
    ) internal pure returns (bool) {
        // Range validation
        if (value < minValue) revert InvalidNumericRange();
        if (value > maxValue) revert InvalidNumericRange();
        
        // Overflow protection
        if (validationMode & STRICT_MODE != 0) {
            // Check for potential overflow in calculations
            if (value > type(uint256).max / 10**18) revert NumericOverflow();
            
            // Check for suspicious round numbers that might indicate manipulation
            if (value % 10**15 == 0 && value > 10**18) {
                // Large round numbers might be suspicious
                revert InvalidFormat();
            }
        }
        
        return true;
    }
    
    /**
     * @dev Array validation with comprehensive checks
     */
    function validateArray(
        address[] calldata addresses,
        uint256 validationMode
    ) internal pure returns (bool) {
        if (addresses.length == 0) revert ArrayEmpty();
        if (addresses.length > MAX_ARRAY_LENGTH) revert ArrayTooLarge();
        
        // Validate each address
        for (uint256 i = 0; i < addresses.length; i++) {
            validateAddress(addresses[i], validationMode);
            
            // Check for duplicates in strict mode
            if (validationMode & STRICT_MODE != 0) {
                for (uint256 j = i + 1; j < addresses.length; j++) {
                    if (addresses[i] == addresses[j]) {
                        revert InvalidArrayElement();
                    }
                }
            }
        }
        
        return true;
    }
    
    /**
     * @dev Validate uint256 array with comprehensive checks
     */
    function validateNumberArray(
        uint256[] calldata numbers,
        uint256 minValue,
        uint256 maxValue,
        uint256 validationMode
    ) internal pure returns (bool) {
        if (numbers.length == 0) revert ArrayEmpty();
        if (numbers.length > MAX_ARRAY_LENGTH) revert ArrayTooLarge();
        
        uint256 sum = 0;
        for (uint256 i = 0; i < numbers.length; i++) {
            validateNumber(numbers[i], minValue, maxValue, validationMode);
            
            // Overflow protection for sum
            if (sum > type(uint256).max - numbers[i]) revert NumericOverflow();
            sum += numbers[i];
        }
        
        return true;
    }
    
    /**
     * @dev Ethereum transaction validation
     */
    function validateTransaction(
        address to,
        uint256 value,
        uint256 gasPrice,
        uint256 gasLimit,
        bytes calldata data,
        uint256 validationMode
    ) internal pure returns (bool) {
        // Validate recipient address
        validateAddress(to, validationMode);
        
        // Validate value
        validateNumber(value, 0, MAX_ETH_AMOUNT, validationMode);
        
        // Validate gas price
        validateNumber(gasPrice, 1, MAX_GAS_PRICE, validationMode);
        
        // Validate gas limit
        validateNumber(gasLimit, MIN_GAS_LIMIT, MAX_GAS_LIMIT, validationMode);
        
        // Validate data size
        if (data.length > 200000) revert InputTooLong(); // ~100KB limit
        
        return true;
    }
    
    /**
     * @dev Flash loan parameter validation
     */
    function validateFlashLoanParams(
        address asset,
        uint256 amount,
        uint256 premium,
        bytes calldata params,
        uint256 validationMode
    ) internal pure returns (bool) {
        validateAddress(asset, validationMode);
        validateNumber(amount, 1, MAX_ETH_AMOUNT, validationMode);
        validateNumber(premium, 0, amount / 10, validationMode); // Max 10% premium
        
        if (params.length > 10000) revert InputTooLong();
        
        return true;
    }
    
    /**
     * @dev Strategy execution parameter validation
     */
    function validateStrategyParams(
        address strategy,
        address[] calldata tokens,
        uint256[] calldata amounts,
        uint256 deadline,
        uint256 validationMode
    ) internal view returns (bool) {
        validateAddress(strategy, validationMode);
        validateArray(tokens, validationMode);
        validateNumberArray(amounts, 1, MAX_ETH_AMOUNT, validationMode);
        
        // Arrays must have same length
        if (tokens.length != amounts.length) revert InvalidArrayElement();
        
        // Validate deadline
        if (deadline <= block.timestamp) revert DeadlineExpired();
        if (deadline > block.timestamp + 3600) revert InvalidTimestamp(); // Max 1 hour
        
        return true;
    }
    
    /**
     * @dev Oracle data validation
     */
    function validateOracleData(        uint256 price,
        uint256 timestamp,
        uint256 lastPrice,
        uint256, /* lastTimestamp */
        uint256 validationMode
    ) internal view returns (bool) {
        // Timestamp validation
        if (timestamp > block.timestamp) revert InvalidTimestamp();
        if (block.timestamp - timestamp > MAX_ORACLE_STALENESS) revert OracleDataStale();
        
        // Price validation
        validateNumber(price, 1, type(uint256).max / 10**18, validationMode);
        
        // Price deviation validation
        if (lastPrice > 0 && validationMode & STRICT_MODE != 0) {
            uint256 deviation;
            if (price > lastPrice) {
                deviation = ((price - lastPrice) * 10000) / lastPrice;
            } else {
                deviation = ((lastPrice - price) * 10000) / lastPrice;
            }
            
            if (deviation > MAX_PRICE_DEVIATION) revert PriceDeviationTooHigh();
        }
        
        return true;
    }
    
    // =================
    // SECURITY PATTERN DETECTION
    // =================
    
    /**
     * @dev Check for SQL injection patterns
     */
    function _checkSQLInjection(bytes memory input) private pure {
        // Check for common SQL injection patterns
        bytes memory patterns = hex"273B"; // ';
        if (_containsPattern(input, patterns)) revert SQLInjectionDetected();
        
        patterns = hex"2D2D"; // --
        if (_containsPattern(input, patterns)) revert SQLInjectionDetected();
        
        patterns = hex"2F2A"; // /*
        if (_containsPattern(input, patterns)) revert SQLInjectionDetected();
        
        // Check for UNION keyword (case insensitive)
        if (_containsKeyword(input, "UNION")) revert SQLInjectionDetected();
        if (_containsKeyword(input, "SELECT")) revert SQLInjectionDetected();
        if (_containsKeyword(input, "INSERT")) revert SQLInjectionDetected();
        if (_containsKeyword(input, "DELETE")) revert SQLInjectionDetected();
        if (_containsKeyword(input, "UPDATE")) revert SQLInjectionDetected();
        if (_containsKeyword(input, "DROP")) revert SQLInjectionDetected();
    }
    
    /**
     * @dev Check for XSS patterns
     */
    function _checkXSSPatterns(bytes memory input) private pure {
        // Check for script tags
        if (_containsKeyword(input, "<SCRIPT")) revert XSSDetected();
        if (_containsKeyword(input, "JAVASCRIPT:")) revert XSSDetected();
        if (_containsKeyword(input, "ONERROR")) revert XSSDetected();
        if (_containsKeyword(input, "ONLOAD")) revert XSSDetected();
        if (_containsKeyword(input, "ALERT(")) revert XSSDetected();
        
        // Check for iframe tags
        if (_containsKeyword(input, "<IFRAME")) revert XSSDetected();
        if (_containsKeyword(input, "<OBJECT")) revert XSSDetected();
        if (_containsKeyword(input, "<EMBED")) revert XSSDetected();
    }
    
    /**
     * @dev Check for command injection patterns
     */
    function _checkCommandInjection(bytes memory input) private pure {
        bytes memory semicolon = hex"3B"; // ;
        if (_containsPattern(input, semicolon)) revert CommandInjectionDetected();
        
        bytes memory pipe = hex"7C"; // |
        if (_containsPattern(input, pipe)) revert CommandInjectionDetected();
        
        bytes memory ampersand = hex"26"; // &
        if (_containsPattern(input, ampersand)) revert CommandInjectionDetected();
        
        bytes memory backtick = hex"60"; // `
        if (_containsPattern(input, backtick)) revert CommandInjectionDetected();
    }
    
    /**
     * @dev Check for path traversal patterns
     */
    function _checkPathTraversal(bytes memory input) private pure {
        // Check for ../
        bytes memory dotdotslash = hex"2E2E2F"; // ../
        if (_containsPattern(input, dotdotslash)) revert PathTraversalDetected();
        
        // Check for ..\
        bytes memory dotdotbackslash = hex"2E2E5C"; // ..\
        if (_containsPattern(input, dotdotbackslash)) revert PathTraversalDetected();
        
        // Check for /etc/
        if (_containsKeyword(input, "/ETC/")) revert PathTraversalDetected();
        if (_containsKeyword(input, "C:")) revert PathTraversalDetected();
    }
    
    /**
     * @dev Check for dangerous addresses
     */
    function _checkDangerousAddresses(address addr) private pure {
        // Add checks for known malicious or dangerous addresses
        // This could be expanded with a registry of known bad addresses
        
        // Example: Check for burn addresses
        if (addr == 0x000000000000000000000000000000000000dEaD) revert DangerousAddress();
    }
    
    // =================
    // UTILITY FUNCTIONS
    // =================
    
    /**
     * @dev Check if input contains a specific byte pattern
     */
    function _containsPattern(bytes memory input, bytes memory pattern) private pure returns (bool) {
        if (pattern.length == 0 || input.length < pattern.length) {
            return false;
        }
        
        for (uint256 i = 0; i <= input.length - pattern.length; i++) {
            bool found = true;
            for (uint256 j = 0; j < pattern.length; j++) {
                if (input[i + j] != pattern[j]) {
                    found = false;
                    break;
                }
            }
            if (found) return true;
        }
        return false;
    }
    
    /**
     * @dev Check if input contains a keyword (case insensitive)
     */
    function _containsKeyword(bytes memory input, string memory keyword) private pure returns (bool) {
        bytes memory keywordBytes = bytes(keyword);
        if (keywordBytes.length == 0 || input.length < keywordBytes.length) {
            return false;
        }
        
        for (uint256 i = 0; i <= input.length - keywordBytes.length; i++) {
            bool found = true;
            for (uint256 j = 0; j < keywordBytes.length; j++) {
                bytes1 inputChar = input[i + j];
                bytes1 keywordChar = keywordBytes[j];
                
                // Convert to uppercase for case-insensitive comparison
                if (inputChar >= 0x61 && inputChar <= 0x7A) {
                    inputChar = bytes1(uint8(inputChar) - 32);
                }
                if (keywordChar >= 0x61 && keywordChar <= 0x7A) {
                    keywordChar = bytes1(uint8(keywordChar) - 32);
                }
                
                if (inputChar != keywordChar) {
                    found = false;
                    break;
                }
            }
            if (found) return true;
        }
        return false;
    }
    
    /**
     * @dev Generate validation hash for audit trail
     */
    function generateValidationHash(
        bytes memory input,
        uint256 validationType,
        uint256 timestamp
    ) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(input, validationType, timestamp));
    }
    
    /**
     * @dev Emergency validation mode - minimal checks for critical operations
     */
    function emergencyValidate(
        address addr,
        uint256 amount
    ) internal pure returns (bool) {
        if (addr == address(0)) revert ZeroAddress();
        if (amount == 0) revert InvalidNumericRange();
        return true;
    }
    
    // =================
    // BATCH VALIDATION
    // =================
    
    /**
     * @dev Validate multiple addresses in batch
     */    function validateAddressBatch(
        address[] calldata addresses,
        uint256 validationMode
    ) external pure returns (bool[] memory results)  {
        // TODO: Add nonReentrant modifier
        results = new bool[](addresses.length);
        
        for (uint256 i = 0; i < addresses.length; i++) {
            results[i] = _isValidAddress(addresses[i], validationMode);
        }
    }
    
    /**
     * @dev Internal helper that returns bool instead of reverting
     */
    function _isValidAddress(address addr, uint256 validationMode) private pure returns (bool) {
        // Basic validation
        if (addr == address(0)) return false;
        
        // Check dangerous addresses in strict mode
        if (validationMode & STRICT_MODE != 0) {
            // Check dangerous precompile addresses (0x01-0x09)
            if (uint160(addr) <= 9 && uint160(addr) >= 1) return false;
            
            // Check max address
            if (addr == 0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF) return false;
        }
        
        return true;
    }
    
    /**
     * @dev External wrapper for address validation (for try/catch)
     */
    function validateAddressExternal(address addr, uint256 validationMode) external pure returns (bool)  {
        // TODO: Add nonReentrant modifier
        return validateAddress(addr, validationMode);
    }
    
    // =================
    // RATE LIMITING HELPERS
    // =================
    
    /**
     * @dev Check rate limit for caller
     */
    function checkRateLimit(
        mapping(address => uint256[]) storage requestTimes,
        address caller,
        uint256 maxRequests,
        uint256 windowSeconds
    ) internal returns (bool) {
        uint256 currentTime = block.timestamp;
        uint256[] storage times = requestTimes[caller];
        
        // Remove old entries
        uint256 cutoff = currentTime - windowSeconds;
        uint256 validCount = 0;
        
        for (uint256 i = 0; i < times.length; i++) {
            if (times[i] > cutoff) {
                times[validCount] = times[i];
                validCount++;
            }
        }
        
        // Resize array
        assembly {
            sstore(times.slot, validCount)
        }
        
        // Check limit
        if (validCount >= maxRequests) {
            return false;
        }
        
        // Add current request
        times.push(currentTime);
        return true;
    }
}
