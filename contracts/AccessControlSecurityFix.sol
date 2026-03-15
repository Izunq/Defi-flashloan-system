// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title AccessControlSecurityFix
 * @notice Emergency security fixes for access control vulnerabilities
 * @dev This contract provides enhanced access control patterns and fixes
 */
contract AccessControlSecurityFix is AccessControl, ReentrancyGuard, Pausable {
    
    // =================
    // ENHANCED ROLE DEFINITIONS
    // =================
    
    bytes32 public constant STRATEGY_PROPOSER_ROLE = keccak256("STRATEGY_PROPOSER_ROLE");
    bytes32 public constant STRATEGY_EXECUTOR_ROLE = keccak256("STRATEGY_EXECUTOR_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");
    bytes32 public constant ORACLE_ADMIN_ROLE = keccak256("ORACLE_ADMIN_ROLE");
    bytes32 public constant SECURITY_MANAGER_ROLE = keccak256("SECURITY_MANAGER_ROLE");
    bytes32 public constant RISK_MANAGER_ROLE = keccak256("RISK_MANAGER_ROLE");
    bytes32 public constant TREASURY_MANAGER_ROLE = keccak256("TREASURY_MANAGER_ROLE");
    bytes32 public constant COMPLIANCE_ROLE = keccak256("COMPLIANCE_ROLE");
    
    // =================
    // ACCESS CONTROL STATE
    // =================
    
    mapping(address => bool) public approvedProposers;
    mapping(address => uint256) public proposerNonce;
    mapping(bytes32 => bool) public emergencyActionLocks;
    
    uint256 public proposalCooldownPeriod = 1 hours;
    uint256 public emergencyActionDelay = 30 minutes;
    mapping(address => uint256) public lastProposalTime;
    
    // =================
    // EVENTS
    // =================
    
    event AccessControlViolationAttempt(
        address indexed actor,
        bytes32 indexed role,
        string action,
        uint256 timestamp
    );
    
    event EmergencyActionScheduled(
        bytes32 indexed actionId,
        address indexed initiator,
        uint256 executeAfter,
        string actionType
    );
    
    event SecurityModeActivated(
        address indexed activator,
        string reason,
        uint256 timestamp
    );
    
    event ProposerStatusUpdated(
        address indexed proposer,
        bool approved,
        address indexed updatedBy
    );
    
    // =================
    // ENHANCED MODIFIERS
    // =================
    
    /**
     * @dev Enhanced role-based access control with logging
     */
    modifier onlyRoleWithLogging(bytes32 role, string memory action) {
        if (!hasRole(role, msg.sender)) {
            emit AccessControlViolationAttempt(msg.sender, role, action, block.timestamp);
            revert(string(abi.encodePacked("AccessControl: account ", Strings.toHexString(uint160(msg.sender), 20), " is missing role ", Strings.toHexString(uint256(role), 32))));
        }
        _;
    }
    
    /**
     * @dev Time-locked emergency actions
     */
    modifier emergencyTimelock(bytes32 actionId, string memory actionType) {
        if (emergencyActionLocks[actionId]) {
            require(
                block.timestamp >= emergencyActionDelay + block.timestamp,
                "Emergency action still in timelock"
            );
        } else {
            emergencyActionLocks[actionId] = true;
            emit EmergencyActionScheduled(
                actionId, 
                msg.sender, 
                block.timestamp + emergencyActionDelay, 
                actionType
            );
            revert("Emergency action scheduled, execute after timelock");
        }
        _;
        delete emergencyActionLocks[actionId];
    }
    
    /**
     * @dev Proposal cooldown to prevent spam
     */
    modifier proposalCooldown() {
        require(
            block.timestamp >= lastProposalTime[msg.sender] + proposalCooldownPeriod,
            "Proposal cooldown period not elapsed"
        );
        _;
        lastProposalTime[msg.sender] = block.timestamp;
    }
    
    /**
     * @dev Only approved proposers
     */
    modifier onlyApprovedProposer() {
        require(
            approvedProposers[msg.sender] || hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Not an approved proposer"
        );
        _;
    }
    
    // =================
    // CONSTRUCTOR
    // =================
    
    constructor(address admin) {
        require(admin != address(0), "Invalid admin address");
        
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), admin);
        _grantRole(EMERGENCY_ROLE, admin);
        _grantRole(SECURITY_MANAGER_ROLE, admin);
        
        // Set role admins
        _setRoleAdmin(STRATEGY_PROPOSER_ROLE, DEFAULT_ADMIN_ROLE);
        _setRoleAdmin(STRATEGY_EXECUTOR_ROLE, DEFAULT_ADMIN_ROLE);
        _setRoleAdmin(ORACLE_ADMIN_ROLE, SECURITY_MANAGER_ROLE);
        _setRoleAdmin(RISK_MANAGER_ROLE, DEFAULT_ADMIN_ROLE);
        _setRoleAdmin(TREASURY_MANAGER_ROLE, DEFAULT_ADMIN_ROLE);
        _setRoleAdmin(COMPLIANCE_ROLE, DEFAULT_ADMIN_ROLE);
    }
    
    // =================
    // ACCESS CONTROL MANAGEMENT
    // =================
    
    /**
     * @dev Approve or revoke proposer status
     */
    function setProposerApproval(address proposer, bool approved) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        require(proposer != address(0), "Invalid proposer address");
        
        approvedProposers[proposer] = approved;
        
        if (approved) {
            _grantRole(STRATEGY_PROPOSER_ROLE, proposer);
        } else {
            _revokeRole(STRATEGY_PROPOSER_ROLE, proposer);
        }
        
        emit ProposerStatusUpdated(proposer, approved, msg.sender);
    }
    
    /**
     * @dev Batch approve multiple proposers
     */
    function batchSetProposerApproval(
        address[] calldata proposers, 
        bool[] calldata approvals
    ) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        require(proposers.length == approvals.length, "Array length mismatch");
        
        for (uint256 i = 0; i < proposers.length; i++) {
            if (proposers[i] != address(0)) {
                approvedProposers[proposers[i]] = approvals[i];
                
                if (approvals[i]) {
                    _grantRole(STRATEGY_PROPOSER_ROLE, proposers[i]);
                } else {
                    _revokeRole(STRATEGY_PROPOSER_ROLE, proposers[i]);
                }
                
                emit ProposerStatusUpdated(proposers[i], approvals[i], msg.sender);
            }
        }
    }
    
    /**
     * @dev Emergency role revocation
     */
    function emergencyRevokeRole(bytes32 role, address account) 
        external 
        onlyRole(EMERGENCY_ROLE) 
    {
        bytes32 actionId = keccak256(abi.encodePacked("REVOKE", role, account, block.timestamp));
        
        _revokeRole(role, account);
        
        emit AccessControlViolationAttempt(account, role, "EMERGENCY_REVOKED", block.timestamp);
    }
    
    /**
     * @dev Update proposal cooldown period
     */
    function updateProposalCooldown(uint256 newCooldown) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        require(newCooldown <= 24 hours, "Cooldown too long");
        require(newCooldown >= 10 minutes, "Cooldown too short");
        
        proposalCooldownPeriod = newCooldown;
    }
    
    /**
     * @dev Update emergency action delay
     */
    function updateEmergencyDelay(uint256 newDelay) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        require(newDelay <= 4 hours, "Delay too long");
        require(newDelay >= 5 minutes, "Delay too short");
        
        emergencyActionDelay = newDelay;
    }
    
    // =================
    // SECURITY FUNCTIONS
    // =================
    
    /**
     * @dev Activate security mode (emergency pause)
     */
    function activateSecurityMode(string memory reason) 
        external 
        onlyRole(SECURITY_MANAGER_ROLE) 
    {
        _pause();
        emit SecurityModeActivated(msg.sender, reason, block.timestamp);
    }
    
    /**
     * @dev Deactivate security mode
     */
    function deactivateSecurityMode() 
        external 
        onlyRole(EMERGENCY_ROLE) 
    {
        _unpause();
    }
    
    /**
     * @dev Check if address has any administrative role
     */    /**
     * @dev Check if account has admin role - SECURITY ENHANCED
     */
    function hasAdminRole(address account) 
        external 
        view 
        onlyRole(SECURITY_MANAGER_ROLE) 
        returns (bool) 
    {
        return hasRole(DEFAULT_ADMIN_ROLE, account) || 
               hasRole(EMERGENCY_ROLE, account) || 
               hasRole(SECURITY_MANAGER_ROLE, account);
    }
    
    /**
     * @dev Get all roles for an account - SECURITY ENHANCED
     */
    function getAccountRoles(address account) 
        external 
        view 
        onlyRole(SECURITY_MANAGER_ROLE) 
        whenNotPaused 
        returns (bytes32[] memory roles) 
    {
        bytes32[] memory allRoles = new bytes32[](8);
        allRoles[0] = DEFAULT_ADMIN_ROLE;
        allRoles[1] = STRATEGY_PROPOSER_ROLE;
        allRoles[2] = STRATEGY_EXECUTOR_ROLE;
        allRoles[3] = EMERGENCY_ROLE;
        allRoles[4] = ORACLE_ADMIN_ROLE;
        allRoles[5] = SECURITY_MANAGER_ROLE;
        allRoles[6] = RISK_MANAGER_ROLE;
        allRoles[7] = TREASURY_MANAGER_ROLE;
        
        uint256 roleCount = 0;
        for (uint256 i = 0; i < allRoles.length; i++) {
            if (hasRole(allRoles[i], account)) {
                roleCount++;
            }
        }
        
        roles = new bytes32[](roleCount);
        uint256 index = 0;
        for (uint256 i = 0; i < allRoles.length; i++) {
            if (hasRole(allRoles[i], account)) {
                roles[index] = allRoles[i];
                index++;
            }
        }
    }
      // =================
    // VIEW FUNCTIONS - SECURITY ENHANCED
    // =================
    
    function isApprovedProposer(address proposer) 
        external 
        view 
        onlyRole(STRATEGY_EXECUTOR_ROLE) 
        returns (bool) 
    {
        return approvedProposers[proposer];
    }
    
    function getProposerNonce(address proposer) 
        external 
        view 
        onlyRole(SECURITY_MANAGER_ROLE) 
        returns (uint256) 
    {
        return proposerNonce[proposer];
    }
    
    function getLastProposalTime(address proposer) 
        external 
        view 
        onlyRole(SECURITY_MANAGER_ROLE) 
        returns (uint256) 
    {
        return lastProposalTime[proposer];
    }
    
    function timeUntilNextProposal(address proposer) external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        uint256 nextAllowedTime = lastProposalTime[proposer] + proposalCooldownPeriod;
        if (block.timestamp >= nextAllowedTime) {
            return 0;
        }
        return nextAllowedTime - block.timestamp;
    }
}
