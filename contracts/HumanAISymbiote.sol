// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "./SelfAmendingProtocol.sol";
import "./ProtocolGenesisEngine.sol";
import "./InterChainCognitiveMesh.sol";
import "./AlgorithmicCentralBank.sol";

/**
 * @title HumanAISymbiote
 * @notice Governance system for the symbiotic relationship between humans and AI
 * @dev Part of the V50 Human-AI Symbiote architecture
 */
contract HumanAISymbiote is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;
    using ECDSA for bytes32;

    // Role definitions
    bytes32 public constant HUMAN_COUNCIL_ROLE = keccak256("HUMAN_COUNCIL_ROLE");
    bytes32 public constant AI_EXECUTIVE_ROLE = keccak256("AI_EXECUTIVE_ROLE");
    bytes32 public constant ETHICS_COMMITTEE_ROLE = keccak256("ETHICS_COMMITTEE_ROLE");
    bytes32 public constant TECHNICAL_COMMITTEE_ROLE = keccak256("TECHNICAL_COMMITTEE_ROLE");

    // Governance token
    IERC20 public governanceToken;

    // Core contracts
    SelfAmendingProtocol public selfAmendingProtocol;
    ProtocolGenesisEngine public protocolGenesisEngine;
    InterChainCognitiveMesh public interChainCognitiveMesh;
    AlgorithmicCentralBank public algorithmicCentralBank;

    // Proposal types
    enum ProposalType {
        EthicalPrinciple,
        SystemUpgrade,
        ResourceAllocation,
        EmergencyAction,
        ProtocolCreation,
        GovernanceChange
    }

    // Proposal status
    enum ProposalStatus {
        Active,
        Approved,
        Rejected,
        Executed,
        Expired
    }

    // Ethical principle
    struct EthicalPrinciple {
        uint256 id;
        string name;
        string description;
        bool isActive;
        uint256 createdAt;
        uint256 lastUpdated;
    }

    // Governance proposal
    struct Proposal {
        uint256 id;
        ProposalType proposalType;
        address proposer;
        string title;
        string description;
        bytes data;
        uint256 createdAt;
        uint256 votingEndsAt;
        ProposalStatus status;
        uint256 humanVotesFor;
        uint256 humanVotesAgainst;
        uint256 aiConfidence;
        bool aiApproval;
        bool ethicsApproval;
        bool technicalApproval;
        mapping(address => bool) hasVoted;
        mapping(address => bool) voteDirection;
    }

    // System metrics
    struct SystemMetrics {
        uint256 totalValueLocked;
        uint256 dailyActiveUsers;
        uint256 protocolCount;
        uint256 transactionCount;
        uint256 averageGasPrice;
        uint256 treasuryBalance;
        uint256 governanceParticipation;
        uint256 lastUpdated;
    }

    // Mappings
    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => EthicalPrinciple) public ethicalPrinciples;
    
    // Counters
    uint256 public proposalCount;
    uint256 public principleCount;
    
    // Configuration
    uint256 public votingPeriod = 7 days;
    uint256 public executionDelay = 2 days;
    uint256 public quorumPercentage = 10;  // 10% of total supply
    uint256 public aiConfidenceThreshold = 80;  // 80% confidence required
    
    // System metrics
    SystemMetrics public systemMetrics;
    
    // Events
    event ProposalCreated(
        uint256 indexed proposalId,
        ProposalType indexed proposalType,
        address indexed proposer,
        string title,
        uint256 votingEndsAt
    );
    
    event VoteCast(
        uint256 indexed proposalId,
        address indexed voter,
        bool support,
        uint256 weight
    );
    
    event AIDecisionMade(
        uint256 indexed proposalId,
        bool approval,
        uint256 confidence
    );
    
    event CommitteeDecisionMade(
        uint256 indexed proposalId,
        bytes32 committeeRole,
        bool approval
    );
    
    event ProposalStatusChanged(
        uint256 indexed proposalId,
        ProposalStatus status
    );
    
    event ProposalExecuted(
        uint256 indexed proposalId,
        address executor
    );
    
    event EthicalPrincipleCreated(
        uint256 indexed principleId,
        string name,
        string description
    );
    
    event EthicalPrincipleUpdated(
        uint256 indexed principleId,
        string name,
        string description,
        bool isActive
    );
    
    event SystemMetricsUpdated(
        uint256 totalValueLocked,
        uint256 dailyActiveUsers,
        uint256 protocolCount,
        uint256 transactionCount
    );
    
    /**
     * @dev Constructor
     * @param _governanceToken Address of the governance token
     * @param _selfAmendingProtocol Address of the SelfAmendingProtocol contract
     * @param _protocolGenesisEngine Address of the ProtocolGenesisEngine contract
     * @param _interChainCognitiveMesh Address of the InterChainCognitiveMesh contract
     * @param _algorithmicCentralBank Address of the AlgorithmicCentralBank contract
     */
    constructor(
        address _governanceToken,
        address _selfAmendingProtocol,
        address _protocolGenesisEngine,
        address _interChainCognitiveMesh,
        address _algorithmicCentralBank
    ) {
        require(_governanceToken != address(0), "Invalid governance token address");
        require(_selfAmendingProtocol != address(0), "Invalid SelfAmendingProtocol address");
        require(_protocolGenesisEngine != address(0), "Invalid ProtocolGenesisEngine address");
        require(_interChainCognitiveMesh != address(0), "Invalid InterChainCognitiveMesh address");
        require(_algorithmicCentralBank != address(0), "Invalid AlgorithmicCentralBank address");
        
        governanceToken = IERC20(_governanceToken);
        selfAmendingProtocol = SelfAmendingProtocol(_selfAmendingProtocol);
        protocolGenesisEngine = ProtocolGenesisEngine(_protocolGenesisEngine);
        interChainCognitiveMesh = InterChainCognitiveMesh(_interChainCognitiveMesh);
        algorithmicCentralBank = AlgorithmicCentralBank(_algorithmicCentralBank);
        
        // Setup roles
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(HUMAN_COUNCIL_ROLE, msg.sender);
        _grantRole(ETHICS_COMMITTEE_ROLE, msg.sender);
        _grantRole(TECHNICAL_COMMITTEE_ROLE, msg.sender);
        
        // Initialize system metrics
        systemMetrics = SystemMetrics({
            totalValueLocked: 0,
            dailyActiveUsers: 0,
            protocolCount: 0,
            transactionCount: 0,
            averageGasPrice: 0,
            treasuryBalance: 0,
            governanceParticipation: 0,
            lastUpdated: block.timestamp
        });
        
        // Create initial ethical principles
        _createInitialEthicalPrinciples();
    }
    
    /**
     * @dev Create initial ethical principles
     */
    function _createInitialEthicalPrinciples() internal {
        _createEthicalPrinciple(
            "Decentralization",
            "The system should maintain and promote decentralization, avoiding single points of failure or control."
        );
        
        _createEthicalPrinciple(
            "Transparency",
            "All system operations should be transparent and verifiable by participants."
        );
        
        _createEthicalPrinciple(
            "Fairness",
            "The system should treat all participants fairly and avoid unfair advantages."
        );
        
        _createEthicalPrinciple(
            "Security",
            "The system should prioritize security and protect user assets."
        );
        
        _createEthicalPrinciple(
            "Privacy",
            "The system should respect user privacy and minimize data collection."
        );
        
        _createEthicalPrinciple(
            "Sustainability",
            "The system should be environmentally and economically sustainable."
        );
        
        _createEthicalPrinciple(
            "Human Oversight",
            "Critical decisions should always have human oversight and approval."
        );
    }
    
    /**
     * @dev Create an ethical principle
     * @param _name Name of the principle
     * @param _description Description of the principle
     */
    function _createEthicalPrinciple(string memory _name, string memory _description) internal {
        uint256 principleId = principleCount++;
        
        ethicalPrinciples[principleId] = EthicalPrinciple({
            id: principleId,
            name: _name,
            description: _description,
            isActive: true,
            createdAt: block.timestamp,
            lastUpdated: block.timestamp
        });
        
        emit EthicalPrincipleCreated(principleId, _name, _description);
    }
    
    /**
     * @dev Create a proposal
     * @param _proposalType Type of the proposal
     * @param _title Title of the proposal
     * @param _description Description of the proposal
     * @param _data Execution data for the proposal
     * @return proposalId ID of the created proposal
     */
    function createProposal(
        ProposalType _proposalType,
        string memory _title,
        string memory _description,
        bytes memory _data
    ) external returns (uint256 proposalId) {
        require(
            hasRole(HUMAN_COUNCIL_ROLE, msg.sender) || hasRole(AI_EXECUTIVE_ROLE, msg.sender),
            "Only Human Council or AI Executive can create proposals"
        );
        
        require(bytes(_title).length > 0, "Title cannot be empty");
        require(bytes(_description).length > 0, "Description cannot be empty");
        
        proposalId = proposalCount++;
        
        Proposal storage proposal = proposals[proposalId];
        proposal.id = proposalId;
        proposal.proposalType = _proposalType;
        proposal.proposer = msg.sender;
        proposal.title = _title;
        proposal.description = _description;
        proposal.data = _data;
        proposal.createdAt = block.timestamp;
        proposal.votingEndsAt = block.timestamp + votingPeriod;
        proposal.status = ProposalStatus.Active;
        
        emit ProposalCreated(
            proposalId,
            _proposalType,
            msg.sender,
            _title,
            proposal.votingEndsAt
        );
        
        return proposalId;
    }
    
    /**
     * @dev Cast a vote on a proposal
     * @param _proposalId ID of the proposal
     * @param _support Whether to support the proposal
     */
    function castVote(uint256 _proposalId, bool _support) external nonReentrant {
        require(hasRole(HUMAN_COUNCIL_ROLE, msg.sender), "Only Human Council members can vote");
        require(_proposalId < proposalCount, "Proposal does not exist");
        
        Proposal storage proposal = proposals[_proposalId];
        
        require(proposal.status == ProposalStatus.Active, "Proposal is not active");
        require(block.timestamp < proposal.votingEndsAt, "Voting period has ended");
        require(!proposal.hasVoted[msg.sender], "Already voted");
        
        // Get voting weight based on governance token balance
        uint256 weight = governanceToken.balanceOf(msg.sender);
        require(weight > 0, "No voting weight");
        
        proposal.hasVoted[msg.sender] = true;
        proposal.voteDirection[msg.sender] = _support;
        
        if (_support) {
            proposal.humanVotesFor += weight;
        } else {
            proposal.humanVotesAgainst += weight;
        }
        
        emit VoteCast(_proposalId, msg.sender, _support, weight);
        
        // Check if quorum is reached
        _checkQuorum(proposal);
    }
    
    /**
     * @dev Record AI decision on a proposal
     * @param _proposalId ID of the proposal
     * @param _approval Whether the AI approves the proposal
     * @param _confidence Confidence level of the AI decision (0-100)
     */
    function recordAIDecision(
        uint256 _proposalId,
        bool _approval,
        uint256 _confidence
    ) external onlyRole(AI_EXECUTIVE_ROLE) {
        require(_proposalId < proposalCount, "Proposal does not exist");
        require(_confidence <= 100, "Confidence must be between 0 and 100");
        
        Proposal storage proposal = proposals[_proposalId];
        
        require(proposal.status == ProposalStatus.Active, "Proposal is not active");
        
        proposal.aiApproval = _approval;
        proposal.aiConfidence = _confidence;
        
        emit AIDecisionMade(_proposalId, _approval, _confidence);
        
        // Check if all approvals are in
        _checkAllApprovals(proposal);
    }
    
    /**
     * @dev Record ethics committee decision on a proposal
     * @param _proposalId ID of the proposal
     * @param _approval Whether the ethics committee approves the proposal
     */
    function recordEthicsDecision(
        uint256 _proposalId,
        bool _approval
    ) external onlyRole(ETHICS_COMMITTEE_ROLE) {
        require(_proposalId < proposalCount, "Proposal does not exist");
        
        Proposal storage proposal = proposals[_proposalId];
        
        require(proposal.status == ProposalStatus.Active, "Proposal is not active");
        
        proposal.ethicsApproval = _approval;
        
        emit CommitteeDecisionMade(_proposalId, ETHICS_COMMITTEE_ROLE, _approval);
        
        // Check if all approvals are in
        _checkAllApprovals(proposal);
    }
    
    /**
     * @dev Record technical committee decision on a proposal
     * @param _proposalId ID of the proposal
     * @param _approval Whether the technical committee approves the proposal
     */
    function recordTechnicalDecision(
        uint256 _proposalId,
        bool _approval
    ) external onlyRole(TECHNICAL_COMMITTEE_ROLE) {
        require(_proposalId < proposalCount, "Proposal does not exist");
        
        Proposal storage proposal = proposals[_proposalId];
        
        require(proposal.status == ProposalStatus.Active, "Proposal is not active");
        
        proposal.technicalApproval = _approval;
        
        emit CommitteeDecisionMade(_proposalId, TECHNICAL_COMMITTEE_ROLE, _approval);
        
        // Check if all approvals are in
        _checkAllApprovals(proposal);
    }
    
    /**
     * @dev Check if quorum is reached
     * @param proposal The proposal to check
     */
    function _checkQuorum(Proposal storage proposal) internal {
        uint256 totalVotes = proposal.humanVotesFor + proposal.humanVotesAgainst;
        uint256 totalSupply = governanceToken.totalSupply();
        
        // Check if quorum is reached
        if (totalVotes * 100 / totalSupply >= quorumPercentage) {
            // Human voting has reached quorum
            // Final decision will be made when all approvals are in
            _checkAllApprovals(proposal);
        }
    }
    
    /**
     * @dev Check if all required approvals are in
     * @param proposal The proposal to check
     */
    function _checkAllApprovals(Proposal storage proposal) internal {
        // Check if human voting has reached quorum
        uint256 totalVotes = proposal.humanVotesFor + proposal.humanVotesAgainst;
        uint256 totalSupply = governanceToken.totalSupply();
        
        bool humanQuorumReached = totalVotes * 100 / totalSupply >= quorumPercentage;
        
        // For ethical principles, ethics committee approval is required
        bool ethicsRequired = proposal.proposalType == ProposalType.EthicalPrinciple;
        
        // For system upgrades and protocol creation, technical committee approval is required
        bool technicalRequired = 
            proposal.proposalType == ProposalType.SystemUpgrade || 
            proposal.proposalType == ProposalType.ProtocolCreation;
        
        // For emergency actions, both ethics and technical approval are required
        bool emergencyAction = proposal.proposalType == ProposalType.EmergencyAction;
        
        // Check if all required approvals are in
        bool allApprovalsIn = 
            humanQuorumReached && 
            (proposal.aiConfidence > 0) &&
            (!ethicsRequired || proposal.ethicsApproval) &&
            (!technicalRequired || proposal.technicalApproval) &&
            (!emergencyAction || (proposal.ethicsApproval && proposal.technicalApproval));
        
        if (allApprovalsIn) {
            // Determine if proposal is approved
            bool humanApproval = proposal.humanVotesFor > proposal.humanVotesAgainst;
            bool aiApprovalValid = proposal.aiConfidence >= aiConfidenceThreshold;
            
            bool approved = 
                humanApproval && 
                (aiApprovalValid ? proposal.aiApproval : true) &&
                (!ethicsRequired || proposal.ethicsApproval) &&
                (!technicalRequired || proposal.technicalApproval) &&
                (!emergencyAction || (proposal.ethicsApproval && proposal.technicalApproval));
            
            // Update proposal status
            proposal.status = approved ? ProposalStatus.Approved : ProposalStatus.Rejected;
            
            emit ProposalStatusChanged(proposal.id, proposal.status);
        }
    }
    
    /**
     * @dev Execute an approved proposal
     * @param _proposalId ID of the proposal
     */
    function executeProposal(uint256 _proposalId) external nonReentrant {
        require(_proposalId < proposalCount, "Proposal does not exist");
        
        Proposal storage proposal = proposals[_proposalId];
        
        require(proposal.status == ProposalStatus.Approved, "Proposal is not approved");
        require(
            block.timestamp >= proposal.votingEndsAt + executionDelay,
            "Execution delay not passed"
        );
        
        // Execute the proposal based on its type
        bool success = _executeProposalByType(proposal);
        
        if (success) {
            proposal.status = ProposalStatus.Executed;
            emit ProposalStatusChanged(proposal.id, ProposalStatus.Executed);
            emit ProposalExecuted(proposal.id, msg.sender);
        } else {
            proposal.status = ProposalStatus.Rejected;
            emit ProposalStatusChanged(proposal.id, ProposalStatus.Rejected);
        }
    }
    
    /**
     * @dev Execute a proposal based on its type
     * @param proposal The proposal to execute
     * @return success Whether the execution was successful
     */
    function _executeProposalByType(Proposal storage proposal) internal returns (bool) {
        if (proposal.proposalType == ProposalType.EthicalPrinciple) {
            return _executeEthicalPrinciple(proposal);
        } else if (proposal.proposalType == ProposalType.SystemUpgrade) {
            return _executeSystemUpgrade(proposal);
        } else if (proposal.proposalType == ProposalType.ResourceAllocation) {
            return _executeResourceAllocation(proposal);
        } else if (proposal.proposalType == ProposalType.EmergencyAction) {
            return _executeEmergencyAction(proposal);
        } else if (proposal.proposalType == ProposalType.ProtocolCreation) {
            return _executeProtocolCreation(proposal);
        } else if (proposal.proposalType == ProposalType.GovernanceChange) {
            return _executeGovernanceChange(proposal);
        }
        
        return false;
    }
    
    /**
     * @dev Execute an ethical principle proposal
     * @param proposal The proposal to execute
     * @return success Whether the execution was successful
     */
    function _executeEthicalPrinciple(Proposal storage proposal) internal returns (bool) {
        // Decode proposal data
        (
            string memory name,
            string memory description,
            bool isUpdate,
            uint256 principleId,
            bool isActive
        ) = abi.decode(proposal.data, (string, string, bool, uint256, bool));
        
        if (isUpdate) {
            // Update existing principle
            require(principleId < principleCount, "Principle does not exist");
            
            EthicalPrinciple storage principle = ethicalPrinciples[principleId];
            principle.name = name;
            principle.description = description;
            principle.isActive = isActive;
            principle.lastUpdated = block.timestamp;
            
            emit EthicalPrincipleUpdated(principleId, name, description, isActive);
        } else {
            // Create new principle
            _createEthicalPrinciple(name, description);
        }
        
        return true;
    }
    
    /**
     * @dev Execute a system upgrade proposal
     * @param proposal The proposal to execute
     * @return success Whether the execution was successful
     */
    function _executeSystemUpgrade(Proposal storage proposal) internal returns (bool) {
        // Decode proposal data
        (
            address targetContract,
            address newImplementation,
            bytes32 worldModelSimulationHash,
            bytes32 ethicalFrameworkHash,
            string memory metadataURI
        ) = abi.decode(proposal.data, (address, address, bytes32, bytes32, string));
        
        // Create proposal in SelfAmendingProtocol
        try selfAmendingProtocol.createProposal(
            targetContract,
            newImplementation,
            worldModelSimulationHash,
            ethicalFrameworkHash,
            metadataURI
        ) {
            return true;
        } catch {
            return false;
        }
    }
    
    /**
     * @dev Execute a resource allocation proposal
     * @param proposal The proposal to execute
     * @return success Whether the execution was successful
     */
    function _executeResourceAllocation(Proposal storage proposal) internal returns (bool) {
        // Decode proposal data
        (
            address recipient,
            uint256 amount,
            string memory reason
        ) = abi.decode(proposal.data, (address, uint256, string));
        
        // Transfer tokens from treasury
        try governanceToken.transfer(recipient, amount) {
            return true;
        } catch {
            return false;
        }
    }
    
    /**
     * @dev Execute an emergency action proposal
     * @param proposal The proposal to execute
     * @return success Whether the execution was successful
     */
    function _executeEmergencyAction(Proposal storage proposal) internal returns (bool) {
        // Decode proposal data
        (
            address targetContract,
            bytes memory callData
        ) = abi.decode(proposal.data, (address, bytes));
        
        // Execute the emergency action
        (bool success, ) = targetContract.call(callData);
        return success;
    }
    
    /**
     * @dev Execute a protocol creation proposal
     * @param proposal The proposal to execute
     * @return success Whether the execution was successful
     */
    function _executeProtocolCreation(Proposal storage proposal) internal returns (bool) {
        // Decode proposal data
        (
            uint256 templateId,
            string memory name,
            string memory description,
            uint256 treasuryAllocationPercentage,
            bytes memory initData
        ) = abi.decode(proposal.data, (uint256, string, string, uint256, bytes));
        
        // Create protocol using ProtocolGenesisEngine
        try protocolGenesisEngine.createProtocol(
            templateId,
            name,
            description,
            treasuryAllocationPercentage,
            initData
        ) returns (uint256) {
            return true;
        } catch {
            return false;
        }
    }
    
    /**
     * @dev Execute a governance change proposal
     * @param proposal The proposal to execute
     * @return success Whether the execution was successful
     */
    function _executeGovernanceChange(Proposal storage proposal) internal returns (bool) {
        // Decode proposal data
        (
            uint256 newVotingPeriod,
            uint256 newExecutionDelay,
            uint256 newQuorumPercentage,
            uint256 newAIConfidenceThreshold
        ) = abi.decode(proposal.data, (uint256, uint256, uint256, uint256));
        
        // Update governance parameters
        if (newVotingPeriod > 0) {
            votingPeriod = newVotingPeriod;
        }
        
        if (newExecutionDelay > 0) {
            executionDelay = newExecutionDelay;
        }
        
        if (newQuorumPercentage > 0 && newQuorumPercentage <= 100) {
            quorumPercentage = newQuorumPercentage;
        }
        
        if (newAIConfidenceThreshold > 0 && newAIConfidenceThreshold <= 100) {
            aiConfidenceThreshold = newAIConfidenceThreshold;
        }
        
        return true;
    }
    
    /**
     * @dev Update system metrics
     * @param _totalValueLocked Total value locked in the system
     * @param _dailyActiveUsers Daily active users
     * @param _protocolCount Number of protocols
     * @param _transactionCount Number of transactions
     * @param _averageGasPrice Average gas price
     * @param _treasuryBalance Treasury balance
     * @param _governanceParticipation Governance participation percentage
     */
    function updateSystemMetrics(
        uint256 _totalValueLocked,
        uint256 _dailyActiveUsers,
        uint256 _protocolCount,
        uint256 _transactionCount,
        uint256 _averageGasPrice,
        uint256 _treasuryBalance,
        uint256 _governanceParticipation
    ) external onlyRole(AI_EXECUTIVE_ROLE) {
        systemMetrics.totalValueLocked = _totalValueLocked;
        systemMetrics.dailyActiveUsers = _dailyActiveUsers;
        systemMetrics.protocolCount = _protocolCount;
        systemMetrics.transactionCount = _transactionCount;
        systemMetrics.averageGasPrice = _averageGasPrice;
        systemMetrics.treasuryBalance = _treasuryBalance;
        systemMetrics.governanceParticipation = _governanceParticipation;
        systemMetrics.lastUpdated = block.timestamp;
        
        emit SystemMetricsUpdated(
            _totalValueLocked,
            _dailyActiveUsers,
            _protocolCount,
            _transactionCount
        );
    }
    
    /**
     * @dev Create an ethical principle proposal
     * @param _name Name of the principle
     * @param _description Description of the principle
     * @param _isUpdate Whether this is an update to an existing principle
     * @param _principleId ID of the principle to update (if isUpdate is true)
     * @param _isActive Whether the principle is active (if isUpdate is true)
     * @return proposalId ID of the created proposal
     */
    function createEthicalPrincipleProposal(
        string memory _name,
        string memory _description,
        bool _isUpdate,
        uint256 _principleId,
        bool _isActive
    ) external returns (uint256) {
        bytes memory data = abi.encode(_name, _description, _isUpdate, _principleId, _isActive);
        
        return createProposal(
            ProposalType.EthicalPrinciple,
            _isUpdate ? "Update Ethical Principle" : "New Ethical Principle",
            _isUpdate ? 
                string(abi.encodePacked("Update principle: ", _name)) : 
                string(abi.encodePacked("New principle: ", _name)),
            data
        );
    }
    
    /**
     * @dev Create a system upgrade proposal
     * @param _targetContract Address of the contract to upgrade
     * @param _newImplementation Address of the new implementation
     * @param _worldModelSimulationHash Hash of the World Model simulation results
     * @param _ethicalFrameworkHash Hash of the ethical framework compliance report
     * @param _metadataURI URI pointing to the proposal metadata
     * @return proposalId ID of the created proposal
     */
    function createSystemUpgradeProposal(
        address _targetContract,
        address _newImplementation,
        bytes32 _worldModelSimulationHash,
        bytes32 _ethicalFrameworkHash,
        string memory _metadataURI
    ) external returns (uint256) {
        bytes memory data = abi.encode(
            _targetContract,
            _newImplementation,
            _worldModelSimulationHash,
            _ethicalFrameworkHash,
            _metadataURI
        );
        
        return createProposal(
            ProposalType.SystemUpgrade,
            "System Upgrade",
            string(abi.encodePacked("Upgrade contract at ", _addressToString(_targetContract))),
            data
        );
    }
    
    /**
     * @dev Create a resource allocation proposal
     * @param _recipient Address of the recipient
     * @param _amount Amount of tokens to allocate
     * @param _reason Reason for the allocation
     * @return proposalId ID of the created proposal
     */
    function createResourceAllocationProposal(
        address _recipient,
        uint256 _amount,
        string memory _reason
    ) external returns (uint256) {
        bytes memory data = abi.encode(_recipient, _amount, _reason);
        
        return createProposal(
            ProposalType.ResourceAllocation,
            "Resource Allocation",
            string(abi.encodePacked("Allocate ", _uintToString(_amount), " tokens to ", _addressToString(_recipient))),
            data
        );
    }
    
    /**
     * @dev Create a protocol creation proposal
     * @param _templateId ID of the template to use
     * @param _name Name of the protocol
     * @param _description Description of the protocol
     * @param _treasuryAllocationPercentage Percentage of treasury to allocate (in basis points)
     * @param _initData Initialization data for the protocol
     * @return proposalId ID of the created proposal
     */
    function createProtocolCreationProposal(
        uint256 _templateId,
        string memory _name,
        string memory _description,
        uint256 _treasuryAllocationPercentage,
        bytes memory _initData
    ) external returns (uint256) {
        bytes memory data = abi.encode(
            _templateId,
            _name,
            _description,
            _treasuryAllocationPercentage,
            _initData
        );
        
        return createProposal(
            ProposalType.ProtocolCreation,
            "Protocol Creation",
            string(abi.encodePacked("Create new protocol: ", _name)),
            data
        );
    }
    
    /**
     * @dev Create a governance change proposal
     * @param _newVotingPeriod New voting period
     * @param _newExecutionDelay New execution delay
     * @param _newQuorumPercentage New quorum percentage
     * @param _newAIConfidenceThreshold New AI confidence threshold
     * @return proposalId ID of the created proposal
     */
    function createGovernanceChangeProposal(
        uint256 _newVotingPeriod,
        uint256 _newExecutionDelay,
        uint256 _newQuorumPercentage,
        uint256 _newAIConfidenceThreshold
    ) external returns (uint256) {
        bytes memory data = abi.encode(
            _newVotingPeriod,
            _newExecutionDelay,
            _newQuorumPercentage,
            _newAIConfidenceThreshold
        );
        
        return createProposal(
            ProposalType.GovernanceChange,
            "Governance Change",
            "Update governance parameters",
            data
        );
    }
    
    /**
     * @dev Get proposal details
     * @param _proposalId ID of the proposal
     * @return proposalType Type of the proposal
     * @return proposer Address of the proposer
     * @return title Title of the proposal
     * @return description Description of the proposal
     * @return createdAt Timestamp when the proposal was created
     * @return votingEndsAt Timestamp when voting ends
     * @return status Status of the proposal
     * @return humanVotesFor Number of human votes for the proposal
     * @return humanVotesAgainst Number of human votes against the proposal
     * @return aiConfidence Confidence level of the AI decision
     * @return aiApproval Whether the AI approves the proposal
     * @return ethicsApproval Whether the ethics committee approves the proposal
     * @return technicalApproval Whether the technical committee approves the proposal
     */
    function getProposalDetails(uint256 _proposalId) external view returns (
        ProposalType proposalType,
        address proposer,
        string memory title,
        string memory description,
        uint256 createdAt,
        uint256 votingEndsAt,
        ProposalStatus status,
        uint256 humanVotesFor,
        uint256 humanVotesAgainst,
        uint256 aiConfidence,
        bool aiApproval,
        bool ethicsApproval,
        bool technicalApproval
    ) {
        require(_proposalId < proposalCount, "Proposal does not exist");
        
        Proposal storage proposal = proposals[_proposalId];
        
        return (
            proposal.proposalType,
            proposal.proposer,
            proposal.title,
            proposal.description,
            proposal.createdAt,
            proposal.votingEndsAt,
            proposal.status,
            proposal.humanVotesFor,
            proposal.humanVotesAgainst,
            proposal.aiConfidence,
            proposal.aiApproval,
            proposal.ethicsApproval,
            proposal.technicalApproval
        );
    }
    
    /**
     * @dev Get all ethical principles
     * @return Array of ethical principles
     */
    function getAllEthicalPrinciples() external view returns (EthicalPrinciple[] memory) {
        EthicalPrinciple[] memory result = new EthicalPrinciple[](principleCount);
        
        for (uint256 i = 0; i < principleCount; i++) {
            result[i] = ethicalPrinciples[i];
        }
        
        return result;
    }
    
    /**
     * @dev Get active ethical principles
     * @return Array of active ethical principles
     */
    function getActiveEthicalPrinciples() external view returns (EthicalPrinciple[] memory) {
        uint256 activeCount = 0;
        
        // Count active principles
        for (uint256 i = 0; i < principleCount; i++) {
            if (ethicalPrinciples[i].isActive) {
                activeCount++;
            }
        }
        
        // Create result array
        EthicalPrinciple[] memory result = new EthicalPrinciple[](activeCount);
        uint256 index = 0;
        
        // Fill result array
        for (uint256 i = 0; i < principleCount; i++) {
            if (ethicalPrinciples[i].isActive) {
                result[index++] = ethicalPrinciples[i];
            }
        }
        
        return result;
    }
    
    /**
     * @dev Check if a voter has voted on a proposal
     * @param _proposalId ID of the proposal
     * @param _voter Address of the voter
     * @return hasVoted Whether the voter has voted
     * @return support Whether the voter supported the proposal
     */
    function getVoterStatus(uint256 _proposalId, address _voter) external view returns (bool hasVoted, bool support) {
        require(_proposalId < proposalCount, "Proposal does not exist");
        
        Proposal storage proposal = proposals[_proposalId];
        
        return (proposal.hasVoted[_voter], proposal.voteDirection[_voter]);
    }
    
    /**
     * @dev Convert an address to a string
     * @param _address Address to convert
     * @return String representation of the address
     */
    function _addressToString(address _address) internal pure returns (string memory) {
        bytes32 value = bytes32(uint256(uint160(_address)));
        bytes memory alphabet = "0123456789abcdef";
        
        bytes memory str = new bytes(42);
        str[0] = "0";
        str[1] = "x";
        
        for (uint256 i = 0; i < 20; i++) {
            str[2 + i * 2] = alphabet[uint8(value[i + 12] >> 4)];
            str[3 + i * 2] = alphabet[uint8(value[i + 12] & 0x0f)];
        }
        
        return string(str);
    }
    
    /**
     * @dev Convert a uint to a string
     * @param _value Value to convert
     * @return String representation of the value
     */
    function _uintToString(uint256 _value) internal pure returns (string memory) {
        if (_value == 0) {
            return "0";
        }
        
        uint256 temp = _value;
        uint256 digits;
        
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        
        bytes memory buffer = new bytes(digits);
        
        while (_value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + _value % 10));
            _value /= 10;
        }
        
        return string(buffer);
    }
}