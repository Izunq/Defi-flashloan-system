// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/Create2.sol";
import "./PreCognitiveOracle.sol";

/**
 * @title EmergentStrategy
 * @notice A modular, dynamically assembled strategy contract
 * @dev Part of the V43 Emergent Strategy Synthesis architecture
 */
contract EmergentStrategy is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;
    
    // Strategy metadata
    string public name;
    string public description;
    address public creator;
    uint256 public creationTime;
    bool public isActive;
    
    // Strategy components
    struct Component {
        address contractAddress;
        string name;
        string componentType;
        bool isActive;
    }
    
    Component[] public components;
    
    // Execution state
    struct ExecutionState {
        uint256 lastExecutionTime;
        uint256 executionCount;
        uint256 successCount;
        int256 totalProfitLoss;
    }
    
    ExecutionState public state;
    
    // Events
    event ComponentAdded(
        address indexed contractAddress,
        string name,
        string componentType,
        uint256 timestamp
    );
    
    event ComponentRemoved(
        address indexed contractAddress,
        string name,
        uint256 timestamp
    );
    
    event StrategyExecuted(
        bool success,
        int256 profitLoss,
        uint256 timestamp
    );
    
    event FundsReceived(
        address indexed sender,
        uint256 amount,
        uint256 timestamp
    );
    
    /**
     * @dev Constructor
     * @param _name Name of the strategy
     * @param _description Description of the strategy
     * @param _creator Address of the creator
     */
    constructor(
        string memory _name,
        string memory _description,
        address _creator
    ) Ownable(_creator) {
        name = _name;
        description = _description;
        creator = _creator;
        creationTime = block.timestamp;
        isActive = true;
    }
    
    /**
     * @dev Add a component to the strategy
     * @param _contractAddress Address of the component contract
     * @param _name Name of the component
     * @param _componentType Type of the component
     */
    function addComponent(
        address _contractAddress,
        string memory _name,
        string memory _componentType
    ) external onlyOwner {
        require(_contractAddress != address(0), "Invalid component address");
        
        components.push(Component({
            contractAddress: _contractAddress,
            name: _name,
            componentType: _componentType,
            isActive: true
        }));
        
        emit ComponentAdded(
            _contractAddress,
            _name,
            _componentType,
            block.timestamp
        );
    }
    
    /**
     * @dev Remove a component from the strategy
     * @param _index Index of the component to remove
     */
    function removeComponent(uint256 _index) external onlyOwner {
        require(_index < components.length, "Invalid component index");
        
        Component storage component = components[_index];
        component.isActive = false;
        
        emit ComponentRemoved(
            component.contractAddress,
            component.name,
            block.timestamp
        );
    }
    
    /**
     * @dev Execute the strategy
     * @return success Whether the execution was successful
     * @return profitLoss Profit or loss from the execution
     */
    function execute() external nonReentrant returns (bool success, int256 profitLoss) {
        require(isActive, "Strategy not active");
        
        // Record initial portfolio value
        uint256 initialValue = getPortfolioValue();
        
        // Execute each component
        bool allSuccess = true;
        for (uint256 i = 0; i < components.length; i++) {
            Component storage component = components[i];
            
            if (!component.isActive) {
                continue;
            }
            
            // Call the component's execute function
            (bool callSuccess, bytes memory result) = component.contractAddress.call(
                abi.encodeWithSignature("execute()")
            );
            
            if (!callSuccess) {
                allSuccess = false;
            }
        }
        
        // Calculate profit/loss
        uint256 finalValue = getPortfolioValue();
        
        if (finalValue > initialValue) {
            profitLoss = int256(finalValue - initialValue);
        } else {
            profitLoss = -int256(initialValue - finalValue);
        }
        
        // Update state
        state.lastExecutionTime = block.timestamp;
        state.executionCount += 1;
        
        if (allSuccess) {
            state.successCount += 1;
        }
        
        state.totalProfitLoss += profitLoss;
        
        // Emit event
        emit StrategyExecuted(
            allSuccess,
            profitLoss,
            block.timestamp
        );
        
        return (allSuccess, profitLoss);
    }
    
    /**
     * @dev Get the portfolio value
     * @return value Total portfolio value
     */
    function getPortfolioValue() public view returns (uint256 value) {
        // In a real implementation, this would calculate the value of all assets
        // For this example, we'll just return the ETH balance
        return address(this).balance;
    }
    
    /**
     * @dev Set the active state of the strategy
     * @param _isActive Whether the strategy is active
     */
    function setActive(bool _isActive) external onlyOwner {
        isActive = _isActive;
    }
    
    /**
     * @dev Get the number of components
     * @return count Number of components
     */
    function getComponentCount() external view returns (uint256 count) {
        return components.length;
    }
    
    /**
     * @dev Get strategy status
     * @return _isActive Whether the strategy is active
     * @return _executionCount Number of executions
     * @return _successCount Number of successful executions
     * @return _totalProfitLoss Total profit or loss
     * @return _lastExecutionTime Timestamp of the last execution
     */
    function getStatus() external view returns (
        bool _isActive,
        uint256 _executionCount,
        uint256 _successCount,
        int256 _totalProfitLoss,
        uint256 _lastExecutionTime
    ) {
        return (
            isActive,
            state.executionCount,
            state.successCount,
            state.totalProfitLoss,
            state.lastExecutionTime
        );
    }
    
    /**
     * @dev Receive ETH
     */
    receive() external payable {
        emit FundsReceived(msg.sender, msg.value, block.timestamp);
    }
    
    /**
     * @dev Rescue ETH from the contract
     * @param _amount Amount to rescue
     * @param _recipient Recipient address
     */
    function rescueETH(uint256 _amount, address payable _recipient) external onlyOwner {
        require(_recipient != address(0), "Invalid recipient address");
        require(_amount <= address(this).balance, "Insufficient balance");
        
        (bool success, ) = _recipient.call{value: _amount}("");
        require(success, "ETH transfer failed");
    }
    
    /**
     * @dev Rescue tokens from the contract
     * @param _tokenAddress Address of the token to rescue
     * @param _amount Amount to rescue
     * @param _recipient Recipient address
     */
    function rescueTokens(
        address _tokenAddress,
        uint256 _amount,
        address _recipient
    ) external onlyOwner {
        require(_tokenAddress != address(0), "Invalid token address");
        require(_recipient != address(0), "Invalid recipient address");
        
        IERC20(_tokenAddress).safeTransfer(_recipient, _amount);
    }
}

