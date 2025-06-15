// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./TrustCurve.sol";
import "./StrategyIncubatorV33.sol";

/**
 * @title SwarmIntelligenceV38
 * @notice Enables inter-agent communication and strategy composition
 * @dev Part of the V38 Swarm Intelligence architecture
 */
contract SwarmIntelligenceV38 is Ownable, AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;
    
    // Role definitions
    bytes32 public constant AGENT_ROLE = keccak256("AGENT_ROLE");
    bytes32 public constant COMPOSER_ROLE = keccak256("COMPOSER_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");
    
    // Contract references
    TrustCurve public immutable TRUST_CURVE;
    StrategyIncubatorV33 public immutable STRATEGY_INCUBATOR;
    
    // Agent registry
    struct Agent {
        address agentAddress;
        string name;
        string metadata;
        uint256 reputationScore;
        uint256 lastActiveTime;
        bool isActive;
    }
    
    mapping(address => Agent) public agents;
    address[] public agentList;
    
    // Strategy composition
    struct CompositeStrategy {
        uint256 compositeId;
        string name;
        string description;
        address composer;
        uint256[] componentStrategyIds;
        uint256 creationTime;
        bool isActive;
        uint256 executionCount;
        uint256 successCount;
        uint256 totalProfit;
    }
    
    mapping(uint256 => CompositeStrategy) public compositeStrategies;
    uint256 public compositeStrategyCounter;
    
    // Inter-agent communication
    struct Message {
        address sender;
        address recipient;
        bytes32 messageType;
        bytes data;
        uint256 timestamp;
        bool isProcessed;
    }
    
    mapping(bytes32 => Message) public messages;
    mapping(address => bytes32[]) public agentInbox;
    
    // ZK-proof verification
    struct ZKProofVerification {
        bytes32 proofHash;
        address verifier;
        uint256 timestamp;
        bool isValid;
    }
    
    mapping(uint256 => ZKProofVerification[]) public strategyProofs;
    
    // Marketplace
    struct ExecutionRights {
        uint256 strategyId;
        address owner;
        uint256 price;
        uint256 expirationTime;
        bool isForSale;
    }
    
    mapping(uint256 => ExecutionRights) public executionRights;
    
    // Events
    event AgentRegistered(
        address indexed agentAddress,
        string name,
        uint256 timestamp
    );
    
    event AgentUpdated(
        address indexed agentAddress,
        string name,
        bool isActive,
        uint256 timestamp
    );
    
    event MessageSent(
        bytes32 indexed messageId,
        address indexed sender,
        address indexed recipient,
        bytes32 messageType,
        uint256 timestamp
    );
    
    event MessageProcessed(
        bytes32 indexed messageId,
        address indexed processor,
        uint256 timestamp
    );
    
    event CompositeStrategyCreated(
        uint256 indexed compositeId,
        address indexed composer,
        string name,
        uint256[] componentStrategyIds,
        uint256 timestamp
    );
    
    event CompositeStrategyExecuted(
        uint256 indexed compositeId,
        bool success,
        uint256 profit,
        uint256 timestamp
    );
    
    event ZKProofSubmitted(
        uint256 indexed strategyId,
        address indexed verifier,
        bytes32 proofHash,
        bool isValid,
        uint256 timestamp
    );
    
    event ExecutionRightsListed(
        uint256 indexed strategyId,
        address indexed owner,
        uint256 price,
        uint256 expirationTime,
        uint256 timestamp
    );
    
    event ExecutionRightsPurchased(
        uint256 indexed strategyId,
        address indexed previousOwner,
        address indexed newOwner,
        uint256 price,
        uint256 timestamp
    );
    
    /**
     * @dev Constructor
     * @param _trustCurveAddress Address of the TrustCurve contract
     * @param _incubatorAddress Address of the StrategyIncubator contract
     */
    constructor(
        address _trustCurveAddress,
        address _incubatorAddress
    ) Ownable(msg.sender) {
        require(_trustCurveAddress != address(0), "Invalid TrustCurve address");
        require(_incubatorAddress != address(0), "Invalid Incubator address");
        
        TRUST_CURVE = TrustCurve(_trustCurveAddress);
        STRATEGY_INCUBATOR = StrategyIncubatorV33(_incubatorAddress);
        
        // Setup roles
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(AGENT_ROLE, msg.sender);
        _grantRole(COMPOSER_ROLE, msg.sender);
        _grantRole(VERIFIER_ROLE, msg.sender);
        
        // Initialize counters
        compositeStrategyCounter = 0;
    }
    
    /**
     * @dev Register a new agent
     * @param _name Agent name
     * @param _metadata Agent metadata
     */
    function registerAgent(
        string memory _name,
        string memory _metadata
    ) external {
        require(agents[msg.sender].agentAddress == address(0), "Agent already registered");
        require(bytes(_name).length > 0, "Name cannot be empty");
        
        agents[msg.sender] = Agent({
            agentAddress: msg.sender,
            name: _name,
            metadata: _metadata,
            reputationScore: 50, // Initial reputation score (0-100)
            lastActiveTime: block.timestamp,
            isActive: true
        });
        
        agentList.push(msg.sender);
        
        // Grant agent role
        _grantRole(AGENT_ROLE, msg.sender);
        
        emit AgentRegistered(msg.sender, _name, block.timestamp);
    }
    
    /**
     * @dev Update agent information
     * @param _name New agent name
     * @param _metadata New agent metadata
     * @param _isActive Whether the agent is active
     */
    function updateAgent(
        string memory _name,
        string memory _metadata,
        bool _isActive
    ) external onlyRole(AGENT_ROLE) {
        require(agents[msg.sender].agentAddress != address(0), "Agent not registered");
        require(bytes(_name).length > 0, "Name cannot be empty");
        
        Agent storage agent = agents[msg.sender];
        
        agent.name = _name;
        agent.metadata = _metadata;
        agent.isActive = _isActive;
        agent.lastActiveTime = block.timestamp;
        
        emit AgentUpdated(msg.sender, _name, _isActive, block.timestamp);
    }
    
    /**
     * @dev Send a message to another agent
     * @param _recipient Recipient address
     * @param _messageType Type of message
     * @param _data Message data
     * @return messageId ID of the message
     */
    function sendMessage(
        address _recipient,
        bytes32 _messageType,
        bytes memory _data
    ) external onlyRole(AGENT_ROLE) returns (bytes32 messageId) {
        require(_recipient != address(0), "Invalid recipient");
        require(agents[_recipient].agentAddress != address(0), "Recipient not registered");
        require(agents[_recipient].isActive, "Recipient not active");
        
        // Generate message ID
        messageId = keccak256(abi.encodePacked(
            msg.sender,
            _recipient,
            _messageType,
            _data,
            block.timestamp
        ));
        
        // Store message
        messages[messageId] = Message({
            sender: msg.sender,
            recipient: _recipient,
            messageType: _messageType,
            data: _data,
            timestamp: block.timestamp,
            isProcessed: false
        });
        
        // Add to recipient's inbox
        agentInbox[_recipient].push(messageId);
        
        // Update agent's last active time
        agents[msg.sender].lastActiveTime = block.timestamp;
        
        emit MessageSent(messageId, msg.sender, _recipient, _messageType, block.timestamp);
        
        return messageId;
    }
    
    /**
     * @dev Process a message
     * @param _messageId ID of the message to process
     */
    function processMessage(bytes32 _messageId) external onlyRole(AGENT_ROLE) {
        Message storage message = messages[_messageId];
        
        require(message.recipient == msg.sender, "Not the recipient");
        require(!message.isProcessed, "Already processed");
        
        // Mark as processed
        message.isProcessed = true;
        
        // Update agent's last active time
        agents[msg.sender].lastActiveTime = block.timestamp;
        
        emit MessageProcessed(_messageId, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Get messages in an agent's inbox
     * @param _agent Agent address
     * @return messageIds Array of message IDs
     */
    function getAgentInbox(address _agent) external view returns (bytes32[] memory) {
        return agentInbox[_agent];
    }
    
    /**
     * @dev Get message details
     * @param _messageId ID of the message
     * @return sender Sender address
     * @return recipient Recipient address
     * @return messageType Type of message
     * @return data Message data
     * @return timestamp Timestamp of the message
     * @return isProcessed Whether the message has been processed
     */
    function getMessage(bytes32 _messageId) external view returns (
        address sender,
        address recipient,
        bytes32 messageType,
        bytes memory data,
        uint256 timestamp,
        bool isProcessed
    ) {
        Message storage message = messages[_messageId];
        
        return (
            message.sender,
            message.recipient,
            message.messageType,
            message.data,
            message.timestamp,
            message.isProcessed
        );
    }
    
    /**
     * @dev Create a composite strategy
     * @param _name Name of the composite strategy
     * @param _description Description of the composite strategy
     * @param _componentStrategyIds IDs of the component strategies
     * @return compositeId ID of the composite strategy
     */
    function createCompositeStrategy(
        string memory _name,
        string memory _description,
        uint256[] memory _componentStrategyIds
    ) external onlyRole(COMPOSER_ROLE) returns (uint256 compositeId) {
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(_componentStrategyIds.length > 0, "No component strategies");
        require(_componentStrategyIds.length <= 5, "Too many component strategies");
        
        // Verify all component strategies exist
        for (uint i = 0; i < _componentStrategyIds.length; i++) {
            require(
                STRATEGY_INCUBATOR.getStrategy(_componentStrategyIds[i]).strategyAddress != address(0),
                "Component strategy does not exist"
            );
        }
        
        // Increment counter
        compositeStrategyCounter++;
        compositeId = compositeStrategyCounter;
        
        // Create composite strategy
        compositeStrategies[compositeId] = CompositeStrategy({
            compositeId: compositeId,
            name: _name,
            description: _description,
            composer: msg.sender,
            componentStrategyIds: _componentStrategyIds,
            creationTime: block.timestamp,
            isActive: true,
            executionCount: 0,
            successCount: 0,
            totalProfit: 0
        });
        
        // Update agent's last active time
        agents[msg.sender].lastActiveTime = block.timestamp;
        
        emit CompositeStrategyCreated(
            compositeId,
            msg.sender,
            _name,
            _componentStrategyIds,
            block.timestamp
        );
        
        return compositeId;
    }
    
    /**
     * @dev Execute a composite strategy
     * @param _compositeId ID of the composite strategy
     * @param _data Execution data
     * @return success Whether the execution was successful
     * @return profit Profit generated by the execution
     */
    function executeCompositeStrategy(
        uint256 _compositeId,
        bytes memory _data
    ) external onlyRole(AGENT_ROLE) nonReentrant returns (bool success, uint256 profit) {
        CompositeStrategy storage strategy = compositeStrategies[_compositeId];
        
        require(strategy.compositeId == _compositeId, "Composite strategy does not exist");
        require(strategy.isActive, "Composite strategy not active");
        
        // Check if caller has execution rights
        if (executionRights[_compositeId].owner != address(0)) {
            require(
                executionRights[_compositeId].owner == msg.sender,
                "Caller does not have execution rights"
            );
        }
        
        // Execute component strategies
        uint256 totalProfit = 0;
        bool allSuccess = true;
        
        for (uint i = 0; i < strategy.componentStrategyIds.length; i++) {
            uint256 strategyId = strategy.componentStrategyIds[i];
            
            // Get strategy address from incubator
            address strategyAddress = STRATEGY_INCUBATOR.getStrategy(strategyId).strategyAddress;
            
            // Execute strategy (mock implementation)
            // In a real implementation, this would call the strategy's execute function
            
            // Mock execution result
            bool componentSuccess = true;
            uint256 componentProfit = 1 ether / 100; // 0.01 ETH profit
            
            if (!componentSuccess) {
                allSuccess = false;
                break;
            }
            
            totalProfit += componentProfit;
        }
        
        // Update execution statistics
        strategy.executionCount++;
        
        if (allSuccess) {
            strategy.successCount++;
            strategy.totalProfit += totalProfit;
        }
        
        // Update agent's last active time
        agents[msg.sender].lastActiveTime = block.timestamp;
        
        emit CompositeStrategyExecuted(
            _compositeId,
            allSuccess,
            totalProfit,
            block.timestamp
        );
        
        return (allSuccess, totalProfit);
    }
    
    /**
     * @dev Submit a ZK proof for a strategy
     * @param _strategyId ID of the strategy
     * @param _proofHash Hash of the ZK proof
     * @param _isValid Whether the proof is valid
     */
    function submitZKProof(
        uint256 _strategyId,
        bytes32 _proofHash,
        bool _isValid
    ) external onlyRole(VERIFIER_ROLE) {
        require(
            STRATEGY_INCUBATOR.getStrategy(_strategyId).strategyAddress != address(0),
            "Strategy does not exist"
        );
        
        // Add proof verification
        strategyProofs[_strategyId].push(ZKProofVerification({
            proofHash: _proofHash,
            verifier: msg.sender,
            timestamp: block.timestamp,
            isValid: _isValid
        }));
        
        // Update agent's last active time
        agents[msg.sender].lastActiveTime = block.timestamp;
        
        emit ZKProofSubmitted(
            _strategyId,
            msg.sender,
            _proofHash,
            _isValid,
            block.timestamp
        );
    }
    
    /**
     * @dev List execution rights for sale
     * @param _strategyId ID of the strategy
     * @param _price Price in wei
     * @param _duration Duration in seconds
     */
    function listExecutionRights(
        uint256 _strategyId,
        uint256 _price,
        uint256 _duration
    ) external {
        require(
            STRATEGY_INCUBATOR.getStrategy(_strategyId).strategyAddress != address(0),
            "Strategy does not exist"
        );
        
        // Check if caller is the owner of the execution rights
        if (executionRights[_strategyId].owner != address(0)) {
            require(
                executionRights[_strategyId].owner == msg.sender,
                "Caller is not the owner"
            );
        } else {
            // If no owner yet, check if caller is the strategy proposer
            require(
                STRATEGY_INCUBATOR.getStrategy(_strategyId).proposer == msg.sender,
                "Caller is not the proposer"
            );
            
            // Set caller as the owner
            executionRights[_strategyId].owner = msg.sender;
        }
        
        // Update execution rights
        executionRights[_strategyId].strategyId = _strategyId;
        executionRights[_strategyId].price = _price;
        executionRights[_strategyId].expirationTime = block.timestamp + _duration;
        executionRights[_strategyId].isForSale = true;
        
        // Update agent's last active time
        agents[msg.sender].lastActiveTime = block.timestamp;
        
        emit ExecutionRightsListed(
            _strategyId,
            msg.sender,
            _price,
            executionRights[_strategyId].expirationTime,
            block.timestamp
        );
    }
    
    /**
     * @dev Purchase execution rights
     * @param _strategyId ID of the strategy
     */
    function purchaseExecutionRights(
        uint256 _strategyId
    ) external payable nonReentrant {
        ExecutionRights storage rights = executionRights[_strategyId];
        
        require(rights.owner != address(0), "Execution rights not available");
        require(rights.isForSale, "Execution rights not for sale");
        require(block.timestamp <= rights.expirationTime, "Execution rights expired");
        require(msg.value >= rights.price, "Insufficient payment");
        
        // Store previous owner
        address previousOwner = rights.owner;
        
        // Transfer ownership
        rights.owner = msg.sender;
        rights.isForSale = false;
        
        // Transfer payment to previous owner
        (bool sent, ) = previousOwner.call{value: rights.price}("");
        require(sent, "Failed to send payment");
        
        // Refund excess payment
        if (msg.value > rights.price) {
            (bool refunded, ) = msg.sender.call{value: msg.value - rights.price}("");
            require(refunded, "Failed to refund excess payment");
        }
        
        // Update agent's last active time
        agents[msg.sender].lastActiveTime = block.timestamp;
        
        emit ExecutionRightsPurchased(
            _strategyId,
            previousOwner,
            msg.sender,
            rights.price,
            block.timestamp
        );
    }
    
    /**
     * @dev Update agent reputation
     * @param _agent Agent address
     * @param _reputationDelta Change in reputation score (can be positive or negative)
     */
    function updateAgentReputation(
        address _agent,
        int256 _reputationDelta
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(agents[_agent].agentAddress != address(0), "Agent not registered");
        
        Agent storage agent = agents[_agent];
        
        // Update reputation score (bounded between 0 and 100)
        if (_reputationDelta > 0) {
            agent.reputationScore = Math.min(agent.reputationScore + uint256(_reputationDelta), 100);
        } else {
            agent.reputationScore = _reputationDelta * -1 > int256(agent.reputationScore)
                ? 0
                : agent.reputationScore - uint256(-_reputationDelta);
        }
    }
    
    /**
     * @dev Get all registered agents
     * @return agentAddresses Array of agent addresses
     */
    function getAllAgents() external view returns (address[] memory) {
        return agentList;
    }
    
    /**
     * @dev Get agent details
     * @param _agent Agent address
     * @return name Agent name
     * @return metadata Agent metadata
     * @return reputationScore Agent reputation score
     * @return lastActiveTime Last active time
     * @return isActive Whether the agent is active
     */
    function getAgentDetails(address _agent) external view returns (
        string memory name,
        string memory metadata,
        uint256 reputationScore,
        uint256 lastActiveTime,
        bool isActive
    ) {
        Agent storage agent = agents[_agent];
        
        return (
            agent.name,
            agent.metadata,
            agent.reputationScore,
            agent.lastActiveTime,
            agent.isActive
        );
    }
    
    /**
     * @dev Get composite strategy details
     * @param _compositeId ID of the composite strategy
     * @return name Strategy name
     * @return description Strategy description
     * @return composer Composer address
     * @return componentStrategyIds IDs of the component strategies
     * @return creationTime Creation time
     * @return isActive Whether the strategy is active
     * @return executionCount Number of executions
     * @return successCount Number of successful executions
     * @return totalProfit Total profit
     */
    function getCompositeStrategyDetails(uint256 _compositeId) external view returns (
        string memory name,
        string memory description,
        address composer,
        uint256[] memory componentStrategyIds,
        uint256 creationTime,
        bool isActive,
        uint256 executionCount,
        uint256 successCount,
        uint256 totalProfit
    ) {
        CompositeStrategy storage strategy = compositeStrategies[_compositeId];
        
        return (
            strategy.name,
            strategy.description,
            strategy.composer,
            strategy.componentStrategyIds,
            strategy.creationTime,
            strategy.isActive,
            strategy.executionCount,
            strategy.successCount,
            strategy.totalProfit
        );
    }
    
    /**
     * @dev Get ZK proofs for a strategy
     * @param _strategyId ID of the strategy
     * @return proofCount Number of proofs
     */
    function getZKProofCount(uint256 _strategyId) external view returns (uint256) {
        return strategyProofs[_strategyId].length;
    }
    
    /**
     * @dev Get ZK proof details
     * @param _strategyId ID of the strategy
     * @param _index Index of the proof
     * @return proofHash Hash of the ZK proof
     * @return verifier Verifier address
     * @return timestamp Timestamp of the verification
     * @return isValid Whether the proof is valid
     */
    function getZKProofDetails(uint256 _strategyId, uint256 _index) external view returns (
        bytes32 proofHash,
        address verifier,
        uint256 timestamp,
        bool isValid
    ) {
        require(_index < strategyProofs[_strategyId].length, "Invalid index");
        
        ZKProofVerification storage proof = strategyProofs[_strategyId][_index];
        
        return (
            proof.proofHash,
            proof.verifier,
            proof.timestamp,
            proof.isValid
        );
    }
    
    /**
     * @dev Get execution rights details
     * @param _strategyId ID of the strategy
     * @return owner Owner address
     * @return price Price in wei
     * @return expirationTime Expiration time
     * @return isForSale Whether the rights are for sale
     */
    function getExecutionRightsDetails(uint256 _strategyId) external view returns (
        address owner,
        uint256 price,
        uint256 expirationTime,
        bool isForSale
    ) {
        ExecutionRights storage rights = executionRights[_strategyId];
        
        return (
            rights.owner,
            rights.price,
            rights.expirationTime,
            rights.isForSale
        );
    }
}