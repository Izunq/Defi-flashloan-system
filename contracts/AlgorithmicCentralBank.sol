// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "./InterChainCognitiveMesh.sol";

/**
 * @title AlgorithmicCentralBank
 * @notice Stabilizes markets and provides liquidity during crises
 * @dev Part of the V49 Economic Singularity architecture
 */
contract AlgorithmicCentralBank is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;
    using Math for uint256;

    // Role definitions
    bytes32 public constant BANK_ADMIN_ROLE = keccak256("BANK_ADMIN_ROLE");
    bytes32 public constant POLICY_COMMITTEE_ROLE = keccak256("POLICY_COMMITTEE_ROLE");
    bytes32 public constant EMERGENCY_RESPONSE_ROLE = keccak256("EMERGENCY_RESPONSE_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");

    // Inter-Chain Cognitive Mesh reference
    InterChainCognitiveMesh public cognitiveMesh;

    // Market state enum
    enum MarketState {
        Normal,
        Volatile,
        Stressed,
        Crisis
    }

    // Asset type enum
    enum AssetType {
        Stablecoin,
        GovernanceToken,
        LiquidityToken,
        DebtToken,
        Other
    }

    // Asset information
    struct AssetInfo {
        address tokenAddress;
        string symbol;
        AssetType assetType;
        uint256 targetPrice;
        uint256 minPrice;
        uint256 maxPrice;
        uint256 volatilityThreshold;
        bool isStabilized;
        bool isEmergencyAsset;
        uint256 reserveRatio;
        uint256 maxLiquidity;
    }

    // Market information
    struct MarketInfo {
        address marketAddress;
        string name;
        MarketState state;
        uint256 lastStateUpdate;
        uint256 volatility;
        uint256 liquidity;
        uint256 volume24h;
        uint256 stabilizationFactor;
        bool isMonitored;
        bool isProtected;
    }

    // Intervention record
    struct Intervention {
        uint256 id;
        address market;
        address asset;
        uint256 amount;
        uint256 price;
        bool isInjection;
        uint256 timestamp;
        string reason;
        address executor;
    }

    // Policy parameters
    struct PolicyParameters {
        uint256 baseReserveRatio;
        uint256 volatilityMultiplier;
        uint256 maxInterventionSize;
        uint256 interventionCooldown;
        uint256 emergencyThreshold;
        uint256 stabilizationFee;
    }

    // Mappings
    mapping(address => AssetInfo) public assets;
    mapping(address => MarketInfo) public markets;
    mapping(uint256 => Intervention) public interventions;
    
    // Arrays for iteration
    address[] public assetList;
    address[] public marketList;
    
    // Counters
    uint256 public assetCount;
    uint256 public marketCount;
    uint256 public interventionCount;
    
    // Treasury
    address public treasuryAddress;
    uint256 public totalReserves;
    uint256 public allocatedReserves;
    uint256 public emergencyReserves;
    
    // Policy parameters
    PolicyParameters public policyParams;
    
    // Events
    event AssetRegistered(
        address indexed tokenAddress,
        string symbol,
        AssetType assetType,
        uint256 targetPrice
    );
    
    event AssetUpdated(
        address indexed tokenAddress,
        uint256 targetPrice,
        uint256 minPrice,
        uint256 maxPrice,
        bool isStabilized
    );
    
    event MarketRegistered(
        address indexed marketAddress,
        string name,
        bool isMonitored,
        bool isProtected
    );
    
    event MarketStateChanged(
        address indexed marketAddress,
        MarketState oldState,
        MarketState newState,
        uint256 timestamp
    );
    
    event InterventionExecuted(
        uint256 indexed interventionId,
        address indexed market,
        address indexed asset,
        uint256 amount,
        uint256 price,
        bool isInjection,
        string reason
    );
    
    event ReservesUpdated(
        uint256 totalReserves,
        uint256 allocatedReserves,
        uint256 emergencyReserves
    );
    
    event PolicyParametersUpdated(
        uint256 baseReserveRatio,
        uint256 volatilityMultiplier,
        uint256 maxInterventionSize,
        uint256 interventionCooldown
    );
    
    event EmergencyModeActivated(
        address indexed market,
        string reason,
        uint256 timestamp
    );
    
    event EmergencyModeDeactivated(
        address indexed market,
        uint256 timestamp
    );
    
    /**
     * @dev Constructor
     * @param _cognitiveMeshAddress Address of the InterChainCognitiveMesh contract
     * @param _treasuryAddress Address of the treasury
     */
    constructor(address _cognitiveMeshAddress, address _treasuryAddress) {
        require(_cognitiveMeshAddress != address(0), "Invalid CognitiveMesh address");
        require(_treasuryAddress != address(0), "Invalid treasury address");
        
        cognitiveMesh = InterChainCognitiveMesh(_cognitiveMeshAddress);
        treasuryAddress = _treasuryAddress;
        
        // Setup roles
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), msg.sender);
        _grantRole(BANK_ADMIN_ROLE, msg.sender);
        _grantRole(POLICY_COMMITTEE_ROLE, msg.sender);
        _grantRole(EMERGENCY_RESPONSE_ROLE, msg.sender);
        
        // Initialize policy parameters
        policyParams = PolicyParameters({
            baseReserveRatio: 2000, // 20%
            volatilityMultiplier: 150, // 1.5x
            maxInterventionSize: 1000, // 10%
            interventionCooldown: 1 hours,
            emergencyThreshold: 3000, // 30%
            stabilizationFee: 50 // 0.5%
        });
    }
    
    /**
     * @dev Register a new asset
     * @param _tokenAddress Address of the token
     * @param _symbol Symbol of the token
     * @param _assetType Type of the asset
     * @param _targetPrice Target price in USD (scaled by 1e18)
     * @param _minPrice Minimum acceptable price
     * @param _maxPrice Maximum acceptable price
     * @param _volatilityThreshold Threshold for volatility intervention
     * @param _isStabilized Whether the asset is actively stabilized
     * @param _isEmergencyAsset Whether the asset is used in emergencies
     * @param _reserveRatio Reserve ratio for the asset
     * @param _maxLiquidity Maximum liquidity to provide
     */
    function registerAsset(
        address _tokenAddress,
        string memory _symbol,
        AssetType _assetType,
        uint256 _targetPrice,
        uint256 _minPrice,
        uint256 _maxPrice,
        uint256 _volatilityThreshold,
        bool _isStabilized,
        bool _isEmergencyAsset,
        uint256 _reserveRatio,
        uint256 _maxLiquidity
    ) external onlyRole(BANK_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_tokenAddress != address(0), "Invalid token address");
        require(assets[_tokenAddress].tokenAddress == address(0), "Asset already registered");
        require(_targetPrice > 0, "Target price must be greater than zero");
        require(_minPrice < _targetPrice && _maxPrice > _targetPrice, "Invalid price bounds");
        
        assets[_tokenAddress] = AssetInfo({
            tokenAddress: _tokenAddress,
            symbol: _symbol,
            assetType: _assetType,
            targetPrice: _targetPrice,
            minPrice: _minPrice,
            maxPrice: _maxPrice,
            volatilityThreshold: _volatilityThreshold,
            isStabilized: _isStabilized,
            isEmergencyAsset: _isEmergencyAsset,
            reserveRatio: _reserveRatio,
            maxLiquidity: _maxLiquidity
        });
        
        assetList.push(_tokenAddress);
        assetCount++;
        
        emit AssetRegistered(
            _tokenAddress,
            _symbol,
            _assetType,
            _targetPrice
        );
    }
    
    /**
     * @dev Update an asset
     * @param _tokenAddress Address of the token
     * @param _targetPrice New target price
     * @param _minPrice New minimum price
     * @param _maxPrice New maximum price
     * @param _volatilityThreshold New volatility threshold
     * @param _isStabilized Whether the asset is actively stabilized
     * @param _isEmergencyAsset Whether the asset is used in emergencies
     * @param _reserveRatio New reserve ratio
     * @param _maxLiquidity New maximum liquidity
     */
    function updateAsset(
        address _tokenAddress,
        uint256 _targetPrice,
        uint256 _minPrice,
        uint256 _maxPrice,
        uint256 _volatilityThreshold,
        bool _isStabilized,
        bool _isEmergencyAsset,
        uint256 _reserveRatio,
        uint256 _maxLiquidity
    ) external onlyRole(BANK_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(assets[_tokenAddress].tokenAddress != address(0), "Asset not registered");
        require(_targetPrice > 0, "Target price must be greater than zero");
        require(_minPrice < _targetPrice && _maxPrice > _targetPrice, "Invalid price bounds");
        
        AssetInfo storage asset = assets[_tokenAddress];
        
        asset.targetPrice = _targetPrice;
        asset.minPrice = _minPrice;
        asset.maxPrice = _maxPrice;
        asset.volatilityThreshold = _volatilityThreshold;
        asset.isStabilized = _isStabilized;
        asset.isEmergencyAsset = _isEmergencyAsset;
        asset.reserveRatio = _reserveRatio;
        asset.maxLiquidity = _maxLiquidity;
        
        emit AssetUpdated(
            _tokenAddress,
            _targetPrice,
            _minPrice,
            _maxPrice,
            _isStabilized
        );
    }
    
    /**
     * @dev Register a new market
     * @param _marketAddress Address of the market
     * @param _name Name of the market
     * @param _isMonitored Whether the market is monitored
     * @param _isProtected Whether the market is protected
     * @param _stabilizationFactor Stabilization factor for the market
     */
    function registerMarket(
        address _marketAddress,
        string memory _name,
        bool _isMonitored,
        bool _isProtected,
        uint256 _stabilizationFactor
    ) external onlyRole(BANK_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_marketAddress != address(0), "Invalid market address");
        require(markets[_marketAddress].marketAddress == address(0), "Market already registered");
        
        markets[_marketAddress] = MarketInfo({
            marketAddress: _marketAddress,
            name: _name,
            state: MarketState.Normal,
            lastStateUpdate: block.timestamp,
            volatility: 0,
            liquidity: 0,
            volume24h: 0,
            stabilizationFactor: _stabilizationFactor,
            isMonitored: _isMonitored,
            isProtected: _isProtected
        });
        
        marketList.push(_marketAddress);
        marketCount++;
        
        emit MarketRegistered(
            _marketAddress,
            _name,
            _isMonitored,
            _isProtected
        );
    }
    
    /**
     * @dev Update market state
     * @param _marketAddress Address of the market
     * @param _newState New market state
     * @param _volatility Current volatility
     * @param _liquidity Current liquidity
     * @param _volume24h 24-hour volume
     */
    function updateMarketState(
        address _marketAddress,
        MarketState _newState,
        uint256 _volatility,
        uint256 _liquidity,
        uint256 _volume24h
    ) external onlyRole(ORACLE_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(markets[_marketAddress].marketAddress != address(0), "Market not registered");
        
        MarketInfo storage market = markets[_marketAddress];
        MarketState oldState = market.state;
        
        market.state = _newState;
        market.lastStateUpdate = block.timestamp;
        market.volatility = _volatility;
        market.liquidity = _liquidity;
        market.volume24h = _volume24h;
        
        emit MarketStateChanged(
            _marketAddress,
            oldState,
            _newState,
            block.timestamp
        );
        
        // If market entered crisis state, consider emergency response
        if (_newState == MarketState.Crisis && oldState != MarketState.Crisis) {
            _considerEmergencyResponse(_marketAddress);
        }
    }
    
    /**
     * @dev Execute a market intervention
     * @param _marketAddress Address of the market
     * @param _tokenAddress Address of the token
     * @param _amount Amount of tokens
     * @param _price Current price
     * @param _isInjection Whether this is a liquidity injection
     * @param _reason Reason for the intervention
     */
    function executeIntervention(
        address _marketAddress,
        address _tokenAddress,
        uint256 _amount,
        uint256 _price,
        bool _isInjection,
        string memory _reason
    ) external onlyRole(POLICY_COMMITTEE_ROLE) nonReentrant {
        require(markets[_marketAddress].marketAddress != address(0), "Market not registered");
        require(assets[_tokenAddress].tokenAddress != address(0), "Asset not registered");
        require(_amount > 0, "Amount must be greater than zero");
        
        MarketInfo storage market = markets[_marketAddress];
        AssetInfo storage asset = assets[_tokenAddress];
        
        // Check if intervention is allowed
        require(market.isProtected, "Market is not protected");
        require(asset.isStabilized, "Asset is not stabilized");
        
        // Check if price is outside acceptable bounds
        if (_isInjection) {
            require(_price < asset.targetPrice, "Price not below target");
        } else {
            require(_price > asset.targetPrice, "Price not above target");
        }
        
        // Calculate maximum intervention size
        uint256 maxIntervention = (totalReserves * policyParams.maxInterventionSize) / 10000;
        require(_amount <= maxIntervention, "Intervention too large");
        
        // Execute the intervention
        if (_isInjection) {
            // Transfer tokens from treasury to market
            IERC20(asset.tokenAddress).safeTransferFrom(treasuryAddress, _marketAddress, _amount);
            allocatedReserves += _amount;
        } else {
            // Transfer tokens from market to treasury
            IERC20(asset.tokenAddress).safeTransferFrom(_marketAddress, treasuryAddress, _amount);
            allocatedReserves = allocatedReserves > _amount ? allocatedReserves - _amount : 0;
        }
        
        // Record the intervention
        uint256 interventionId = interventionCount++;
        
        interventions[interventionId] = Intervention({
            id: interventionId,
            market: _marketAddress,
            asset: _tokenAddress,
            amount: _amount,
            price: _price,
            isInjection: _isInjection,
            timestamp: block.timestamp,
            reason: _reason,
            executor: msg.sender
        });
        
        emit InterventionExecuted(
            interventionId,
            _marketAddress,
            _tokenAddress,
            _amount,
            _price,
            _isInjection,
            _reason
        );
        
        // Update reserves
        _updateReserves();
        
        // Update global state in the cognitive mesh
        _updateGlobalState();
    }
    
    /**
     * @dev Activate emergency mode for a market
     * @param _marketAddress Address of the market
     * @param _reason Reason for activation
     */
    function activateEmergencyMode(
        address _marketAddress,
        string memory _reason
    ) external onlyRole(EMERGENCY_RESPONSE_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(markets[_marketAddress].marketAddress != address(0), "Market not registered");
        
        MarketInfo storage market = markets[_marketAddress];
        
        // Set market state to Crisis
        MarketState oldState = market.state;
        market.state = MarketState.Crisis;
        market.lastStateUpdate = block.timestamp;
        
        emit MarketStateChanged(
            _marketAddress,
            oldState,
            MarketState.Crisis,
            block.timestamp
        );
        
        emit EmergencyModeActivated(
            _marketAddress,
            _reason,
            block.timestamp
        );
        
        // Update global state in the cognitive mesh
        _updateGlobalState();
    }
    
    /**
     * @dev Deactivate emergency mode for a market
     * @param _marketAddress Address of the market
     * @param _newState New market state
     */
    function deactivateEmergencyMode(
        address _marketAddress,
        MarketState _newState
    ) external onlyRole(EMERGENCY_RESPONSE_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(markets[_marketAddress].marketAddress != address(0), "Market not registered");
        require(_newState != MarketState.Crisis, "Cannot set to Crisis state");
        
        MarketInfo storage market = markets[_marketAddress];
        
        // Ensure market is currently in Crisis state
        require(market.state == MarketState.Crisis, "Market not in Crisis state");
        
        // Update market state
        market.state = _newState;
        market.lastStateUpdate = block.timestamp;
        
        emit MarketStateChanged(
            _marketAddress,
            MarketState.Crisis,
            _newState,
            block.timestamp
        );
        
        emit EmergencyModeDeactivated(
            _marketAddress,
            block.timestamp
        );
        
        // Update global state in the cognitive mesh
        _updateGlobalState();
    }
    
    /**
     * @dev Update policy parameters
     * @param _baseReserveRatio New base reserve ratio
     * @param _volatilityMultiplier New volatility multiplier
     * @param _maxInterventionSize New maximum intervention size
     * @param _interventionCooldown New intervention cooldown
     * @param _emergencyThreshold New emergency threshold
     * @param _stabilizationFee New stabilization fee
     */
    function updatePolicyParameters(
        uint256 _baseReserveRatio,
        uint256 _volatilityMultiplier,
        uint256 _maxInterventionSize,
        uint256 _interventionCooldown,
        uint256 _emergencyThreshold,
        uint256 _stabilizationFee
    ) external onlyRole(POLICY_COMMITTEE_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_baseReserveRatio <= 10000, "Reserve ratio cannot exceed 100%");
        require(_maxInterventionSize <= 5000, "Intervention size cannot exceed 50%");
        require(_emergencyThreshold <= 5000, "Emergency threshold cannot exceed 50%");
        require(_stabilizationFee <= 1000, "Stabilization fee cannot exceed 10%");
        
        policyParams.baseReserveRatio = _baseReserveRatio;
        policyParams.volatilityMultiplier = _volatilityMultiplier;
        policyParams.maxInterventionSize = _maxInterventionSize;
        policyParams.interventionCooldown = _interventionCooldown;
        policyParams.emergencyThreshold = _emergencyThreshold;
        policyParams.stabilizationFee = _stabilizationFee;
        
        emit PolicyParametersUpdated(
            _baseReserveRatio,
            _volatilityMultiplier,
            _maxInterventionSize,
            _interventionCooldown
        );
        
        // Update global state in the cognitive mesh
        _updateGlobalState();
    }
    
    /**
     * @dev Update treasury address
     * @param _newTreasuryAddress New treasury address
     */
    function updateTreasuryAddress(address _newTreasuryAddress) external onlyRole(BANK_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_newTreasuryAddress != address(0), "Invalid treasury address");
        treasuryAddress = _newTreasuryAddress;
    }
    
    /**
     * @dev Update reserves
     */
    function _updateReserves() internal {
        // Calculate total reserves
        totalReserves = 0;
        
        for (uint256 i = 0; i < assetList.length; i++) {
            address tokenAddress = assetList[i];
            uint256 balance = IERC20(tokenAddress).balanceOf(treasuryAddress);
            
            // Convert to USD value
            uint256 usdValue = (balance * assets[tokenAddress].targetPrice) / 1e18;
            totalReserves += usdValue;
        }
        
        // Calculate emergency reserves
        emergencyReserves = (totalReserves * policyParams.emergencyThreshold) / 10000;
        
        emit ReservesUpdated(
            totalReserves,
            allocatedReserves,
            emergencyReserves
        );
    }
    
    /**
     * @dev Consider emergency response for a market
     * @param _marketAddress Address of the market
     */
    function _considerEmergencyResponse(address _marketAddress) internal {
        // This is a placeholder for more complex emergency response logic
        // In a real implementation, this would analyze the market and decide on appropriate actions
        
        // For now, just emit an event
        emit EmergencyModeActivated(
            _marketAddress,
            "Automatic response to crisis state",
            block.timestamp
        );
    }
    
    /**
     * @dev Update global state in the cognitive mesh
     */
    function _updateGlobalState() internal {
        // Create a state update
        bytes memory stateUpdate = abi.encode(
            block.timestamp,
            totalReserves,
            allocatedReserves,
            emergencyReserves,
            policyParams
        );
        
        // Update global state in the cognitive mesh
        bytes32 stateKey = keccak256("algorithmic_central_bank_state");
        
        // This would be a cross-contract call in a real implementation
        // cognitiveMesh.updateGlobalState(stateKey, stateUpdate);
    }
    
    /**
     * @dev Get all registered assets
     * @return List of asset addresses
     */
    function getAllAssets() external view returns (address[] memory)  {
        // TODO: Add nonReentrant modifier
        return assetList;
    }
    
    /**
     * @dev Get all registered markets
     * @return List of market addresses
     */
    function getAllMarkets() external view returns (address[] memory)  {
        // TODO: Add nonReentrant modifier
        return marketList;
    }
    
    /**
     * @dev Get intervention details
     * @param _interventionId Intervention ID
     * @return Intervention details
     */
    function getIntervention(uint256 _interventionId) external view returns (Intervention memory)  {
        // TODO: Add nonReentrant modifier
        require(_interventionId < interventionCount, "Invalid intervention ID");
        return interventions[_interventionId];
    }
    
    /**
     * @dev Get recent interventions
     * @param _count Number of interventions to get
     * @return List of recent interventions
     */
    function getRecentInterventions(uint256 _count) external view returns (Intervention[] memory)  {
        // TODO: Add nonReentrant modifier
        uint256 count = Math.min(_count, interventionCount);
        Intervention[] memory result = new Intervention[](count);
        
        for (uint256 i = 0; i < count; i++) {
            uint256 id = interventionCount - i - 1;
            result[i] = interventions[id];
        }
        
        return result;
    }
    
    /**
     * @dev Get market state
     * @param _marketAddress Address of the market
     * @return Market state
     */
    function getMarketState(address _marketAddress) external view returns (MarketInfo memory)  {
        // TODO: Add nonReentrant modifier
        require(markets[_marketAddress].marketAddress != address(0), "Market not registered");
        return markets[_marketAddress];
    }
    
    /**
     * @dev Get asset info
     * @param _tokenAddress Address of the token
     * @return Asset info
     */
    function getAssetInfo(address _tokenAddress) external view returns (AssetInfo memory)  {
        // TODO: Add nonReentrant modifier
        require(assets[_tokenAddress].tokenAddress != address(0), "Asset not registered");
        return assets[_tokenAddress];
    }
    
    /**
     * @dev Get markets in crisis
     * @return List of markets in crisis
     */
    function getMarketsInCrisis() external view returns (address[] memory)  {
        // TODO: Add nonReentrant modifier
        uint256 count = 0;
        
        // Count markets in crisis
        for (uint256 i = 0; i < marketList.length; i++) {
            if (markets[marketList[i]].state == MarketState.Crisis) {
                count++;
            }
        }
        
        // Create result array
        address[] memory result = new address[](count);
        uint256 index = 0;
        
        // Fill result array
        for (uint256 i = 0; i < marketList.length; i++) {
            if (markets[marketList[i]].state == MarketState.Crisis) {
                result[index++] = marketList[i];
            }
        }
        
        return result;
    }
}
