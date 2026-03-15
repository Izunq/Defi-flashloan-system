// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/proxy/transparent/TransparentUpgradeableProxy.sol";
import "@openzeppelin/contracts/proxy/transparent/ProxyAdmin.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "./TrustCurve.sol";
import "./ProofAwareExecutorV35.sol";

/**
 * @title SelfAmendingProtocol
 * @notice Governance module that allows the AI to propose and implement upgrades to core contracts
 * @dev Part of the V46 Metamorphic Core architecture
 */
contract SelfAmendingProtocol is AccessControl, ReentrancyGuard {
    using ECDSA for bytes32;

    // Role definitions
    bytes32 public constant GOVERNANCE_ADMIN_ROLE = keccak256("GOVERNANCE_ADMIN_ROLE");
    bytes32 public constant AI_PROPOSER_ROLE = keccak256("AI_PROPOSER_ROLE");
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");

    // Proxy admin for managing upgradeable contracts
    ProxyAdmin public proxyAdmin;

    // Proposal status enum
    enum ProposalStatus {
        Pending,
        Approved,
        Rejected,
        Executed,
        Expired
    }

    // Proposal struct
    struct Proposal {
        uint256 id;
        address targetContract;
        address newImplementation;
        bytes32 worldModelSimulationHash;
        bytes32 ethicalFrameworkHash;
        string metadataURI;
        uint256 proposedAt;
        uint256 votingEndsAt;
        uint256 executionDelay;
        ProposalStatus status;
        uint256 yesVotes;
        uint256 noVotes;
        address proposer;
        mapping(address => bool) hasVoted;
    }

    // Mapping from proposal ID to Proposal
    mapping(uint256 => Proposal) public proposals;
    
    // Counter for proposal IDs
    uint256 public proposalCounter;
    
    // Voting period duration in seconds (default: 3 days)
    uint256 public votingPeriod = 3 days;
    
    // Execution delay after approval in seconds (default: 2 days)
    uint256 public executionDelay = 2 days;
    
    // Minimum quorum percentage required for a proposal to pass (default: 51%)
    uint256 public quorumPercentage = 51;
    
    // Registered contracts that can be upgraded
    mapping(address => bool) public registeredContracts;
    
    // Events
    event ProposalCreated(
        uint256 indexed proposalId,
        address indexed targetContract,
        address indexed newImplementation,
        bytes32 worldModelSimulationHash,
        bytes32 ethicalFrameworkHash,
        string metadataURI,
        uint256 proposedAt,
        uint256 votingEndsAt
    );
    
    event ProposalVoted(
        uint256 indexed proposalId,
        address indexed voter,
        bool support,
        uint256 yesVotes,
        uint256 noVotes
    );
    
    event ProposalStatusChanged(
        uint256 indexed proposalId,
        ProposalStatus status
    );
    
    event ContractUpgraded(
        uint256 indexed proposalId,
        address indexed targetContract,
        address indexed newImplementation,
        uint256 executedAt
    );
    
    event ContractRegistered(
        address indexed contractAddress,
        string contractName,
        address indexed registeredBy
    );
    
    event ContractUnregistered(
        address indexed contractAddress,
        address indexed unregisteredBy
    );
    
    /**
     * @dev Constructor
     * @param _proxyAdmin Address of the ProxyAdmin contract
     */
    constructor(address _proxyAdmin) {
        require(_proxyAdmin != address(0), "Invalid ProxyAdmin address");
        
        proxyAdmin = ProxyAdmin(_proxyAdmin);
        
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), msg.sender);
        _grantRole(GOVERNANCE_ADMIN_ROLE, msg.sender);
    }
    
    /**
     * @dev Register a contract that can be upgraded
     * @param _contractAddress Address of the contract to register
     * @param _contractName Name of the contract
     */
    function registerContract(address _contractAddress, string memory _contractName) external onlyRole(GOVERNANCE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_contractAddress != address(0), "Invalid contract address");
        require(!registeredContracts[_contractAddress], "Contract already registered");
        
        registeredContracts[_contractAddress] = true;
        
        emit ContractRegistered(_contractAddress, _contractName, msg.sender);
    }
    
    /**
     * @dev Unregister a contract
     * @param _contractAddress Address of the contract to unregister
     */
    function unregisterContract(address _contractAddress) external onlyRole(GOVERNANCE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(registeredContracts[_contractAddress], "Contract not registered");
        
        registeredContracts[_contractAddress] = false;
        
        emit ContractUnregistered(_contractAddress, msg.sender);
    }
    
    /**
     * @dev Create a proposal to upgrade a contract
     * @param _targetContract Address of the contract to upgrade
     * @param _newImplementation Address of the new implementation
     * @param _worldModelSimulationHash Hash of the World Model simulation results
     * @param _ethicalFrameworkHash Hash of the ethical framework compliance report
     * @param _metadataURI URI pointing to the proposal metadata
     */
    function createProposal(
        address _targetContract,
        address _newImplementation,
        bytes32 _worldModelSimulationHash,
        bytes32 _ethicalFrameworkHash,
        string memory _metadataURI
    ) external onlyRole(AI_PROPOSER_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(registeredContracts[_targetContract], "Target contract not registered");
        require(_newImplementation != address(0), "Invalid implementation address");
        require(bytes(_metadataURI).length > 0, "Metadata URI cannot be empty");
        
        uint256 proposalId = proposalCounter++;
        
        Proposal storage proposal = proposals[proposalId];
        proposal.id = proposalId;
        proposal.targetContract = _targetContract;
        proposal.newImplementation = _newImplementation;
        proposal.worldModelSimulationHash = _worldModelSimulationHash;
        proposal.ethicalFrameworkHash = _ethicalFrameworkHash;
        proposal.metadataURI = _metadataURI;
        proposal.proposedAt = block.timestamp;
        proposal.votingEndsAt = block.timestamp + votingPeriod;
        proposal.executionDelay = executionDelay;
        proposal.status = ProposalStatus.Pending;
        proposal.proposer = msg.sender;
        
        emit ProposalCreated(
            proposalId,
            _targetContract,
            _newImplementation,
            _worldModelSimulationHash,
            _ethicalFrameworkHash,
            _metadataURI,
            block.timestamp,
            block.timestamp + votingPeriod
        );
    }
    
    /**
     * @dev Vote on a proposal
     * @param _proposalId ID of the proposal
     * @param _support Whether to support the proposal
     */
    function vote(uint256 _proposalId, bool _support) external onlyRole(VALIDATOR_ROLE) nonReentrant {
        Proposal storage proposal = proposals[_proposalId];
        
        require(proposal.status == ProposalStatus.Pending, "Proposal not in voting period");
        require(block.timestamp < proposal.votingEndsAt, "Voting period ended");
        require(!proposal.hasVoted[msg.sender], "Already voted");
        
        proposal.hasVoted[msg.sender] = true;
        
        if (_support) {
            proposal.yesVotes += 1;
        } else {
            proposal.noVotes += 1;
        }
        
        emit ProposalVoted(
            _proposalId,
            msg.sender,
            _support,
            proposal.yesVotes,
            proposal.noVotes
        );
        
        // Check if quorum is reached
        uint256 totalVotes = proposal.yesVotes + proposal.noVotes;
        uint256 totalValidators = getRoleMemberCount(VALIDATOR_ROLE);
        
        if (totalVotes * 100 / totalValidators >= quorumPercentage) {
            if (proposal.yesVotes > proposal.noVotes) {
                proposal.status = ProposalStatus.Approved;
            } else {
                proposal.status = ProposalStatus.Rejected;
            }
            
            emit ProposalStatusChanged(_proposalId, proposal.status);
        }
    }
    
    /**
     * @dev Execute an approved proposal after the execution delay
     * @param _proposalId ID of the proposal
     */
    function executeProposal(uint256 _proposalId) external nonReentrant{
        Proposal storage proposal = proposals[_proposalId];
        
        require(proposal.status == ProposalStatus.Approved, "Proposal not approved");
        require(block.timestamp >= proposal.votingEndsAt + proposal.executionDelay, "Execution delay not passed");
        
        // Upgrade the contract
        proxyAdmin.upgrade(
            TransparentUpgradeableProxy(payable(proposal.targetContract)),
            proposal.newImplementation
        );
        
        proposal.status = ProposalStatus.Executed;
        
        emit ProposalStatusChanged(_proposalId, ProposalStatus.Executed);
        emit ContractUpgraded(
            _proposalId,
            proposal.targetContract,
            proposal.newImplementation,
            block.timestamp
        );
    }
    
    /**
     * @dev Update the voting period
     * @param _newVotingPeriod New voting period in seconds
     */
    function updateVotingPeriod(uint256 _newVotingPeriod) external onlyRole(GOVERNANCE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_newVotingPeriod > 0, "Voting period must be greater than zero");
        votingPeriod = _newVotingPeriod;
    }
    
    /**
     * @dev Update the execution delay
     * @param _newExecutionDelay New execution delay in seconds
     */
    function updateExecutionDelay(uint256 _newExecutionDelay) external onlyRole(GOVERNANCE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_newExecutionDelay > 0, "Execution delay must be greater than zero");
        executionDelay = _newExecutionDelay;
    }
    
    /**
     * @dev Update the quorum percentage
     * @param _newQuorumPercentage New quorum percentage
     */
    function updateQuorumPercentage(uint256 _newQuorumPercentage) external onlyRole(GOVERNANCE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_newQuorumPercentage > 0 && _newQuorumPercentage <= 100, "Quorum percentage must be between 1 and 100");
        quorumPercentage = _newQuorumPercentage;
    }
    
    /**
     * @dev Get the number of members in a role
     * @param _role The role to check
     * @return The number of members in the role
     */
    function getRoleMemberCount(bytes32 _role) public view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return getRoleMemberCount(_role);
    }
    
    /**
     * @dev Check if a proposal exists
     * @param _proposalId ID of the proposal
     * @return Whether the proposal exists
     */
    function proposalExists(uint256 _proposalId) external view returns (bool)  {
        // TODO: Add nonReentrant modifier
        return proposals[_proposalId].proposedAt > 0;
    }
    
    /**
     * @dev Get proposal details
     * @param _proposalId ID of the proposal
     * @return targetContract The target contract address
     * @return newImplementation The new implementation address
     * @return worldModelSimulationHash The hash of the World Model simulation results
     * @return ethicalFrameworkHash The hash of the ethical framework compliance report
     * @return metadataURI The URI pointing to the proposal metadata
     * @return proposedAt The timestamp when the proposal was created
     * @return votingEndsAt The timestamp when voting ends
     * @return status The status of the proposal
     * @return yesVotes The number of yes votes
     * @return noVotes The number of no votes
     */
    function getProposalDetails(uint256 _proposalId) external view returns (
        address targetContract,
        address newImplementation,
        bytes32 worldModelSimulationHash,
        bytes32 ethicalFrameworkHash,
        string memory metadataURI,
        uint256 proposedAt,
        uint256 votingEndsAt,
        ProposalStatus status,
        uint256 yesVotes,
        uint256 noVotes
    ) {
        Proposal storage proposal = proposals[_proposalId];
        
        return (
            proposal.targetContract,
            proposal.newImplementation,
            proposal.worldModelSimulationHash,
            proposal.ethicalFrameworkHash,
            proposal.metadataURI,
            proposal.proposedAt,
            proposal.votingEndsAt,
            proposal.status,
            proposal.yesVotes,
            proposal.noVotes
        );
    }
    
    /**
     * @dev Check if an address has voted on a proposal
     * @param _proposalId ID of the proposal
     * @param _voter Address of the voter
     * @return Whether the address has voted
     */
    function hasVoted(uint256 _proposalId, address _voter) external view returns (bool)  {
        // TODO: Add nonReentrant modifier
        return proposals[_proposalId].hasVoted[_voter];
    }
}
