// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title InputValidationTemplate
 * @notice Template for secure input validation
 */
library InputValidationTemplate {
    
    // Address validation
    function validateAddress(address _addr) internal pure {
        require(_addr != address(0), "Invalid address: zero address");
        require(_addr != address(0xdead), "Invalid address: dead address");
    }
    
    // Amount validation
    function validateAmount(uint256 _amount, uint256 _maxAmount) internal pure {
        require(_amount > 0, "Invalid amount: must be positive");
        require(_amount <= _maxAmount, "Invalid amount: exceeds maximum");
    }
    
    // Array validation
    function validateArrayLength(uint256 _length, uint256 _maxLength) internal pure {
        require(_length > 0, "Invalid array: empty array");
        require(_length <= _maxLength, "Invalid array: too long");
    }
    
    // Percentage validation (in basis points)
    function validatePercentage(uint256 _percentage) internal pure {
        require(_percentage <= 10000, "Invalid percentage: exceeds 100%");
    }
    
    // Time validation
    function validateTimestamp(uint256 _timestamp) internal view {
        require(_timestamp >= block.timestamp, "Invalid timestamp: in the past");
        require(_timestamp <= block.timestamp + 365 days, "Invalid timestamp: too far in future");
    }
}
