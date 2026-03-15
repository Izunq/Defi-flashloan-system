// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title SystemAccessControl
 * @dev Centralized access control for the entire system.
 * Defines all major roles.
 */
contract SystemAccessControl is AccessControl {
    // Role for top-level administrative tasks
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    
    // Role for pausing/unpausing the system in emergencies
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    
    // Role for managing oracle sources and configurations
    bytes32 public constant ORACLE_MANAGER_ROLE = keccak256("ORACLE_MANAGER_ROLE");

    // Role for bots or accounts allowed to execute arbitrage trades
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");

    constructor(address initialAdmin, address initialExecutor, address initialPauser) {
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), initialAdmin);
        _grantRole(ADMIN_ROLE, initialAdmin);
        _grantRole(EXECUTOR_ROLE, initialExecutor);
        _grantRole(PAUSER_ROLE, initialPauser);
    }
}