/**
 * @title EmergentStrategyFactory
 * @notice Factory contract for creating emergent strategies
 * @dev Part of the V43 Emergent Strategy Synthesis architecture
 */
contract EmergentStrategyFactory is Ownable {
    // Mapping from strategy ID to strategy address
    mapping(uint256 => address) public strategies;
    
    // Counter for strategy IDs
    uint256 public strategyCount;
    
    // Events
    event StrategyCreated(
        uint256 indexed strategyId,
        address indexed strategyAddress,
        string name,
        address creator,
        uint256 timestamp
    );
    
    /**
     * @dev Constructor
     */
    constructor() Ownable(msg.sender) {}
    
    /**
     * @dev Create a new emergent strategy
     * @param _name Name of the strategy
     * @param _description Description of the strategy
     * @param _creator Address of the creator
     * @param _salt Salt for deterministic address generation
     * @return strategyId ID of the created strategy
     * @return strategyAddress Address of the created strategy
     */
    function createStrategy(
        string memory _name,
        string memory _description,
        address _creator,
        bytes32 _salt
    ) external returns (uint256 strategyId, address strategyAddress) {
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(_creator != address(0), "Invalid creator address");
        
        // Create strategy contract
        bytes memory bytecode = abi.encodePacked(
            type(EmergentStrategy).creationCode,
            abi.encode(_name, _description, _creator)
        );
        
        strategyAddress = Create2.deploy(0, _salt, bytecode);
        
        // Increment counter
        strategyCount++;
        strategyId = strategyCount;
        
        // Store strategy
        strategies[strategyId] = strategyAddress;
        
        // Emit event
        emit StrategyCreated(
            strategyId,
            strategyAddress,
            _name,
            _creator,
            block.timestamp
        );
        
        return (strategyId, strategyAddress);
    }
    
    /**
     * @dev Get strategy address by ID
     * @param _strategyId ID of the strategy
     * @return Strategy address
     */
    function getStrategyAddress(uint256 _strategyId) external view returns (address) {
        return strategies[_strategyId];
    }
    
    /**
     * @dev Predict strategy address
     * @param _name Name of the strategy
     * @param _description Description of the strategy
     * @param _creator Address of the creator
     * @param _salt Salt for deterministic address generation
     * @return Predicted strategy address
     */
    function predictStrategyAddress(
        string memory _name,
        string memory _description,
        address _creator,
        bytes32 _salt
    ) external view returns (address) {
        bytes memory bytecode = abi.encodePacked(
            type(EmergentStrategy).creationCode,
            abi.encode(_name, _description, _creator)
        );
        
        return Create2.computeAddress(_salt, keccak256(bytecode));
    }
}

/**
 * @title StrategyComponent
 * @notice Base contract for strategy components
 * @dev Part of the V43 Emergent Strategy Synthesis architecture
 */
