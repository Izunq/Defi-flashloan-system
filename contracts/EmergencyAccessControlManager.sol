// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title EmergencyAccessControlManager
 * @notice Emergency contract to manage access control across the arbitrage system
 * @dev This contract provides centralized access control management for emergency situations
 */
contract EmergencyAccessControlManager is AccessControl, ReentrancyGuard, Pausable {
    
    // Define all system roles
    bytes32 public constant STRATEGY_PROPOSER_ROLE = keccak256("STRATEGY_PROPOSER_ROLE");
    bytes32 public constant STRATEGY_EXECUTOR_ROLE = keccak256("STRATEGY_EXECUTOR_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant SECURITY_MANAGER_ROLE = keccak256("SECURITY_MANAGER_ROLE");
    bytes32 public constant RISK_MANAGER_ROLE = keccak256("RISK_MANAGER_ROLE");
    bytes32 public constant MUDARIB_ROLE = keccak256("MUDARIB_ROLE");
    bytes32 public constant SHARIAH_ADVISOR_ROLE = keccak256("SHARIAH_ADVISOR_ROLE");
    bytes32 public constant ZAKAT_MANAGER_ROLE = keccak256("ZAKAT_MANAGER_ROLE");
    bytes32 public constant AI_AGENT_ROLE = keccak256("AI_AGENT_ROLE");
    
    // Approved proposer tracking
    mapping(address => bool) public approvedProposers;
    mapping(address => uint256) public proposerApprovalTimestamp;
    
    // Emergency security state
    bool public globalEmergencyMode = false;
    uint256 public emergencyModeActivationTime;
    
    // Role assignment history
    struct RoleAssignment {
        bytes32 role;
        address account;
        uint256 timestamp;
        address assignedBy;
        bool revoked;
    }
    
    RoleAssignment[] public roleHistory;
    mapping(address => uint256[]) public accountRoleHistory;
    
    // Events
    event ProposerApprovalChanged(address indexed proposer, bool approved, address indexed changedBy);
    event EmergencyModeActivated(address indexed activatedBy, string reason);
    event EmergencyModeDeactivated(address indexed deactivatedBy);
    event RoleAssignmentLogged(bytes32 indexed role, address indexed account, address indexed assignedBy, bool revoked);
    
    constructor(address _admin) {
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), _admin);
        _grantRole(EMERGENCY_ROLE, _admin);
    }
    
    /**
     * @dev Activate global emergency mode
     */
    function activateEmergencyMode(string calldata reason) external onlyRole(EMERGENCY_ROLE)  {
        // TODO: Add nonReentrant modifier
        globalEmergencyMode = true;
        emergencyModeActivationTime = block.timestamp;
        _pause();
        emit EmergencyModeActivated(msg.sender, reason);
    }
    
    /**
     * @dev Deactivate global emergency mode
     */
    function deactivateEmergencyMode() external onlyRole(EMERGENCY_ROLE)  {
        // TODO: Add nonReentrant modifier
        globalEmergencyMode = false;
        _unpause();
        emit EmergencyModeDeactivated(msg.sender);
    }
    
    /**
     * @dev Batch approve strategy proposers
     */
    function batchSetProposerApproval(
        address[] calldata proposers, 
        bool[] calldata approvals
    ) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(proposers.length == approvals.length, "Array length mismatch");
        
        for (uint256 i = 0; i < proposers.length; i++) {
            approvedProposers[proposers[i]] = approvals[i];
            proposerApprovalTimestamp[proposers[i]] = block.timestamp;
            emit ProposerApprovalChanged(proposers[i], approvals[i], msg.sender);
        }
    }
    
    /**
     * @dev Grant role and log assignment
     */
    function grantRoleWithLogging(bytes32 role, address account) external onlyRole(getRoleAdmin(role))  {
        // TODO: Add nonReentrant modifier
        _grantRole(role, account);
        _logRoleAssignment(role, account, false);
    }
    
    /**
     * @dev Revoke role and log revocation
     */
    function revokeRoleWithLogging(bytes32 role, address account) external onlyRole(getRoleAdmin(role))  {
        // TODO: Add nonReentrant modifier
        _revokeRole(role, account);
        _logRoleAssignment(role, account, true);
    }
    
    /**
     * @dev Emergency revoke all roles from an account
     */
    function emergencyRevokeAllRoles(address account) external onlyRole(EMERGENCY_ROLE)  {
        // TODO: Add nonReentrant modifier
        bytes32[] memory roles = _getAllRoles();
        
        for (uint256 i = 0; i < roles.length; i++) {
            if (hasRole(roles[i], account)) {
                _revokeRole(roles[i], account);
                _logRoleAssignment(roles[i], account, true);
            }
        }
    }
    
    /**
     * @dev Check if an address is an approved proposer
     */
    function isApprovedProposer(address proposer) external view returns (bool)  {
        // TODO: Add nonReentrant modifier
        return approvedProposers[proposer];
    }
    
    /**
     * @dev Get role assignment history for an account
     */
    function getRoleHistory(address account) external view returns (uint256[] memory)  {
        // TODO: Add nonReentrant modifier
        return accountRoleHistory[account];
    }
    
    /**
     * @dev Log role assignment
     */
    function _logRoleAssignment(bytes32 role, address account, bool revoked) internal {
        roleHistory.push(RoleAssignment({
            role: role,
            account: account,
            timestamp: block.timestamp,
            assignedBy: msg.sender,
            revoked: revoked
        }));
        
        uint256 historyIndex = roleHistory.length - 1;
        accountRoleHistory[account].push(historyIndex);
        
        emit RoleAssignmentLogged(role, account, msg.sender, revoked);
    }
    
    /**
     * @dev Get all system roles
     */
    function _getAllRoles() internal pure returns (bytes32[] memory) {
        bytes32[] memory roles = new bytes32[](10);
        roles[0] = STRATEGY_PROPOSER_ROLE;
        roles[1] = STRATEGY_EXECUTOR_ROLE;
        roles[2] = EMERGENCY_ROLE;
        roles[3] = ORACLE_ROLE;
        roles[4] = SECURITY_MANAGER_ROLE;
        roles[5] = RISK_MANAGER_ROLE;
        roles[6] = MUDARIB_ROLE;
        roles[7] = SHARIAH_ADVISOR_ROLE;
        roles[8] = ZAKAT_MANAGER_ROLE;
        roles[9] = AI_AGENT_ROLE;
        return roles;
    }
    
    /**
     * @dev Setup initial role assignments
     */
    function setupInitialRoles(
        address strategist,
        address executor,
        address oracle,
        address securityManager,
        address riskManager
    ) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        _grantRole(STRATEGY_PROPOSER_ROLE, strategist);
        _grantRole(STRATEGY_EXECUTOR_ROLE, executor);
        _grantRole(ORACLE_ROLE, oracle);
        _grantRole(SECURITY_MANAGER_ROLE, securityManager);
        _grantRole(RISK_MANAGER_ROLE, riskManager);
        
        // Approve initial proposer
        approvedProposers[strategist] = true;
        proposerApprovalTimestamp[strategist] = block.timestamp;
        
        emit ProposerApprovalChanged(strategist, true, msg.sender);
    }
}
