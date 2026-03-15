// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./HalalAssetRegistry.sol";

/**
 * @title StrategyLeasingPlatform
 * @notice Shariah-compliant platform for leasing trading strategies based on Ijara principles
 * @dev Replaces the conventional marketplace with a halal leasing model
 */
contract StrategyLeasingPlatform is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant SHARIAH_COMMITTEE_ROLE = keccak256("SHARIAH_COMMITTEE_ROLE");
    bytes32 public constant STRATEGY_PROVIDER_ROLE = keccak256("STRATEGY_PROVIDER_ROLE");

    // Halal asset registry
    HalalAssetRegistry public immutable HALAL_REGISTRY;

    // Strategy lease structure
    struct StrategyLease {
        address provider;              // Strategy provider
        string name;                   // Strategy name
        string description;            // Strategy description
        uint256 leasePrice;            // Price per lease period
        uint256 leasePeriod;           // Lease period in seconds
        address paymentToken;          // Token used for payment
        bool active;                   // Whether the strategy is active
        uint256 creationTime;          // When the strategy was created
        uint256 lastUpdateTime;        // When the strategy was last updated
        bytes32 shariahApprovalId;     // ID of Shariah approval
        bool shariahApproved;          // Whether the strategy is Shariah-approved
        uint256 performanceScore;      // Performance score (0-10000)
        uint256 profitabilityScore;    // Profitability score (0-10000)
        uint256 riskScore;             // Risk score (0-10000)
        uint256 trustScore;            // Trust score (0-10000)
        uint256 totalLeases;           // Total number of leases
        uint256 totalRevenue;          // Total revenue generated
        uint256 recommendedPrice;      // AI-recommended price
    }

    // Lease agreement structure
    struct LeaseAgreement {
        bytes32 strategyId;            // ID of the strategy
        address lessee;                // Address of the lessee
        uint256 startTime;             // Start time of the lease
        uint256 endTime;               // End time of the lease
        uint256 price;                 // Price paid for the lease
        bool active;                   // Whether the lease is active
        bool terminated;               // Whether the lease was terminated early
    }

    // Strategy data
    mapping(bytes32 => StrategyLease) public strategies;
    bytes32[] public strategyIds;

    // Lease agreements
    mapping(bytes32 => LeaseAgreement[]) public leaseAgreements;
    mapping(address => bytes32[]) public lesseeStrategies;

    // Provider statistics
    mapping(address => uint256) public providerEarnings;
    mapping(address => uint256) public providerStrategyCount;

    // Platform fee
    uint256 public platformFeeBps = 500; // 5% fee
    address public feeTreasury;
    
    // Strategy analytics
    struct StrategyAnalytics {
        uint256 historicalProfitUSD;    // Historical profit in USD
        uint256 averageROI;             // Average ROI in basis points
        uint256 executionCount;         // Number of executions
        uint256 successRate;            // Success rate in basis points
        uint256 averageExecutionTime;   // Average execution time in seconds
        uint256 lastExecutionTime;      // Last execution timestamp
        uint256 volatility;             // Profit volatility in basis points
        uint256 sharpeRatio;            // Sharpe ratio in basis points
        uint256 maxDrawdown;            // Maximum drawdown in basis points
    }
    
    // Strategy analytics mapping
    mapping(bytes32 => StrategyAnalytics) public strategyAnalytics;

    // Events
    event StrategyRegistered(
        bytes32 indexed strategyId,
        address indexed provider,
        string name,
        uint256 leasePrice,
        uint256 leasePeriod,
        address paymentToken
    );

    event StrategyUpdated(
        bytes32 indexed strategyId,
        uint256 leasePrice,
        uint256 leasePeriod,
        bool active
    );

    event StrategyApproved(
        bytes32 indexed strategyId,
        address indexed approver,
        bytes32 approvalId
    );

    event StrategyRejected(
        bytes32 indexed strategyId,
        address indexed rejector,
        string reason
    );

    event LeaseCreated(
        bytes32 indexed strategyId,
        address indexed lessee,
        uint256 startTime,
        uint256 endTime,
        uint256 price
    );

    event LeaseTerminated(
        bytes32 indexed strategyId,
        address indexed lessee,
        uint256 terminationTime,
        string reason
    );

    event PlatformFeeUpdated(
        uint256 previousFee,
        uint256 newFee
    );

    event FeeTreasuryUpdated(
        address previousTreasury,
        address newTreasury
    );
    
    // V52 Analytics Events
    event StrategyAnalyticsUpdated(
        bytes32 indexed strategyId,
        uint256 historicalProfitUSD,
        uint256 successRate,
        uint256 sharpeRatio
    );
    
    event StrategyScoresUpdated(
        bytes32 indexed strategyId,
        uint256 performanceScore,
        uint256 profitabilityScore,
        uint256 riskScore,
        uint256 trustScore
    );
    
    event PriceRecommendationUpdated(
        bytes32 indexed strategyId,
        uint256 currentPrice,
        uint256 recommendedPrice,
        uint256 timestamp
    );
    
    event MarketAnalysisGenerated(
        uint256 totalStrategies,
        uint256 averagePrice,
        uint256 medianPrice,
        uint256 timestamp
    );

    /**
     * @dev Modifier to ensure only halal-compliant assets are used
     */
    modifier onlyHalalAsset(address token) {
        require(HALAL_REGISTRY.isHalalCompliant(token), "Asset not Shariah-compliant");
        _;
    }

    /**
     * @dev Constructor
     * @param _halalRegistry Address of the HalalAssetRegistry contract
     * @param _feeTreasury Address of the treasury to collect platform fees
     * @param _admin Address of the admin
     * @param _shariahCommittee Address of the initial Shariah committee member
     */
    constructor(
        address _halalRegistry,
        address _feeTreasury,
        address _admin,
        address _shariahCommittee
    ) {
        require(_halalRegistry != address(0), "Invalid registry address");
        require(_feeTreasury != address(0), "Invalid treasury address");
        require(_admin != address(0), "Invalid admin address");
        require(_shariahCommittee != address(0), "Invalid committee address");
        
        HALAL_REGISTRY = HalalAssetRegistry(_halalRegistry);
        feeTreasury = _feeTreasury;
        
        _setupRole(DEFAULT_ADMIN_ROLE, _admin);
        _setupRole(ADMIN_ROLE, _admin);
        _setupRole(SHARIAH_COMMITTEE_ROLE, _shariahCommittee);
    }

    /**
     * @dev Register a new strategy for leasing
     * @param _name Strategy name
     * @param _description Strategy description
     * @param _leasePrice Price per lease period
     * @param _leasePeriod Lease period in seconds
     * @param _paymentToken Token used for payment
     * @return strategyId The ID of the registered strategy
     */
    function registerStrategy(
        string calldata _name,
        string calldata _description,
        uint256 _leasePrice,
        uint256 _leasePeriod,
        address _paymentToken
    ) external nonReentrant whenNotPaused onlyHalalAsset(_paymentToken) returns (bytes32)  {
        // TODO: Add nonReentrant modifier
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_description).length > 0, "Description cannot be empty");
        require(_leasePrice > 0, "Lease price must be greater than 0");
        require(_leasePeriod > 0, "Lease period must be greater than 0");
        
        // Generate strategy ID
        bytes32 strategyId = keccak256(abi.encodePacked(
            msg.sender,
            _name,
            block.timestamp
        ));
        
        // Ensure strategy ID is unique
        require(strategies[strategyId].provider == address(0), "Strategy ID already exists");
        
        // Create strategy
        strategies[strategyId] = StrategyLease({
            provider: msg.sender,
            name: _name,
            description: _description,
            leasePrice: _leasePrice,
            leasePeriod: _leasePeriod,
            paymentToken: _paymentToken,
            active: false, // Inactive until Shariah-approved
            creationTime: block.timestamp,
            lastUpdateTime: block.timestamp,
            shariahApprovalId: bytes32(0),
            shariahApproved: false
        });
        
        // Add to strategy IDs
        strategyIds.push(strategyId);
        
        // Update provider statistics
        providerStrategyCount[msg.sender]++;
        
        // Grant strategy provider role if not already granted
        if (!hasRole(STRATEGY_PROVIDER_ROLE, msg.sender)) {
            grantRole(STRATEGY_PROVIDER_ROLE, msg.sender);
        }
        
        emit StrategyRegistered(
            strategyId,
            msg.sender,
            _name,
            _leasePrice,
            _leasePeriod,
            _paymentToken
        );
        
        return strategyId;
    }

    /**
     * @dev Update an existing strategy
     * @param _strategyId ID of the strategy to update
     * @param _leasePrice New lease price
     * @param _leasePeriod New lease period
     * @param _active Whether the strategy is active
     */
    function updateStrategy(
        bytes32 _strategyId,
        uint256 _leasePrice,
        uint256 _leasePeriod,
        bool _active
    ) external nonReentrant whenNotPaused nonReentrant{
        StrategyLease storage strategy = strategies[_strategyId];
        
        require(strategy.provider == msg.sender, "Not strategy provider");
        require(_leasePrice > 0, "Lease price must be greater than 0");
        require(_leasePeriod > 0, "Lease period must be greater than 0");
        
        // Update strategy
        strategy.leasePrice = _leasePrice;
        strategy.leasePeriod = _leasePeriod;
        strategy.active = _active && strategy.shariahApproved; // Can only be active if Shariah-approved
        strategy.lastUpdateTime = block.timestamp;
        
        emit StrategyUpdated(
            _strategyId,
            _leasePrice,
            _leasePeriod,
            strategy.active
        );
    }

    /**
     * @dev Approve a strategy as Shariah-compliant
     * @param _strategyId ID of the strategy to approve
     * @param _approvalId ID of the approval
     */
    function approveStrategy(
        bytes32 _strategyId,
        bytes32 _approvalId
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE)  {
        // TODO: Add nonReentrant modifier
        StrategyLease storage strategy = strategies[_strategyId];
        
        require(strategy.provider != address(0), "Strategy does not exist");
        require(!strategy.shariahApproved, "Strategy already approved");
        
        // Approve strategy
        strategy.shariahApproved = true;
        strategy.shariahApprovalId = _approvalId;
        strategy.lastUpdateTime = block.timestamp;
        
        // Strategy can now be active if provider set it as active
        if (strategy.active) {
            strategy.active = true;
        }
        
        emit StrategyApproved(
            _strategyId,
            msg.sender,
            _approvalId
        );
    }

    /**
     * @dev Reject a strategy as non-Shariah-compliant
     * @param _strategyId ID of the strategy to reject
     * @param _reason Reason for rejection
     */
    function rejectStrategy(
        bytes32 _strategyId,
        string calldata _reason
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE)  {
        // TODO: Add nonReentrant modifier
        StrategyLease storage strategy = strategies[_strategyId];
        
        require(strategy.provider != address(0), "Strategy does not exist");
        
        // Reject strategy
        strategy.shariahApproved = false;
        strategy.active = false;
        strategy.lastUpdateTime = block.timestamp;
        
        emit StrategyRejected(
            _strategyId,
            msg.sender,
            _reason
        );
    }

    /**
     * @dev Lease a strategy
     * @param _strategyId ID of the strategy to lease
     */
    function leaseStrategy(
        bytes32 _strategyId
    ) external nonReentrant whenNotPaused nonReentrant{
        StrategyLease storage strategy = strategies[_strategyId];
        
        require(strategy.provider != address(0), "Strategy does not exist");
        require(strategy.active, "Strategy not active");
        require(strategy.shariahApproved, "Strategy not Shariah-approved");
        
        // Check if lessee already has an active lease for this strategy
        LeaseAgreement[] storage agreements = leaseAgreements[_strategyId];
        for (uint256 i = 0; i < agreements.length; i++) {
            if (agreements[i].lessee == msg.sender && agreements[i].active) {
                revert("Already leasing this strategy");
            }
        }
        
        // Calculate lease price with platform fee
        uint256 platformFee = (strategy.leasePrice * platformFeeBps) / 10000;
        uint256 providerPayment = strategy.leasePrice - platformFee;
        
        // Transfer payment
        IERC20(strategy.paymentToken).safeTransferFrom(
            msg.sender,
            address(this),
            strategy.leasePrice
        );
        
        // Pay provider
        IERC20(strategy.paymentToken).safeTransfer(
            strategy.provider,
            providerPayment
        );
        
        // Pay platform fee
        IERC20(strategy.paymentToken).safeTransfer(
            feeTreasury,
            platformFee
        );
        
        // Create lease agreement
        uint256 startTime = block.timestamp;
        uint256 endTime = startTime + strategy.leasePeriod;
        
        LeaseAgreement memory agreement = LeaseAgreement({
            strategyId: _strategyId,
            lessee: msg.sender,
            startTime: startTime,
            endTime: endTime,
            price: strategy.leasePrice,
            active: true,
            terminated: false
        });
        
        // Add agreement to storage
        leaseAgreements[_strategyId].push(agreement);
        lesseeStrategies[msg.sender].push(_strategyId);
        
        // Update provider earnings
        providerEarnings[strategy.provider] += providerPayment;
        
        emit LeaseCreated(
            _strategyId,
            msg.sender,
            startTime,
            endTime,
            strategy.leasePrice
        );
    }

    /**
     * @dev Terminate a lease agreement early
     * @param _strategyId ID of the strategy
     * @param _reason Reason for termination
     */
    function terminateLease(
        bytes32 _strategyId,
        string calldata _reason
    ) external nonReentrant{
        LeaseAgreement[] storage agreements = leaseAgreements[_strategyId];
        
        // Find the active lease agreement for the caller
        bool found = false;
        for (uint256 i = 0; i < agreements.length; i++) {
            if (agreements[i].lessee == msg.sender && agreements[i].active) {
                // Terminate the lease
                agreements[i].active = false;
                agreements[i].terminated = true;
                
                found = true;
                
                emit LeaseTerminated(
                    _strategyId,
                    msg.sender,
                    block.timestamp,
                    _reason
                );
                
                break;
            }
        }
        
        require(found, "No active lease found");
    }

    /**
     * @dev Check if a user has an active lease for a strategy
     * @param _strategyId ID of the strategy
     * @param _lessee Address of the lessee
     * @return Whether the lessee has an active lease
     */
    function hasActiveLease(
        bytes32 _strategyId,
        address _lessee
    ) external view returns (bool)  {
        // TODO: Add nonReentrant modifier
        LeaseAgreement[] storage agreements = leaseAgreements[_strategyId];
        
        for (uint256 i = 0; i < agreements.length; i++) {
            if (agreements[i].lessee == _lessee && agreements[i].active) {
                // Check if lease is still valid (not expired)
                if (block.timestamp <= agreements[i].endTime) {
                    return true;
                }
            }
        }
        
        return false;
    }

    /**
     * @dev Get all strategies
     * @return Array of strategy IDs
     */
    function getAllStrategies() external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return strategyIds;
    }

    /**
     * @dev Get active strategies
     * @return Array of active strategy IDs
     */
    function getActiveStrategies() external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        uint256 activeCount = 0;
        
        // Count active strategies
        for (uint256 i = 0; i < strategyIds.length; i++) {
            if (strategies[strategyIds[i]].active) {
                activeCount++;
            }
        }
        
        // Create array of active strategy IDs
        bytes32[] memory activeStrategies = new bytes32[](activeCount);
        uint256 index = 0;
        
        for (uint256 i = 0; i < strategyIds.length; i++) {
            if (strategies[strategyIds[i]].active) {
                activeStrategies[index] = strategyIds[i];
                index++;
            }
        }
        
        return activeStrategies;
    }

    /**
     * @dev Get strategies by provider
     * @param _provider Address of the provider
     * @return Array of strategy IDs
     */
    function getProviderStrategies(
        address _provider
    ) external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        uint256 count = 0;
        
        // Count provider strategies
        for (uint256 i = 0; i < strategyIds.length; i++) {
            if (strategies[strategyIds[i]].provider == _provider) {
                count++;
            }
        }
        
        // Create array of provider strategy IDs
        bytes32[] memory providerStrategies = new bytes32[](count);
        uint256 index = 0;
        
        for (uint256 i = 0; i < strategyIds.length; i++) {
            if (strategies[strategyIds[i]].provider == _provider) {
                providerStrategies[index] = strategyIds[i];
                index++;
            }
        }
        
        return providerStrategies;
    }

    /**
     * @dev Get strategies leased by a lessee
     * @param _lessee Address of the lessee
     * @return Array of strategy IDs
     */
    function getLesseeStrategies(
        address _lessee
    ) external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return lesseeStrategies[_lessee];
    }

    /**
     * @dev Update platform fee
     * @param _platformFeeBps New platform fee in basis points
     */
    function updatePlatformFee(
        uint256 _platformFeeBps
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_platformFeeBps <= 1000, "Fee cannot exceed 10%");
        
        uint256 previousFee = platformFeeBps;
        platformFeeBps = _platformFeeBps;
        
        emit PlatformFeeUpdated(previousFee, _platformFeeBps);
    }

    /**
     * @dev Update fee treasury
     * @param _feeTreasury New fee treasury address
     */
    function updateFeeTreasury(
        address _feeTreasury
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_feeTreasury != address(0), "Invalid treasury address");
        
        address previousTreasury = feeTreasury;
        feeTreasury = _feeTreasury;
        
        emit FeeTreasuryUpdated(previousTreasury, _feeTreasury);
    }

    /**
     * @dev Pause the contract
     */
    function pause() external onlyRole(ADMIN_ROLE)  nonReentrant onlyOwner{
        _pause();
    }

    /**
     * @dev Unpause the contract
     */
    function unpause() external onlyRole(ADMIN_ROLE)  nonReentrant onlyOwner{
        _unpause();
    }
}