abstract contract StrategyComponent {
    address public strategy;
    string public name;
    string public componentType;
    bool public isActive;
    
    /**
     * @dev Constructor
     * @param _strategy Address of the parent strategy
     * @param _name Name of the component
     * @param _componentType Type of the component
     */
    constructor(
        address _strategy,
        string memory _name,
        string memory _componentType
    ) {
        require(_strategy != address(0), "Invalid strategy address");
        
        strategy = _strategy;
        name = _name;
        componentType = _componentType;
        isActive = true;
    }
    
    /**
     * @dev Modifier to restrict access to the parent strategy
     */
    modifier onlyStrategy() {
        require(msg.sender == strategy, "Caller is not the strategy");
        _;
    }
    
    /**
     * @dev Execute the component
     * @return success Whether the execution was successful
     */
    function execute() external virtual onlyStrategy returns (bool success);
}

/**
 * @title SwapComponent
 * @notice Component for swapping assets
 * @dev Part of the V43 Emergent Strategy Synthesis architecture
 */
contract SwapComponent is StrategyComponent {
    using SafeERC20 for IERC20;
    
    address public immutable tokenIn;
    address public immutable tokenOut;
    address public immutable dex;
    uint256 public amountPercentage;
    
    /**
     * @dev Constructor
     * @param _strategy Address of the parent strategy
     * @param _name Name of the component
     * @param _tokenIn Address of the input token
     * @param _tokenOut Address of the output token
     * @param _dex Address of the DEX
     * @param _amountPercentage Percentage of available balance to swap
     */
    constructor(
        address _strategy,
        string memory _name,
        address _tokenIn,
        address _tokenOut,
        address _dex,
        uint256 _amountPercentage
    ) StrategyComponent(_strategy, _name, "swap") {
        require(_tokenIn != address(0), "Invalid tokenIn address");
        require(_tokenOut != address(0), "Invalid tokenOut address");
        require(_dex != address(0), "Invalid DEX address");
        require(_amountPercentage <= 10000, "Percentage cannot exceed 10000 (100%)");
        
        tokenIn = _tokenIn;
        tokenOut = _tokenOut;
        dex = _dex;
        amountPercentage = _amountPercentage;
    }
    
    /**
     * @dev Execute the swap
     * @return success Whether the execution was successful
     */
    function execute() external override onlyStrategy returns (bool success) {
        // Get balance of tokenIn
        uint256 balance = IERC20(tokenIn).balanceOf(strategy);
        
        if (balance == 0) {
            return false;
        }
        
        // Calculate amount to swap
        uint256 amount = (balance * amountPercentage) / 10000;
        
        if (amount == 0) {
            return false;
        }
        
        // Approve DEX to spend tokens
        IERC20(tokenIn).safeApprove(dex, 0);
        IERC20(tokenIn).safeApprove(dex, amount);
        
        // Call swap function on DEX
        // In a real implementation, this would call the specific DEX's swap function
        // For this example, we'll just simulate a successful swap
        
        return true;
    }
    
    /**
     * @dev Update amount percentage
     * @param _amountPercentage New percentage
     */
    function updateAmountPercentage(uint256 _amountPercentage) external onlyStrategy {
        require(_amountPercentage <= 10000, "Percentage cannot exceed 10000 (100%)");
        amountPercentage = _amountPercentage;
    }
}

/**
 * @title LendingComponent
 * @notice Component for interacting with lending protocols
 * @dev Part of the V43 Emergent Strategy Synthesis architecture
 */
