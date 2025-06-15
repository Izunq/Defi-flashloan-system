// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

/**
 * @title ArbitrageVaultERC4626
 * @notice ERC4626-compliant vault for arbitrage strategy execution
 * @dev Implements the ERC4626 standard with enhanced security features
 */
contract ArbitrageVaultERC4626 is ERC4626, AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;
    using Math for uint256;

    // Roles
    bytes32 public constant STRATEGY_EXECUTOR_ROLE = keccak256("STRATEGY_EXECUTOR_ROLE");
    bytes32 public constant EMERGENCY_ADMIN_ROLE = keccak256("EMERGENCY_ADMIN_ROLE");
    bytes32 public constant FEE_MANAGER_ROLE = keccak256("FEE_MANAGER_ROLE");

    // Fee configuration
    uint256 public performanceFee = 1000; // 10% (in basis points)
    uint256 public managementFee = 100; // 1% per year (in basis points)
    uint256 public constant MAX_FEE = 3000; // 30% maximum fee (in basis points)
    uint256 public constant FEE_DENOMINATOR = 10000;
    
    // Fee accounting
    uint256 public lastFeeCollectionTimestamp;
    uint256 public accumulatedManagementFee;
    address public feeCollector;
    
    // Deposit/withdrawal limits
    uint256 public maxDeposit;
    uint256 public minDeposit;
    uint256 public maxWithdrawal;
    
    // Cooldown periods
    uint256 public depositCooldown = 0;
    uint256 public withdrawalCooldown = 0;
    mapping(address => uint256) public lastDepositTimestamp;
    mapping(address => uint256) public lastWithdrawalTimestamp;
    
    // Events
    event PerformanceFeeCollected(uint256 amount, uint256 timestamp);
    event ManagementFeeCollected(uint256 amount, uint256 timestamp);
    event StrategyExecuted(address indexed strategy, uint256 profit, uint256 timestamp);
    event FeesUpdated(uint256 performanceFee, uint256 managementFee);
    event FeeCollectorUpdated(address indexed newCollector);
    event DepositLimitsUpdated(uint256 minDeposit, uint256 maxDeposit);
    event WithdrawalLimitsUpdated(uint256 maxWithdrawal);
    event CooldownPeriodsUpdated(uint256 depositCooldown, uint256 withdrawalCooldown);
    
    /**
     * @dev Constructor
     * @param _asset Underlying asset token
     * @param _name Vault token name
     * @param _symbol Vault token symbol
     * @param _feeCollector Address to collect fees
     */
    constructor(
        IERC20Metadata _asset,
        string memory _name,
        string memory _symbol,
        address _feeCollector
    ) ERC4626(_asset) ERC20(_name, _symbol) {
        require(_feeCollector != address(0), "Invalid fee collector address");
        
        feeCollector = _feeCollector;
        lastFeeCollectionTimestamp = block.timestamp;
        
        // Setup roles
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(EMERGENCY_ADMIN_ROLE, msg.sender);
        _setupRole(FEE_MANAGER_ROLE, msg.sender);
        _setupRole(STRATEGY_EXECUTOR_ROLE, msg.sender);
        
        // Set default limits
        maxDeposit = type(uint256).max;
        minDeposit = 0;
        maxWithdrawal = type(uint256).max;
    }
    
    /**
     * @dev Modifier to check deposit cooldown
     */
    modifier checkDepositCooldown() {
        if (depositCooldown > 0) {
            require(
                block.timestamp >= lastDepositTimestamp[msg.sender] + depositCooldown,
                "Deposit cooldown period not elapsed"
            );
        }
        _;
        lastDepositTimestamp[msg.sender] = block.timestamp;
    }
    
    /**
     * @dev Modifier to check withdrawal cooldown
     */
    modifier checkWithdrawalCooldown() {
        if (withdrawalCooldown > 0) {
            require(
                block.timestamp >= lastWithdrawalTimestamp[msg.sender] + withdrawalCooldown,
                "Withdrawal cooldown period not elapsed"
            );
        }
        _;
        lastWithdrawalTimestamp[msg.sender] = block.timestamp;
    }
    
    /**
     * @dev Set fee parameters
     * @param _performanceFee Performance fee in basis points
     * @param _managementFee Management fee in basis points
     */
    function setFees(uint256 _performanceFee, uint256 _managementFee) 
        external 
        onlyRole(FEE_MANAGER_ROLE) 
    {
        require(_performanceFee <= MAX_FEE, "Performance fee too high");
        require(_managementFee <= MAX_FEE, "Management fee too high");
        
        // Collect any pending fees before changing rates
        _collectManagementFee();
        
        performanceFee = _performanceFee;
        managementFee = _managementFee;
        
        emit FeesUpdated(_performanceFee, _managementFee);
    }
    
    /**
     * @dev Set fee collector address
     * @param _feeCollector New fee collector address
     */
    function setFeeCollector(address _feeCollector) 
        external 
        onlyRole(FEE_MANAGER_ROLE) 
    {
        require(_feeCollector != address(0), "Invalid fee collector address");
        feeCollector = _feeCollector;
        emit FeeCollectorUpdated(_feeCollector);
    }
    
    /**
     * @dev Set deposit limits
     * @param _minDeposit Minimum deposit amount
     * @param _maxDeposit Maximum deposit amount
     */
    function setDepositLimits(uint256 _minDeposit, uint256 _maxDeposit) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        require(_minDeposit <= _maxDeposit, "Min deposit must be <= max deposit");
        minDeposit = _minDeposit;
        maxDeposit = _maxDeposit;
        emit DepositLimitsUpdated(_minDeposit, _maxDeposit);
    }
    
    /**
     * @dev Set maximum withdrawal amount
     * @param _maxWithdrawal Maximum withdrawal amount
     */
    function setMaxWithdrawal(uint256 _maxWithdrawal) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        maxWithdrawal = _maxWithdrawal;
        emit WithdrawalLimitsUpdated(_maxWithdrawal);
    }
    
    /**
     * @dev Set cooldown periods
     * @param _depositCooldown Deposit cooldown period in seconds
     * @param _withdrawalCooldown Withdrawal cooldown period in seconds
     */
    function setCooldownPeriods(uint256 _depositCooldown, uint256 _withdrawalCooldown) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        depositCooldown = _depositCooldown;
        withdrawalCooldown = _withdrawalCooldown;
        emit CooldownPeriodsUpdated(_depositCooldown, _withdrawalCooldown);
    }
    
    /**
     * @dev Emergency pause function
     */
    function emergencyPause() 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
    {
        _pause();
    }
    
    /**
     * @dev Emergency unpause function
     */
    function emergencyUnpause() 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
    {
        _unpause();
    }
    
    /**
     * @dev Record profit from strategy execution
     * @param profit Amount of profit in underlying tokens
     */
    function recordStrategyProfit(uint256 profit) 
        external 
        nonReentrant 
        whenNotPaused 
        onlyRole(STRATEGY_EXECUTOR_ROLE) 
        returns (uint256 feeAmount)
    {
        require(profit > 0, "Profit must be greater than 0");
        
        // Collect management fee first
        _collectManagementFee();
        
        // Calculate performance fee
        feeAmount = profit * performanceFee / FEE_DENOMINATOR;
        
        if (feeAmount > 0) {
            // Transfer fee to fee collector
            IERC20(asset()).safeTransfer(feeCollector, feeAmount);
            emit PerformanceFeeCollected(feeAmount, block.timestamp);
        }
        
        emit StrategyExecuted(msg.sender, profit, block.timestamp);
        
        return feeAmount;
    }
    
    /**
     * @dev Collect pending management fee
     * @return feeAmount Amount of fee collected
     */
    function collectManagementFee() 
        external 
        nonReentrant 
        whenNotPaused 
        onlyRole(FEE_MANAGER_ROLE) 
        returns (uint256 feeAmount)
    {
        return _collectManagementFee();
    }
    
    /**
     * @dev Internal function to collect management fee
     * @return feeAmount Amount of fee collected
     */
    function _collectManagementFee() internal returns (uint256 feeAmount) {
        if (block.timestamp <= lastFeeCollectionTimestamp) {
            return 0;
        }
        
        uint256 timeElapsed = block.timestamp - lastFeeCollectionTimestamp;
        uint256 totalAssets = totalAssets();
        
        // Calculate pro-rated management fee (annual fee pro-rated to the time elapsed)
        // managementFee is in basis points (1% = 100)
        // 365 days * 24 hours * 60 minutes * 60 seconds = 31536000 seconds in a year
        feeAmount = totalAssets * managementFee * timeElapsed / (FEE_DENOMINATOR * 31536000);
        
        if (feeAmount > 0) {
            // Transfer fee to fee collector
            IERC20(asset()).safeTransfer(feeCollector, feeAmount);
            emit ManagementFeeCollected(feeAmount, block.timestamp);
        }
        
        lastFeeCollectionTimestamp = block.timestamp;
        return feeAmount;
    }
    
    /**
     * @dev Override deposit function to add cooldown and limits
     */
    function deposit(uint256 assets, address receiver) 
        public 
        override 
        nonReentrant 
        whenNotPaused 
        checkDepositCooldown 
        returns (uint256) 
    {
        require(assets >= minDeposit, "Deposit amount below minimum");
        require(assets <= maxDeposit, "Deposit amount above maximum");
        
        // Collect management fee before deposit to ensure accurate share price
        _collectManagementFee();
        
        return super.deposit(assets, receiver);
    }
    
    /**
     * @dev Override mint function to add cooldown and limits
     */
    function mint(uint256 shares, address receiver) 
        public 
        override 
        nonReentrant 
        whenNotPaused 
        checkDepositCooldown 
        returns (uint256) 
    {
        uint256 assets = previewMint(shares);
        require(assets >= minDeposit, "Deposit amount below minimum");
        require(assets <= maxDeposit, "Deposit amount above maximum");
        
        // Collect management fee before mint to ensure accurate share price
        _collectManagementFee();
        
        return super.mint(shares, receiver);
    }
    
    /**
     * @dev Override withdraw function to add cooldown and limits
     */
    function withdraw(uint256 assets, address receiver, address owner) 
        public 
        override 
        nonReentrant 
        whenNotPaused 
        checkWithdrawalCooldown 
        returns (uint256) 
    {
        require(assets <= maxWithdrawal, "Withdrawal amount above maximum");
        
        // Collect management fee before withdrawal to ensure accurate share price
        _collectManagementFee();
        
        return super.withdraw(assets, receiver, owner);
    }
    
    /**
     * @dev Override redeem function to add cooldown and limits
     */
    function redeem(uint256 shares, address receiver, address owner) 
        public 
        override 
        nonReentrant 
        whenNotPaused 
        checkWithdrawalCooldown 
        returns (uint256) 
    {
        uint256 assets = previewRedeem(shares);
        require(assets <= maxWithdrawal, "Withdrawal amount above maximum");
        
        // Collect management fee before redemption to ensure accurate share price
        _collectManagementFee();
        
        return super.redeem(shares, receiver, owner);
    }
    
    /**
     * @dev Override maxDeposit function to respect deposit limit
     */
    function maxDeposit(address) public view override returns (uint256) {
        if (paused()) {
            return 0;
        }
        return maxDeposit;
    }
    
    /**
     * @dev Override maxMint function to respect deposit limit
     */
    function maxMint(address) public view override returns (uint256) {
        if (paused()) {
            return 0;
        }
        
        if (maxDeposit == type(uint256).max) {
            return type(uint256).max;
        }
        
        return convertToShares(maxDeposit);
    }
    
    /**
     * @dev Override maxWithdraw function to respect withdrawal limit
     */
    function maxWithdraw(address owner) public view override returns (uint256) {
        if (paused()) {
            return 0;
        }
        
        uint256 maxBasedOnBalance = convertToAssets(balanceOf(owner));
        return Math.min(maxBasedOnBalance, maxWithdrawal);
    }
    
    /**
     * @dev Override maxRedeem function to respect withdrawal limit
     */
    function maxRedeem(address owner) public view override returns (uint256) {
        if (paused()) {
            return 0;
        }
        
        uint256 maxBasedOnWithdrawalLimit = convertToShares(maxWithdrawal);
        return Math.min(balanceOf(owner), maxBasedOnWithdrawalLimit);
    }
    
    /**
     * @dev Override totalAssets function to account for pending fees
     */
    function totalAssets() public view override returns (uint256) {
        uint256 assets = super.totalAssets();
        
        // Calculate pending management fee
        if (block.timestamp > lastFeeCollectionTimestamp && assets > 0) {
            uint256 timeElapsed = block.timestamp - lastFeeCollectionTimestamp;
            uint256 pendingFee = assets * managementFee * timeElapsed / (FEE_DENOMINATOR * 31536000);
            
            // Subtract pending fee from total assets
            if (pendingFee < assets) {
                assets -= pendingFee;
            }
        }
        
        return assets;
    }
    
    /**
     * @dev Get time until deposit cooldown expires
     * @param account Account to check
     * @return Time in seconds until deposit cooldown expires, 0 if already expired
     */
    function timeUntilDepositCooldownExpires(address account) external view returns (uint256) {
        if (depositCooldown == 0) {
            return 0;
        }
        
        uint256 cooldownEnd = lastDepositTimestamp[account] + depositCooldown;
        if (block.timestamp >= cooldownEnd) {
            return 0;
        }
        
        return cooldownEnd - block.timestamp;
    }
    
    /**
     * @dev Get time until withdrawal cooldown expires
     * @param account Account to check
     * @return Time in seconds until withdrawal cooldown expires, 0 if already expired
     */
    function timeUntilWithdrawalCooldownExpires(address account) external view returns (uint256) {
        if (withdrawalCooldown == 0) {
            return 0;
        }
        
        uint256 cooldownEnd = lastWithdrawalTimestamp[account] + withdrawalCooldown;
        if (block.timestamp >= cooldownEnd) {
            return 0;
        }
        
        return cooldownEnd - block.timestamp;
    }
}