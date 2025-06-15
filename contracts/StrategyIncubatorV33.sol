// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
// import "./interfaces/IZKVerifier.sol"; // If ZK features are used

contract StrategyIncubatorV33 is Ownable, AccessControl, ReentrancyGuard, Pausable {
    // IZKVerifier public zkVerifier; // If ZK features are used
    
    // Define the roles
    bytes32 public constant STRATEGY_PROPOSER_ROLE = keccak256("STRATEGY_PROPOSER_ROLE");
    bytes32 public constant STRATEGY_EXECUTOR_ROLE = keccak256("STRATEGY_EXECUTOR_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");

    enum StrategyStatus { Proposed, Testing, Approved, Rejected, Live }

    struct StrategyDetails {
        address strategyAddress;
        address proposer;
        uint256 baseStrategyId; // ID of the strategy it was derived from, if variant
        bool isVariant;
        StrategyStatus status;
        uint256 proposalTimestamp;
        // bytes32 zkProofHash; // If ZK features are used
        // uint256 publicSignal; // If ZK features are used
        uint256 performanceScore; // Example: could be profit, win rate, etc.
        uint256 testsPassed;
        uint256 testsFailed;
    }

    uint256 public strategyCounter;
    mapping(uint256 => StrategyDetails) public strategies;
    mapping(address => uint256) public strategyIds; // strategy address to its incubator ID

    event StrategyProposed(
        uint256 indexed strategyId,
        address indexed strategyAddress,
        address indexed proposer,
        uint256 baseStrategyId,
        bool isVariant
    );
    event StrategyStatusUpdated(uint256 indexed strategyId, StrategyStatus newStatus);
    // event ZKProofSubmitted(uint256 indexed strategyId, bytes32 proofHash, uint256 publicSignal); // If ZK    constructor(address initialOwner/*, address _zkVerifierAddress*/) Ownable(initialOwner) {
        // zkVerifier = IZKVerifier(_zkVerifierAddress); // If ZK
        
        // Setup roles
        _grantRole(DEFAULT_ADMIN_ROLE, initialOwner);
        _grantRole(EMERGENCY_ROLE, initialOwner);
    }    // Production: proposeStrategy is onlyOwner
    function proposeStrategy(
        address _strategyAddress,
        uint256 _baseStrategyId, // 0 if not a variant
        bool _isVariant
    ) external onlyRole(STRATEGY_PROPOSER_ROLE) whenNotPaused nonReentrant returns (uint256 strategyId) {
        require(_strategyAddress != address(0), "Incubator: Zero address strategy");
        require(strategyIds[_strategyAddress] == 0, "Incubator: Strategy already proposed");

        strategyCounter++;
        strategyId = strategyCounter;

        strategies[strategyId] = StrategyDetails({
            strategyAddress: _strategyAddress,
            proposer: msg.sender, // Owner is the agent
            baseStrategyId: _baseStrategyId,
            isVariant: _isVariant,
            status: StrategyStatus.Proposed,
            proposalTimestamp: block.timestamp,
            // zkProofHash: bytes32(0), // If ZK
            // publicSignal: 0, // If ZK
            performanceScore: 0,
            testsPassed: 0,
            testsFailed: 0
        });
        strategyIds[_strategyAddress] = strategyId;

        emit StrategyProposed(strategyId, _strategyAddress, msg.sender, _baseStrategyId, _isVariant);
        return strategyId;
    }

    // ... (other functions: updateStatus, recordTestResult, submitZKProof (if ZK), etc.) ...

    function updateStrategyStatus(uint256 _strategyId, StrategyStatus _newStatus) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(strategies[_strategyId].strategyAddress != address(0), "Incubator: Strategy not found");
        strategies[_strategyId].status = _newStatus;
        emit StrategyStatusUpdated(_strategyId, _newStatus);
    }

    function getStrategy(uint256 _strategyId) external view returns (StrategyDetails memory) {
        require(strategies[_strategyId].strategyAddress != address(0), "Incubator: Strategy not found");
        return strategies[_strategyId];
    }

    function recordTestResult(uint256 _strategyId, bool _passed) external onlyRole(STRATEGY_EXECUTOR_ROLE) {
        require(strategies[_strategyId].strategyAddress != address(0), "Incubator: Strategy not found");
        
        if (_passed) {
            strategies[_strategyId].testsPassed++;
        } else {
            strategies[_strategyId].testsFailed++;
        }
    }

    function updatePerformanceScore(uint256 _strategyId, uint256 _score) external onlyRole(STRATEGY_EXECUTOR_ROLE) {
        require(strategies[_strategyId].strategyAddress != address(0), "Incubator: Strategy not found");
        strategies[_strategyId].performanceScore = _score;
    }

    function getStrategyCount() external view returns (uint256) {
        return strategyCounter;
    }

    function getAllStrategies() external view returns (StrategyDetails[] memory) {
        StrategyDetails[] memory allStrategies = new StrategyDetails[](strategyCounter);
        
        for (uint256 i = 1; i <= strategyCounter; i++) {
            allStrategies[i - 1] = strategies[i];
        }
        
        return allStrategies;
    }

    function getStrategiesByStatus(StrategyStatus _status) external view returns (uint256[] memory) {
        uint256[] memory tempIds = new uint256[](strategyCounter);
        uint256 count = 0;
        
        for (uint256 i = 1; i <= strategyCounter; i++) {
            if (strategies[i].status == _status) {
                tempIds[count] = i;
                count++;
            }
        }
        
        // Create properly sized array
        uint256[] memory result = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = tempIds[i];
        }
        
        return result;
    }
}