contract LendingComponent is StrategyComponent {
    using SafeERC20 for IERC20;
    
    enum ActionType { Deposit, Withdraw, Borrow, Repay }
    
    address public immutable token;
    address public immutable lendingProtocol;
    ActionType public actionType;
    uint256 public amountPercentage;
    
    /**
     * @dev Constructor
     * @param _strategy Address of the parent strategy
     * @param _name Name of the component
     * @param _token Address of the token
     * @param _lendingProtocol Address of the lending protocol
     * @param _actionType Type of lending action
     * @param _amountPercentage Percentage of available balance to use
     */
    constructor(
        address _strategy,
        string memory _name,
        address _token,
        address _lendingProtocol,
        ActionType _actionType,
        uint256 _amountPercentage
    ) StrategyComponent(_strategy, _name, "lending") {
        require(_token != address(0), "Invalid token address");
        require(_lendingProtocol != address(0), "Invalid lending protocol address");
        require(_amountPercentage <= 10000, "Percentage cannot exceed 10000 (100%)");
        
        token = _token;
        lendingProtocol = _lendingProtocol;
        actionType = _actionType;
        amountPercentage = _amountPercentage;
    }
    
    /**
     * @dev Execute the lending action
     * @return success Whether the execution was successful
     */
    function execute() external override onlyStrategy returns (bool success) {
        // Get relevant balance
        uint256 balance;
        
        if (actionType == ActionType.Deposit || actionType == ActionType.Repay) {
            // For deposit/repay, use token balance of strategy
            balance = IERC20(token).balanceOf(strategy);
        } else {
            // For withdraw/borrow, this would check the available amount in the lending protocol
            // For this example, we'll just use a dummy value
            balance = 1000 * 10**18;
        }
        
        if (balance == 0) {
            return false;
        }
        
        // Calculate amount to use
        uint256 amount = (balance * amountPercentage) / 10000;
        
        if (amount == 0) {
            return false;
        }
        
        // Execute action based on type
        if (actionType == ActionType.Deposit) {
            // Approve lending protocol to spend tokens
            IERC20(token).safeApprove(lendingProtocol, 0);
            IERC20(token).safeApprove(lendingProtocol, amount);
            
            // Call deposit function on lending protocol
            // In a real implementation, this would call the specific protocol's function
        } else if (actionType == ActionType.Withdraw) {
            // Call withdraw function on lending protocol
        } else if (actionType == ActionType.Borrow) {
            // Call borrow function on lending protocol
        } else if (actionType == ActionType.Repay) {
            // Approve lending protocol to spend tokens
            IERC20(token).safeApprove(lendingProtocol, 0);
            IERC20(token).safeApprove(lendingProtocol, amount);
            
            // Call repay function on lending protocol
        }
        
        // For this example, we'll just simulate a successful action
        return true;
    }
    
    /**
     * @dev Update amount percentage
     * @param _amountPercentage New percentage
     */
    function updateAmountPercentage(uint256 _amountPercentage) external onlyStrategy {
        require(_amountPercentage <= 10000, "Percentage cannot exceed 10000 (100%)");
        amountPercentage = _amountPercentage;
    }
    
    /**
     * @dev Update action type
     * @param _actionType New action type
     */
    function updateActionType(ActionType _actionType) external onlyStrategy {
        actionType = _actionType;
    }
}

/**
 * @title OracleComponent
 * @notice Component for interacting with the Pre-Cognitive Oracle
 * @dev Part of the V43 Emergent Strategy Synthesis architecture
 */
contract OracleComponent is StrategyComponent {
    PreCognitiveOracle public immutable oracle;
    bytes32 public eventTypeId;
    bytes32 public horizonId;
    uint256 public probabilityThreshold;
    uint256 public confidenceThreshold;
    
    /**
     * @dev Constructor
     * @param _strategy Address of the parent strategy
     * @param _name Name of the component
     * @param _oracle Address of the Pre-Cognitive Oracle
     * @param _eventTypeId ID of the event type to monitor
     * @param _horizonId ID of the time horizon
     * @param _probabilityThreshold Threshold for probability (in basis points)
     * @param _confidenceThreshold Threshold for confidence (in basis points)
     */
    constructor(
        address _strategy,
        string memory _name,
        address _oracle,
        bytes32 _eventTypeId,
        bytes32 _horizonId,
        uint256 _probabilityThreshold,
        uint256 _confidenceThreshold
    ) StrategyComponent(_strategy, _name, "oracle") {
        require(_oracle != address(0), "Invalid oracle address");
        
        oracle = PreCognitiveOracle(_oracle);
        eventTypeId = _eventTypeId;
        horizonId = _horizonId;
        probabilityThreshold = _probabilityThreshold;
        confidenceThreshold = _confidenceThreshold;
    }
    
    /**
     * @dev Execute the oracle check
     * @return success Whether the execution was successful
     */
    function execute() external override onlyStrategy returns (bool success) {
        // Get latest probability from oracle
        (
            bytes32 probabilityId,
            uint256 probability,
            uint256 confidence,
            ,  // timestamp
            // expirationTime
        ) = oracle.getLatestProbability(eventTypeId, horizonId);
        
        if (probabilityId == bytes32(0)) {
            return false;
        }
        
        // Check if probability and confidence exceed thresholds
        return (
            probability >= probabilityThreshold &&
            confidence >= confidenceThreshold
        );
    }
    
    /**
     * @dev Update thresholds
     * @param _probabilityThreshold New probability threshold
     * @param _confidenceThreshold New confidence threshold
     */
    function updateThresholds(
        uint256 _probabilityThreshold,
        uint256 _confidenceThreshold
    ) external onlyStrategy {
        probabilityThreshold = _probabilityThreshold;
        confidenceThreshold = _confidenceThreshold;
    }
    
    /**
     * @dev Update event type and horizon
     * @param _eventTypeId New event type ID
     * @param _horizonId New horizon ID
     */
    function updateEventType(
        bytes32 _eventTypeId,
        bytes32 _horizonId
    ) external onlyStrategy {
        eventTypeId = _eventTypeId;
        horizonId = _horizonId;
    }
}