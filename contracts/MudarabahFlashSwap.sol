// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "./HalalAssetRegistry.sol";
import "./interfaces/IFlashLoanSimpleReceiver.sol";
import "./interfaces/IMudarabahFlashSwap.sol";

/**
 * @title MudarabahFlashSwap
 * @notice Shariah-compliant alternative to flash loans based on Mudarabah (profit-sharing) principles
 * @dev This contract implements a halal flash swap mechanism where fees are only charged on profitable trades
 */
contract MudarabahFlashSwap is AccessControl, ReentrancyGuard, Pausable, IFlashLoanSimpleReceiver {
    using SafeERC20 for IERC20;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant CAPITAL_PROVIDER_ROLE = keccak256("CAPITAL_PROVIDER_ROLE");
    bytes32 public constant MUDARIB_ROLE = keccak256("MUDARIB_ROLE"); // Manager role
    bytes32 public constant TIMELOCK_ADMIN_ROLE = keccak256("TIMELOCK_ADMIN_ROLE");

    // Halal asset registry
    HalalAssetRegistry public immutable HALAL_REGISTRY;

    // Profit sharing ratio (in basis points)
    uint256 public capitalProviderShare = 8000; // 80% to capital providers
    uint256 public mudaribShare = 2000; // 20% to the protocol (mudarib)

    // Capital pool tracking
    mapping(address => uint256) public assetPoolSize; // token => total pool size
    mapping(address => uint256) public assetPoolUtilization; // token => current utilization
    mapping(address => uint256) public totalProfitGenerated; // token => total profit
    mapping(address => uint256) public totalTransactionsExecuted; // token => transaction count

    // Capital provider tracking
    mapping(address => mapping(address => uint256)) public providerDeposits; // provider => token => amount
    mapping(address => mapping(address => uint256)) public providerProfitShare; // provider => token => profit share

    // Mudarib (protocol) profit tracking
    address public mudaribTreasury;
    mapping(address => uint256) public mudaribProfitShare; // token => profit share
    
    // Multi-signature requirements
    uint256 public constant REQUIRED_SIGNATURES = 2; // Require 2 signatures for admin actions
    mapping(bytes32 => mapping(address => bool)) public adminSignatures; // operation hash => admin => has signed
    mapping(bytes32 => uint256) public signatureCount; // operation hash => number of signatures
    mapping(bytes32 => uint256) public operationTimestamps; // operation hash => timestamp when operation was proposed
    
    // Timelock for critical parameter changes
    uint256 public constant TIMELOCK_PERIOD = 24 hours;
    mapping(bytes32 => uint256) public timelockExpirations; // operation hash => expiration timestamp
    
    // Reentrancy guard state
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;
    uint256 private _status;

    // Transaction tracking
    struct MudarabahTransaction {
        address mudarib; // The manager executing the transaction
        address token; // The token being used
        uint256 amount; // The amount being used
        uint256 profitGenerated; // Profit generated from the transaction
        uint256 capitalProviderProfit; // Profit share for capital providers
        uint256 mudaribProfit; // Profit share for the mudarib
        uint256 timestamp; // When the transaction was executed
        bool successful; // Whether the transaction was successful
    }

    // Transaction history
    MudarabahTransaction[] public transactions;
    mapping(address => uint256[]) public mudaribTransactions; // mudarib => transaction indices
    
    // Events
    event CapitalDeposited(address indexed provider, address indexed token, uint256 amount);
    event CapitalWithdrawn(address indexed provider, address indexed token, uint256 amount);
    event MudarabahExecuted(
        uint256 indexed transactionId,
        address indexed mudarib,
        address indexed token,
        uint256 amount,
        uint256 profit,
        uint256 capitalProviderShare,
        uint256 mudaribShare
    );
    event ProfitShareUpdated(uint256 capitalProviderShare, uint256 mudaribShare);
    event MudaribTreasuryUpdated(address previousTreasury, address newTreasury);
    event ProfitWithdrawn(address indexed recipient, address indexed token, uint256 amount, bool isMudarib);
    
    // Multi-signature and timelock events
    event OperationProposed(bytes32 indexed operationId, string operation, address proposer);
    event OperationSigned(bytes32 indexed operationId, address signer);
    event OperationExecuted(bytes32 indexed operationId, string operation);
    event OperationCancelled(bytes32 indexed operationId, string operation);
    event TimelockInitiated(bytes32 indexed operationId, string operation, uint256 executeAfter);
    event TimelockExecuted(bytes32 indexed operationId, string operation);
    event TimelockCancelled(bytes32 indexed operationId, string operation);

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
     * @param _mudaribTreasury Address of the treasury to collect mudarib profit share
     * @param _admin Address of the admin
     * @param _secondAdmin Address of the second admin for multi-sig
     */
    constructor(
        address _halalRegistry,
        address _mudaribTreasury,
        address _admin,
        address _secondAdmin
    ) {
        require(_halalRegistry != address(0), "Invalid registry address");
        require(_mudaribTreasury != address(0), "Invalid treasury address");
        require(_admin != address(0), "Invalid admin address");
        require(_secondAdmin != address(0), "Invalid second admin address");
        require(_admin != _secondAdmin, "Admins must be different");
        
        HALAL_REGISTRY = HalalAssetRegistry(_halalRegistry);
        mudaribTreasury = _mudaribTreasury;
        
        // Initialize reentrancy guard
        _status = _NOT_ENTERED;
        
        // Setup roles
        _setupRole(DEFAULT_ADMIN_ROLE, _admin);
        _setupRole(ADMIN_ROLE, _admin);
        _setupRole(ADMIN_ROLE, _secondAdmin);
        _setupRole(MUDARIB_ROLE, _admin);
        _setupRole(TIMELOCK_ADMIN_ROLE, _admin);
        _setupRole(TIMELOCK_ADMIN_ROLE, _secondAdmin);
    }

    /**
     * @dev Deposit capital into the Mudarabah pool
     * @param token The token to deposit
     * @param amount The amount to deposit
     */
    function depositCapital(
        address token,
        uint256 amount
    ) external nonReentrant whenNotPaused onlyHalalAsset(token) {
        require(amount > 0, "Amount must be greater than 0");
        
        // Transfer tokens from sender to contract
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);
        
        // Update capital provider's deposit
        providerDeposits[msg.sender][token] += amount;
        
        // Update pool size
        assetPoolSize[token] += amount;
        
        // Grant capital provider role if not already granted
        if (!hasRole(CAPITAL_PROVIDER_ROLE, msg.sender)) {
            _setupRole(CAPITAL_PROVIDER_ROLE, msg.sender);
        }
        
        emit CapitalDeposited(msg.sender, token, amount);
    }

    /**
     * @dev Withdraw capital from the Mudarabah pool
     * @param token The token to withdraw
     * @param amount The amount to withdraw
     */
    function withdrawCapital(
        address token,
        uint256 amount
    ) external nonReentrant onlyRole(CAPITAL_PROVIDER_ROLE) {
        require(amount > 0, "Amount must be greater than 0");
        require(providerDeposits[msg.sender][token] >= amount, "Insufficient deposit");
        
        // Ensure there's enough available capital (not currently in use)
        uint256 availableCapital = assetPoolSize[token] - assetPoolUtilization[token];
        require(availableCapital >= amount, "Insufficient available capital");
        
        // Update capital provider's deposit
        providerDeposits[msg.sender][token] -= amount;
        
        // Update pool size
        assetPoolSize[token] -= amount;
        
        // Transfer tokens to sender
        IERC20(token).safeTransfer(msg.sender, amount);
        
        emit CapitalWithdrawn(msg.sender, token, amount);
    }

    /**
     * @dev Custom reentrancy guard modifier
     */
    modifier nonReentrantCustom() {
        // On the first call to nonReentrant, _status will be _NOT_ENTERED
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");

        // Any calls to nonReentrant after this point will fail
        _status = _ENTERED;

        _;

        // By storing the original value once again, a refund is triggered (see
        // https://eips.ethereum.org/EIPS/eip-2200)
        _status = _NOT_ENTERED;
    }
    
    /**
     * @dev Execute a Mudarabah flash swap
     * @param token The token to use for the transaction
     * @param amount The amount to borrow
     * @param data The execution data
     */
    function executeMudarabah(
        address token,
        uint256 amount,
        bytes calldata data
    ) external nonReentrantCustom whenNotPaused onlyRole(MUDARIB_ROLE) onlyHalalAsset(token) {
        require(amount > 0, "Amount must be greater than 0");
        require(assetPoolSize[token] >= amount, "Insufficient pool size");
        require(assetPoolSize[token] - assetPoolUtilization[token] >= amount, "Insufficient available capital");
        
        // Update state before external calls (checks-effects-interactions pattern)
        assetPoolUtilization[token] += amount;
        
        // Record initial balance to calculate profit
        uint256 initialBalance = IERC20(token).balanceOf(address(this));
        
        // Create transaction record
        uint256 transactionId = transactions.length;
        transactions.push(MudarabahTransaction({
            mudarib: msg.sender,
            token: token,
            amount: amount,
            profitGenerated: 0,
            capitalProviderProfit: 0,
            mudaribProfit: 0,
            timestamp: block.timestamp,
            successful: false
        }));
        
        mudaribTransactions[msg.sender].push(transactionId);
        
        // Transfer tokens to mudarib (external interaction)
        IERC20(token).safeTransfer(msg.sender, amount);
        
        // Call the mudarib with the data (external interaction)
        (bool success, ) = msg.sender.call(data);
        require(success, "Mudarib execution failed");
        
        // Calculate profit
        uint256 finalBalance = IERC20(token).balanceOf(address(this));
        
        // Update utilization (state update)
        assetPoolUtilization[token] -= amount;
        
        // Check if the transaction was profitable
        if (finalBalance > initialBalance) {
            // Calculate profit
            uint256 profit = finalBalance - initialBalance;
            
            // Calculate profit shares
            uint256 capitalProviderProfit = (profit * capitalProviderShare) / 10000;
            uint256 mudaribProfit = profit - capitalProviderProfit;
            
            // Update profit tracking (state updates)
            totalProfitGenerated[token] += profit;
            mudaribProfitShare[token] += mudaribProfit;
            
            // Update transaction record (state updates)
            transactions[transactionId].profitGenerated = profit;
            transactions[transactionId].capitalProviderProfit = capitalProviderProfit;
            transactions[transactionId].mudaribProfit = mudaribProfit;
            transactions[transactionId].successful = true;
            
            // Distribute capital provider profit proportionally
            _distributeCapitalProviderProfit(token, capitalProviderProfit);
            
            emit MudarabahExecuted(
                transactionId,
                msg.sender,
                token,
                amount,
                profit,
                capitalProviderProfit,
                mudaribProfit
            );
        } else {
            // No profit, just mark as successful (state update)
            transactions[transactionId].successful = true;
            
            emit MudarabahExecuted(
                transactionId,
                msg.sender,
                token,
                amount,
                0,
                0,
                0
            );
        }
        
        // Update transaction count (state update)
        totalTransactionsExecuted[token]++;
    }
    
    /**
     * @dev Implements the Aave V3 flash loan callback
     * @param asset The address of the flash-borrowed asset
     * @param amount The amount of the flash-borrowed asset
     * @param premium The fee of the flash-borrowed asset
     * @param initiator The address of the flash loan initiator
     * @param params Encoded parameters for the operation
     * @return True if the operation is successful
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override nonReentrantCustom whenNotPaused returns (bool) {
        // Verify the caller is a trusted lending pool
        require(hasRole(ADMIN_ROLE, initiator), "Initiator not authorized");
        
        // Decode the parameters
        (address recipient, bytes memory executionData) = abi.decode(params, (address, bytes));
        
        // Verify recipient has MUDARIB_ROLE
        require(hasRole(MUDARIB_ROLE, recipient), "Recipient not authorized as mudarib");
        
        // Record initial balance to calculate profit
        uint256 initialBalance = IERC20(asset).balanceOf(address(this));
        
        // Create transaction record
        uint256 transactionId = transactions.length;
        transactions.push(MudarabahTransaction({
            mudarib: recipient,
            token: asset,
            amount: amount,
            profitGenerated: 0,
            capitalProviderProfit: 0,
            mudaribProfit: 0,
            timestamp: block.timestamp,
            successful: false
        }));
        
        mudaribTransactions[recipient].push(transactionId);
        
        // Transfer tokens to the recipient
        IERC20(asset).safeTransfer(recipient, amount);
        
        // Execute the mudarabah operation
        (bool success, uint256 actualProfit) = IMudarabahFlashSwap(recipient).executeMudarabahOperation(
            asset,
            amount,
            premium,
            initiator,
            executionData
        );
        require(success, "Mudarabah operation failed");
        
        // Calculate final balance
        uint256 finalBalance = IERC20(asset).balanceOf(address(this));
        
        // Ensure we have enough to repay the loan
        require(finalBalance >= initialBalance + premium, "Insufficient funds to repay flash loan");
        
        // Calculate profit (if any)
        uint256 profit = 0;
        if (finalBalance > initialBalance + premium) {
            profit = finalBalance - initialBalance - premium;
        }
        
        // Calculate profit shares
        uint256 capitalProviderProfit = (profit * capitalProviderShare) / 10000;
        uint256 mudaribProfit = profit - capitalProviderProfit;
        
        // Update profit tracking
        totalProfitGenerated[asset] += profit;
        mudaribProfitShare[asset] += mudaribProfit;
        
        // Update transaction record
        transactions[transactionId].profitGenerated = profit;
        transactions[transactionId].capitalProviderProfit = capitalProviderProfit;
        transactions[transactionId].mudaribProfit = mudaribProfit;
        transactions[transactionId].successful = true;
        
        // Distribute capital provider profit proportionally
        if (capitalProviderProfit > 0) {
            _distributeCapitalProviderProfit(asset, capitalProviderProfit);
        }
        
        // Approve the lending pool to pull the repayment amount
        IERC20(asset).safeApprove(msg.sender, amount + premium);
        
        emit MudarabahExecuted(
            transactionId,
            recipient,
            asset,
            amount,
            profit,
            capitalProviderProfit,
            mudaribProfit
        );
        
        // Update transaction count
        totalTransactionsExecuted[asset]++;
        
        return true;
    }

    /**
     * @dev Distribute profit to capital providers proportionally
     * @param token The token to distribute
     * @param profit The profit amount to distribute
     */
    function _distributeCapitalProviderProfit(
        address token,
        uint256 profit
    ) internal {
        if (profit == 0 || assetPoolSize[token] == 0) {
            return;
        }
        
        // Get all accounts with the CAPITAL_PROVIDER_ROLE
        uint256 roleCount = getRoleMemberCount(CAPITAL_PROVIDER_ROLE);
        
        for (uint256 i = 0; i < roleCount; i++) {
            address provider = getRoleMember(CAPITAL_PROVIDER_ROLE, i);
            uint256 providerDeposit = providerDeposits[provider][token];
            
            if (providerDeposit > 0) {
                // Calculate proportional profit share
                uint256 providerProfit = (profit * providerDeposit) / assetPoolSize[token];
                
                // Update provider's profit share
                providerProfitShare[provider][token] += providerProfit;
            }
        }
    }

    /**
     * @dev Withdraw profit share (for capital providers)
     * @param token The token to withdraw profit from
     */
    function withdrawProfitShare(
        address token
    ) external nonReentrant onlyRole(CAPITAL_PROVIDER_ROLE) {
        uint256 profitShare = providerProfitShare[msg.sender][token];
        require(profitShare > 0, "No profit to withdraw");
        
        // Reset profit share
        providerProfitShare[msg.sender][token] = 0;
        
        // Transfer profit to capital provider
        IERC20(token).safeTransfer(msg.sender, profitShare);
        
        emit ProfitWithdrawn(msg.sender, token, profitShare, false);
    }

    /**
     * @dev Withdraw mudarib profit share (for treasury)
     * @param token The token to withdraw profit from
     */
    function withdrawMudaribProfitShare(
        address token
    ) external nonReentrant onlyRole(ADMIN_ROLE) {
        uint256 profitShare = mudaribProfitShare[token];
        require(profitShare > 0, "No profit to withdraw");
        
        // Reset profit share
        mudaribProfitShare[token] = 0;
        
        // Transfer profit to treasury
        IERC20(token).safeTransfer(mudaribTreasury, profitShare);
        
        emit ProfitWithdrawn(mudaribTreasury, token, profitShare, true);
    }

    /**
     * @dev Propose a multi-signature operation
     * @param operation The operation description
     * @param operationData The operation data hash
     */
    function proposeOperation(
        string calldata operation,
        bytes32 operationData
    ) external onlyRole(ADMIN_ROLE) {
        bytes32 operationId = keccak256(abi.encodePacked(operation, operationData));
        
        // Ensure operation hasn't been proposed before or was cancelled
        require(operationTimestamps[operationId] == 0, "Operation already proposed");
        
        // Record proposal timestamp
        operationTimestamps[operationId] = block.timestamp;
        
        // First signature is from the proposer
        adminSignatures[operationId][msg.sender] = true;
        signatureCount[operationId] = 1;
        
        emit OperationProposed(operationId, operation, msg.sender);
        emit OperationSigned(operationId, msg.sender);
    }
    
    /**
     * @dev Sign a proposed operation
     * @param operationId The operation ID to sign
     */
    function signOperation(
        bytes32 operationId
    ) external onlyRole(ADMIN_ROLE) {
        // Ensure operation exists
        require(operationTimestamps[operationId] > 0, "Operation not proposed");
        
        // Ensure admin hasn't already signed
        require(!adminSignatures[operationId][msg.sender], "Already signed");
        
        // Record signature
        adminSignatures[operationId][msg.sender] = true;
        signatureCount[operationId]++;
        
        emit OperationSigned(operationId, msg.sender);
    }
    
    /**
     * @dev Cancel a proposed operation
     * @param operationId The operation ID to cancel
     * @param operation The operation description (for event)
     */
    function cancelOperation(
        bytes32 operationId,
        string calldata operation
    ) external onlyRole(ADMIN_ROLE) {
        // Ensure operation exists
        require(operationTimestamps[operationId] > 0, "Operation not proposed");
        
        // Reset operation data
        delete operationTimestamps[operationId];
        delete signatureCount[operationId];
        
        emit OperationCancelled(operationId, operation);
    }
    
    /**
     * @dev Initiate timelock for a critical operation
     * @param operation The operation description
     * @param operationData The operation data hash
     */
    function initiateTimelock(
        string calldata operation,
        bytes32 operationData
    ) external onlyRole(TIMELOCK_ADMIN_ROLE) {
        bytes32 operationId = keccak256(abi.encodePacked(operation, operationData));
        
        // Ensure timelock hasn't been initiated before
        require(timelockExpirations[operationId] == 0, "Timelock already initiated");
        
        // Set timelock expiration
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, operation, block.timestamp + TIMELOCK_PERIOD);
    }
    
    /**
     * @dev Cancel a timelock operation
     * @param operationId The operation ID to cancel
     * @param operation The operation description (for event)
     */
    function cancelTimelock(
        bytes32 operationId,
        string calldata operation
    ) external onlyRole(TIMELOCK_ADMIN_ROLE) {
        // Ensure timelock exists
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        
        // Reset timelock
        delete timelockExpirations[operationId];
        
        emit TimelockCancelled(operationId, operation);
    }
    
    /**
     * @dev Verify if an operation has enough signatures
     * @param operationId The operation ID to verify
     * @return True if the operation has enough signatures
     */
    function hasRequiredSignatures(
        bytes32 operationId
    ) public view returns (bool) {
        return signatureCount[operationId] >= REQUIRED_SIGNATURES;
    }
    
    /**
     * @dev Verify if a timelock has expired
     * @param operationId The operation ID to verify
     * @return True if the timelock has expired
     */
    function isTimelockExpired(
        bytes32 operationId
    ) public view returns (bool) {
        uint256 expiration = timelockExpirations[operationId];
        return expiration > 0 && block.timestamp >= expiration;
    }
    
    /**
     * @dev Update profit sharing ratio (requires multi-signature)
     * @param _capitalProviderShare New capital provider share (in basis points)
     * @param _mudaribShare New mudarib share (in basis points)
     */
    function updateProfitSharing(
        uint256 _capitalProviderShare,
        uint256 _mudaribShare
    ) external onlyRole(ADMIN_ROLE) {
        require(_capitalProviderShare + _mudaribShare == 10000, "Shares must total 100%");
        
        // Create operation ID
        bytes32 operationData = keccak256(abi.encodePacked(_capitalProviderShare, _mudaribShare));
        bytes32 operationId = keccak256(abi.encodePacked("updateProfitSharing", operationData));
        
        // Verify multi-signature requirement
        require(hasRequiredSignatures(operationId), "Insufficient signatures");
        
        // Verify timelock requirement
        require(isTimelockExpired(operationId), "Timelock not expired");
        
        // Update profit sharing ratio
        capitalProviderShare = _capitalProviderShare;
        mudaribShare = _mudaribShare;
        
        // Clean up
        delete operationTimestamps[operationId];
        delete signatureCount[operationId];
        delete timelockExpirations[operationId];
        
        emit ProfitShareUpdated(_capitalProviderShare, _mudaribShare);
        emit OperationExecuted(operationId, "updateProfitSharing");
        emit TimelockExecuted(operationId, "updateProfitSharing");
    }

    /**
     * @dev Update mudarib treasury address (requires multi-signature)
     * @param _mudaribTreasury New treasury address
     */
    function updateMudaribTreasury(
        address _mudaribTreasury
    ) external onlyRole(ADMIN_ROLE) {
        require(_mudaribTreasury != address(0), "Invalid treasury address");
        
        // Create operation ID
        bytes32 operationData = keccak256(abi.encodePacked(_mudaribTreasury));
        bytes32 operationId = keccak256(abi.encodePacked("updateMudaribTreasury", operationData));
        
        // Verify multi-signature requirement
        require(hasRequiredSignatures(operationId), "Insufficient signatures");
        
        // Verify timelock requirement
        require(isTimelockExpired(operationId), "Timelock not expired");
        
        // Update treasury address
        address oldTreasury = mudaribTreasury;
        mudaribTreasury = _mudaribTreasury;
        
        // Clean up
        delete operationTimestamps[operationId];
        delete signatureCount[operationId];
        delete timelockExpirations[operationId];
        
        emit MudaribTreasuryUpdated(oldTreasury, _mudaribTreasury);
        emit OperationExecuted(operationId, "updateMudaribTreasury");
        emit TimelockExecuted(operationId, "updateMudaribTreasury");
    }

    /**
     * @dev Grant mudarib role to an address
     * @param _mudarib Address to grant the role to
     */
    function grantMudaribRole(
        address _mudarib
    ) external onlyRole(ADMIN_ROLE) {
        require(_mudarib != address(0), "Invalid mudarib address");
        
        grantRole(MUDARIB_ROLE, _mudarib);
    }

    /**
     * @dev Revoke mudarib role from an address
     * @param _mudarib Address to revoke the role from
     */
    function revokeMudaribRole(
        address _mudarib
    ) external onlyRole(ADMIN_ROLE) {
        revokeRole(MUDARIB_ROLE, _mudarib);
    }

    /**
     * @dev Pause the contract (emergency)
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

    /**
     * @dev Get transaction count
     * @return Number of transactions
     */
    function getTransactionCount() external view returns (uint256) {
        return transactions.length;
    }

    /**
     * @dev Get mudarib transaction count
     * @param _mudarib Address of the mudarib
     * @return Number of transactions by the mudarib
     */
    function getMudaribTransactionCount(
        address _mudarib
    ) external view returns (uint256) {
        return mudaribTransactions[_mudarib].length;
    }

    /**
     * @dev Get mudarib transactions
     * @param _mudarib Address of the mudarib
     * @return Array of transaction IDs
     */
    function getMudaribTransactions(
        address _mudarib
    ) external view returns (uint256[] memory) {
        return mudaribTransactions[_mudarib];
    }
}