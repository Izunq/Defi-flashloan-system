// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ReentrancyGuard
 * @dev Provides a modifier to prevent reentrancy attacks.
 */
abstract contract CustomReentrancyGuard {
    // Using uint256 for status: 1 for ENTERED, 2 for NOT_ENTERED.
    // This is slightly more gas-efficient than a boolean.
    uint256 private _status;

    constructor() {
        _status = 2; // NOT_ENTERED
    }

    /**
     * @dev Prevents a contract from calling itself, directly or indirectly.
     */
    modifier nonReentrant() {
        require(_status != 1, "ReentrancyGuard: reentrant call");
        _status = 1; // Mark as ENTERED
        _;
        _status = 2; // Reset to NOT_ENTERED
    }
}
