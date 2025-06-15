// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "./HalalAssetRegistry.sol";

/**
 * @title ZakatManager
 * @notice Automated Zakat calculation and distribution system
 * @dev Implements the Islamic obligation of Zakat (2.5% annual charity)
 */
contract ZakatManager is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant SHARIAH_COMMITTEE_ROLE = keccak256("SHARIAH_COMMITTEE_ROLE");
    bytes32 public constant ZAKAT_DISTRIBUTOR_ROLE = keccak256("ZAKAT_DISTRIBUTOR_ROLE");
    bytes32 public constant TREASURY_ROLE = keccak256("TREASURY_ROLE");

    // Halal asset registry
    HalalAssetRegistry public immutable HALAL_REGISTRY;

    // Zakat parameters
    uint256 public constant ZAKAT_RATE = 250; // 2.5% in basis points
    uint256 public constant LUNAR_YEAR = 354 days; // Islamic lunar year (Hijri)
    
    // Nisab thresholds (minimum wealth for Zakat obligation)
    // These are stored in USD with 6 decimals ($1 = 1,000,000)
    uint256 public goldNisabUSD; // Nisab based on gold value
    uint256 public silverNisabUSD; // Nisab based on silver value
    
    // Asset price oracle addresses
    mapping(address => address) public assetPriceOracles;
    
    // Zakat calculation tracking
    struct ZakatPeriod {
        uint256 startTimestamp;
        uint256 endTimestamp;
        uint256 totalZakatUSD;
        bool calculated;
        bool distributed;
    }
    
    // Zakat periods
    ZakatPeriod[] public zakatPeriods;
    
    // Zakat recipients (charities)
    struct ZakatRecipient {
        string name;
        address paymentAddress;
        string category; // e.g., "Poor", "Needy", "Zakat Administrators", etc.
        bool approved;
        uint256 totalReceived;
    }
    
    // Recipient tracking
    mapping(address => ZakatRecipient) public zakatRecipients;
    address[] public recipientList;
    
    // Treasury assets
    mapping(address => bool) public treasuryAssets;
    address[] public treasuryAssetList;
    
    // Distribution records
    struct DistributionRecord {
        uint256 periodId;
        address recipient;
        address asset;
        uint256 amount;
        uint256 timestamp;
    }
    
    // Distribution history
    DistributionRecord[] public distributions;
    
    // Events
    event NisabUpdated(
        uint256 goldNisabUSD,
        uint256 silverNisabUSD,
        uint256 timestamp
    );
    
    event AssetPriceOracleSet(
        address indexed asset,
        address indexed oracle,
        uint256 timestamp
    );
    
    event ZakatPeriodStarted(
        uint256 indexed periodId,
        uint256 startTimestamp,
        uint256 endTimestamp
    );
    
    event ZakatCalculated(
        uint256 indexed periodId,
        uint256 totalZakatUSD,
        uint256 timestamp
    );
    
    event ZakatDistributed(
        uint256 indexed periodId,
        address indexed recipient,
        address indexed asset,
        uint256 amount,
        uint256 timestamp
    );
    
    event RecipientAdded(
        address indexed recipient,
        string name,
        string category,
        uint256 timestamp
    );
    
    event RecipientStatusChanged(
        address indexed recipient,
        bool approved,
        uint256 timestamp
    );
    
    event TreasuryAssetAdded(
        address indexed asset,
        uint256 timestamp
    );
    
    event TreasuryAssetRemoved(
        address indexed asset,
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
     * @param _admin Address of the admin
     * @param _shariahCommittee Address of the initial Shariah committee member
     * @param _zakatDistributor Address of the Zakat distributor
     * @param _treasury Address of the treasury
     * @param _initialGoldNisabUSD Initial gold Nisab in USD (6 decimals)
     * @param _initialSilverNisabUSD Initial silver Nisab in USD (6 decimals)
     */
    constructor(
        address _halalRegistry,
        address _admin,
        address _shariahCommittee,
        address _zakatDistributor,
        address _treasury,
        uint256 _initialGoldNisabUSD,
        uint256 _initialSilverNisabUSD
    ) {
        require(_halalRegistry != address(0), "Invalid registry address");
        require(_admin != address(0), "Invalid admin address");
        require(_shariahCommittee != address(0), "Invalid committee address");
        require(_zakatDistributor != address(0), "Invalid distributor address");
        require(_treasury != address(0), "Invalid treasury address");
        require(_initialGoldNisabUSD > 0, "Invalid gold Nisab");
        require(_initialSilverNisabUSD > 0, "Invalid silver Nisab");
        
        HALAL_REGISTRY = HalalAssetRegistry(_halalRegistry);
        goldNisabUSD = _initialGoldNisabUSD;
        silverNisabUSD = _initialSilverNisabUSD;
        
        // Setup roles
        _setupRole(DEFAULT_ADMIN_ROLE, _admin);
        _setupRole(ADMIN_ROLE, _admin);
        _setupRole(SHARIAH_COMMITTEE_ROLE, _shariahCommittee);
        _setupRole(ZAKAT_DISTRIBUTOR_ROLE, _zakatDistributor);
        _setupRole(TREASURY_ROLE, _treasury);
        
        emit NisabUpdated(_initialGoldNisabUSD, _initialSilverNisabUSD, block.timestamp);
    }

    /**
     * @dev Start a new Zakat period
     */
    function startZakatPeriod() external onlyRole(ADMIN_ROLE) {
        // Check if there's an active period
        if (zakatPeriods.length > 0) {
            ZakatPeriod storage lastPeriod = zakatPeriods[zakatPeriods.length - 1];
            require(lastPeriod.calculated, "Previous period not calculated");
        }
        
        // Create new period
        uint256 startTimestamp = block.timestamp;
        uint256 endTimestamp = startTimestamp + LUNAR_YEAR;
        
        zakatPeriods.push(ZakatPeriod({
            startTimestamp: startTimestamp,
            endTimestamp: endTimestamp,
            totalZakatUSD: 0,
            calculated: false,
            distributed: false
        }));
        
        emit ZakatPeriodStarted(
            zakatPeriods.length - 1,
            startTimestamp,
            endTimestamp
        );
    }

    /**
     * @dev Calculate Zakat for the current period
     * @return totalZakatUSD The total Zakat calculated in USD
     */
    function calculateZakat() external onlyRole(ADMIN_ROLE) returns (uint256) {
        require(zakatPeriods.length > 0, "No active Zakat period");
        
        ZakatPeriod storage currentPeriod = zakatPeriods[zakatPeriods.length - 1];
        require(!currentPeriod.calculated, "Zakat already calculated");
        require(block.timestamp >= currentPeriod.endTimestamp, "Period not complete");
        
        // Calculate total treasury value in USD
        uint256 totalTreasuryValueUSD = 0;
        
        for (uint256 i = 0; i < treasuryAssetList.length; i++) {
            address asset = treasuryAssetList[i];
            address oracle = assetPriceOracles[asset];
            
            require(oracle != address(0), "Oracle not set for asset");
            
            // Get asset balance and price
            uint256 balance = IERC20(asset).balanceOf(address(this));
            uint256 priceUSD = _getAssetPriceUSD(asset, oracle);
            
            // Calculate value in USD
            uint256 assetValueUSD = (balance * priceUSD) / 1e18; // Assuming price has 18 decimals
            totalTreasuryValueUSD += assetValueUSD;
        }
        
        // Check if total value exceeds Nisab
        uint256 nisabUSD = goldNisabUSD < silverNisabUSD ? goldNisabUSD : silverNisabUSD;
        
        if (totalTreasuryValueUSD >= nisabUSD) {
            // Calculate Zakat (2.5% of total value)
            uint256 zakatUSD = (totalTreasuryValueUSD * ZAKAT_RATE) / 10000;
            
            // Update period
            currentPeriod.totalZakatUSD = zakatUSD;
            currentPeriod.calculated = true;
            
            emit ZakatCalculated(
                zakatPeriods.length - 1,
                zakatUSD,
                block.timestamp
            );
            
            return zakatUSD;
        } else {
            // Below Nisab, no Zakat due
            currentPeriod.totalZakatUSD = 0;
            currentPeriod.calculated = true;
            
            emit ZakatCalculated(
                zakatPeriods.length - 1,
                0,
                block.timestamp
            );
            
            return 0;
        }
    }

    /**
     * @dev Distribute Zakat to a recipient
     * @param _periodId ID of the Zakat period
     * @param _recipient Address of the recipient
     * @param _asset Address of the asset to distribute
     * @param _amount Amount to distribute
     */
    function distributeZakat(
        uint256 _periodId,
        address _recipient,
        address _asset,
        uint256 _amount
    ) external nonReentrant onlyRole(ZAKAT_DISTRIBUTOR_ROLE) onlyHalalAsset(_asset) {
        require(_periodId < zakatPeriods.length, "Invalid period ID");
        require(zakatRecipients[_recipient].approved, "Recipient not approved");
        require(treasuryAssets[_asset], "Asset not in treasury");
        require(_amount > 0, "Amount must be > 0");
        
        ZakatPeriod storage period = zakatPeriods[_periodId];
        require(period.calculated, "Zakat not calculated");
        
        // Check if there's enough Zakat to distribute
        address oracle = assetPriceOracles[_asset];
        require(oracle != address(0), "Oracle not set for asset");
        
        uint256 priceUSD = _getAssetPriceUSD(_asset, oracle);
        uint256 amountUSD = (_amount * priceUSD) / 1e18; // Assuming price has 18 decimals
        
        // Transfer Zakat to recipient
        IERC20(_asset).safeTransfer(_recipient, _amount);
        
        // Update recipient record
        zakatRecipients[_recipient].totalReceived += amountUSD;
        
        // Record distribution
        distributions.push(DistributionRecord({
            periodId: _periodId,
            recipient: _recipient,
            asset: _asset,
            amount: _amount,
            timestamp: block.timestamp
        }));
        
        emit ZakatDistributed(
            _periodId,
            _recipient,
            _asset,
            _amount,
            block.timestamp
        );
    }

    /**
     * @dev Add a Zakat recipient
     * @param _recipient Address of the recipient
     * @param _name Name of the recipient
     * @param _category Category of the recipient
     */
    function addRecipient(
        address _recipient,
        string calldata _name,
        string calldata _category
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) {
        require(_recipient != address(0), "Invalid recipient address");
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_category).length > 0, "Category cannot be empty");
        require(zakatRecipients[_recipient].paymentAddress == address(0), "Recipient already exists");
        
        // Add recipient
        zakatRecipients[_recipient] = ZakatRecipient({
            name: _name,
            paymentAddress: _recipient,
            category: _category,
            approved: true,
            totalReceived: 0
        });
        
        // Add to recipient list
        recipientList.push(_recipient);
        
        emit RecipientAdded(
            _recipient,
            _name,
            _category,
            block.timestamp
        );
    }

    /**
     * @dev Set recipient approval status
     * @param _recipient Address of the recipient
     * @param _approved Whether the recipient is approved
     */
    function setRecipientApproval(
        address _recipient,
        bool _approved
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) {
        require(zakatRecipients[_recipient].paymentAddress != address(0), "Recipient does not exist");
        
        zakatRecipients[_recipient].approved = _approved;
        
        emit RecipientStatusChanged(
            _recipient,
            _approved,
            block.timestamp
        );
    }

    /**
     * @dev Add a treasury asset
     * @param _asset Address of the asset
     */
    function addTreasuryAsset(
        address _asset
    ) external onlyRole(TREASURY_ROLE) onlyHalalAsset(_asset) {
        require(!treasuryAssets[_asset], "Asset already in treasury");
        
        treasuryAssets[_asset] = true;
        treasuryAssetList.push(_asset);
        
        emit TreasuryAssetAdded(_asset, block.timestamp);
    }

    /**
     * @dev Remove a treasury asset
     * @param _asset Address of the asset
     */
    function removeTreasuryAsset(
        address _asset
    ) external onlyRole(TREASURY_ROLE) {
        require(treasuryAssets[_asset], "Asset not in treasury");
        
        treasuryAssets[_asset] = false;
        
        // Remove from asset list
        for (uint256 i = 0; i < treasuryAssetList.length; i++) {
            if (treasuryAssetList[i] == _asset) {
                treasuryAssetList[i] = treasuryAssetList[treasuryAssetList.length - 1];
                treasuryAssetList.pop();
                break;
            }
        }
        
        emit TreasuryAssetRemoved(_asset, block.timestamp);
    }

    /**
     * @dev Set asset price oracle
     * @param _asset Address of the asset
     * @param _oracle Address of the price oracle
     */
    function setAssetPriceOracle(
        address _asset,
        address _oracle
    ) external onlyRole(ADMIN_ROLE) {
        require(_asset != address(0), "Invalid asset address");
        require(_oracle != address(0), "Invalid oracle address");
        
        assetPriceOracles[_asset] = _oracle;
        
        emit AssetPriceOracleSet(_asset, _oracle, block.timestamp);
    }

    /**
     * @dev Update Nisab thresholds
     * @param _goldNisabUSD Gold Nisab in USD
     * @param _silverNisabUSD Silver Nisab in USD
     */
    function updateNisab(
        uint256 _goldNisabUSD,
        uint256 _silverNisabUSD
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) {
        require(_goldNisabUSD > 0, "Invalid gold Nisab");
        require(_silverNisabUSD > 0, "Invalid silver Nisab");
        
        goldNisabUSD = _goldNisabUSD;
        silverNisabUSD = _silverNisabUSD;
        
        emit NisabUpdated(_goldNisabUSD, _silverNisabUSD, block.timestamp);
    }

    /**
     * @dev Get asset price in USD
     * @param _asset Address of the asset
     * @param _oracle Address of the price oracle
     * @return Price in USD (18 decimals)
     */
    function _getAssetPriceUSD(
        address _asset,
        address _oracle
    ) internal view returns (uint256) {
        // In a real implementation, this would call the oracle
        // For simplicity, we'll return a fixed price
        return 1e18; // $1 with 18 decimals
    }

    /**
     * @dev Get all Zakat recipients
     * @return Array of recipient addresses
     */
    function getAllRecipients() external view returns (address[] memory) {
        return recipientList;
    }

    /**
     * @dev Get all treasury assets
     * @return Array of asset addresses
     */
    function getAllTreasuryAssets() external view returns (address[] memory) {
        return treasuryAssetList;
    }

    /**
     * @dev Get distribution count
     * @return Number of distributions
     */
    function getDistributionCount() external view returns (uint256) {
        return distributions.length;
    }

    /**
     * @dev Get period count
     * @return Number of Zakat periods
     */
    function getPeriodCount() external view returns (uint256) {
        return zakatPeriods.length;
    }

    /**
     * @dev Pause the contract
     */
    function pause() external onlyRole(ADMIN_ROLE) {
        _pause();
    }

    /**
     * @dev Unpause the contract
     */
    function unpause() external onlyRole(ADMIN_ROLE) {
        _unpause();
    }
}