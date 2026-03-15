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
 * @title SalamFactory
 * @notice Factory for creating Salam contracts (Shariah-compliant forward contracts)
 * @dev Implements the Islamic Salam contract for future delivery of assets
 */
contract SalamFactory is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant SHARIAH_COMMITTEE_ROLE = keccak256("SHARIAH_COMMITTEE_ROLE");
    bytes32 public constant BUYER_ROLE = keccak256("BUYER_ROLE");

    // Halal asset registry
    HalalAssetRegistry public immutable HALAL_REGISTRY;

    // Salam contract structure
    struct SalamContract {
        address buyer;                 // Address of the buyer
        address seller;                // Address of the seller
        address assetToDeliver;        // Asset to be delivered
        uint256 quantityToDeliver;     // Quantity to be delivered
        address paymentAsset;          // Asset used for payment
        uint256 paymentAmount;         // Amount paid
        uint256 deliveryDate;          // Date of delivery
        uint256 creationDate;          // Date of contract creation
        SalamStatus status;            // Status of the contract
        bool buyerApproved;            // Whether the buyer has approved delivery
        bool sellerApproved;           // Whether the seller has approved delivery
        uint256 deliveryTimestamp;     // When the delivery was completed
    }

    // Salam status enum
    enum SalamStatus {
        Created,
        Paid,
        Delivered,
        Completed,
        Disputed,
        Cancelled
    }

    // Salam contracts
    mapping(uint256 => SalamContract) public salamContracts;
    uint256 public nextSalamId = 1;
    
    // User contracts
    mapping(address => uint256[]) public buyerContracts;
    mapping(address => uint256[]) public sellerContracts;
    
    // Events
    event SalamContractCreated(
        uint256 indexed salamId,
        address indexed buyer,
        address indexed seller,
        address assetToDeliver,
        uint256 quantityToDeliver,
        address paymentAsset,
        uint256 paymentAmount,
        uint256 deliveryDate
    );
    
    event SalamPaymentMade(
        uint256 indexed salamId,
        address indexed buyer,
        uint256 amount,
        uint256 timestamp
    );
    
    event SalamDeliveryInitiated(
        uint256 indexed salamId,
        address indexed seller,
        uint256 timestamp
    );
    
    event SalamDeliveryApproved(
        uint256 indexed salamId,
        address indexed approver,
        bool isBuyer,
        uint256 timestamp
    );
    
    event SalamContractCompleted(
        uint256 indexed salamId,
        uint256 timestamp
    );
    
    event SalamContractDisputed(
        uint256 indexed salamId,
        address indexed disputeInitiator,
        string reason,
        uint256 timestamp
    );
    
    event SalamContractCancelled(
        uint256 indexed salamId,
        string reason,
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
     */
    constructor(
        address _halalRegistry,
        address _admin,
        address _shariahCommittee
    ) {
        require(_halalRegistry != address(0), "Invalid registry address");
        require(_admin != address(0), "Invalid admin address");
        require(_shariahCommittee != address(0), "Invalid committee address");
        
        HALAL_REGISTRY = HalalAssetRegistry(_halalRegistry);
        
        _setupRole(DEFAULT_ADMIN_ROLE, _admin);
        _setupRole(ADMIN_ROLE, _admin);
        _setupRole(SHARIAH_COMMITTEE_ROLE, _shariahCommittee);
    }

    /**
     * @dev Create a new Salam contract
     * @param _seller Address of the seller
     * @param _assetToDeliver Asset to be delivered
     * @param _quantityToDeliver Quantity to be delivered
     * @param _paymentAsset Asset used for payment
     * @param _paymentAmount Amount to be paid
     * @param _deliveryDate Date of delivery
     * @return salamId The ID of the created Salam contract
     */
    function createSalamContract(
        address _seller,
        address _assetToDeliver,
        uint256 _quantityToDeliver,
        address _paymentAsset,
        uint256 _paymentAmount,
        uint256 _deliveryDate
    ) external nonReentrant whenNotPaused onlyHalalAsset(_assetToDeliver) onlyHalalAsset(_paymentAsset) returns (uint256)  {
        // TODO: Add nonReentrant modifier
        require(_seller != address(0), "Invalid seller address");
        require(_assetToDeliver != address(0), "Invalid asset address");
        require(_paymentAsset != address(0), "Invalid payment asset address");
        require(_quantityToDeliver > 0, "Quantity must be > 0");
        require(_paymentAmount > 0, "Payment amount must be > 0");
        require(_deliveryDate > block.timestamp, "Delivery date must be in future");
        
        // Create Salam contract
        uint256 salamId = nextSalamId++;
        
        salamContracts[salamId] = SalamContract({
            buyer: msg.sender,
            seller: _seller,
            assetToDeliver: _assetToDeliver,
            quantityToDeliver: _quantityToDeliver,
            paymentAsset: _paymentAsset,
            paymentAmount: _paymentAmount,
            deliveryDate: _deliveryDate,
            creationDate: block.timestamp,
            status: SalamStatus.Created,
            buyerApproved: false,
            sellerApproved: false,
            deliveryTimestamp: 0
        });
        
        // Add to user contracts
        buyerContracts[msg.sender].push(salamId);
        sellerContracts[_seller].push(salamId);
        
        // Grant buyer role if not already granted
        if (!hasRole(BUYER_ROLE, msg.sender)) {
            grantRole(BUYER_ROLE, msg.sender);
        }
        
        emit SalamContractCreated(
            salamId,
            msg.sender,
            _seller,
            _assetToDeliver,
            _quantityToDeliver,
            _paymentAsset,
            _paymentAmount,
            _deliveryDate
        );
        
        return salamId;
    }

    /**
     * @dev Make payment for a Salam contract
     * @param _salamId ID of the Salam contract
     */
    function makeSalamPayment(
        uint256 _salamId
    ) external nonReentrant whenNotPaused nonReentrant{
        SalamContract storage salamContract = salamContracts[_salamId];
        
        require(salamContract.buyer == msg.sender, "Not the buyer");
        require(salamContract.status == SalamStatus.Created, "Invalid contract status");
        
        // Transfer payment
        IERC20(salamContract.paymentAsset).safeTransferFrom(
            msg.sender,
            salamContract.seller,
            salamContract.paymentAmount
        );
        
        // Update contract status
        salamContract.status = SalamStatus.Paid;
        
        emit SalamPaymentMade(
            _salamId,
            msg.sender,
            salamContract.paymentAmount,
            block.timestamp
        );
    }

    /**
     * @dev Initiate delivery for a Salam contract
     * @param _salamId ID of the Salam contract
     */
    function initiateDelivery(
        uint256 _salamId
    ) external nonReentrant whenNotPaused nonReentrant{
        SalamContract storage salamContract = salamContracts[_salamId];
        
        require(salamContract.seller == msg.sender, "Not the seller");
        require(salamContract.status == SalamStatus.Paid, "Invalid contract status");
        
        // Transfer asset to contract
        IERC20(salamContract.assetToDeliver).safeTransferFrom(
            msg.sender,
            address(this),
            salamContract.quantityToDeliver
        );
        
        // Update contract status
        salamContract.status = SalamStatus.Delivered;
        salamContract.sellerApproved = true;
        salamContract.deliveryTimestamp = block.timestamp;
        
        emit SalamDeliveryInitiated(
            _salamId,
            msg.sender,
            block.timestamp
        );
    }

    /**
     * @dev Approve delivery for a Salam contract
     * @param _salamId ID of the Salam contract
     */
    function approveDelivery(
        uint256 _salamId
    ) external nonReentrant whenNotPaused nonReentrant{
        SalamContract storage salamContract = salamContracts[_salamId];
        
        require(salamContract.buyer == msg.sender, "Not the buyer");
        require(salamContract.status == SalamStatus.Delivered, "Invalid contract status");
        
        // Update contract status
        salamContract.buyerApproved = true;
        
        emit SalamDeliveryApproved(
            _salamId,
            msg.sender,
            true,
            block.timestamp
        );
        
        // If both parties have approved, complete the contract
        if (salamContract.buyerApproved && salamContract.sellerApproved) {
            _completeSalamContract(_salamId);
        }
    }

    /**
     * @dev Complete a Salam contract
     * @param _salamId ID of the Salam contract
     */
    function _completeSalamContract(
        uint256 _salamId
    ) internal {
        SalamContract storage salamContract = salamContracts[_salamId];
        
        // Transfer asset to buyer
        IERC20(salamContract.assetToDeliver).safeTransfer(
            salamContract.buyer,
            salamContract.quantityToDeliver
        );
        
        // Update contract status
        salamContract.status = SalamStatus.Completed;
        
        emit SalamContractCompleted(
            _salamId,
            block.timestamp
        );
    }

    /**
     * @dev Dispute a Salam contract
     * @param _salamId ID of the Salam contract
     * @param _reason Reason for the dispute
     */
    function disputeSalamContract(
        uint256 _salamId,
        string calldata _reason
    ) external nonReentrant whenNotPaused nonReentrant{
        SalamContract storage salamContract = salamContracts[_salamId];
        
        require(
            salamContract.buyer == msg.sender || salamContract.seller == msg.sender,
            "Not a party to the contract"
        );
        require(
            salamContract.status == SalamStatus.Paid || 
            salamContract.status == SalamStatus.Delivered,
            "Invalid contract status"
        );
        
        // Update contract status
        salamContract.status = SalamStatus.Disputed;
        
        emit SalamContractDisputed(
            _salamId,
            msg.sender,
            _reason,
            block.timestamp
        );
    }

    /**
     * @dev Resolve a disputed Salam contract
     * @param _salamId ID of the Salam contract
     * @param _refundBuyer Whether to refund the buyer
     * @param _reason Reason for the resolution
     */
    function resolveDispute(
        uint256 _salamId,
        bool _refundBuyer,
        string calldata _reason
    ) external nonReentrant onlyRole(SHARIAH_COMMITTEE_ROLE)  {
        // TODO: Add nonReentrant modifier
        SalamContract storage salamContract = salamContracts[_salamId];
        
        require(salamContract.status == SalamStatus.Disputed, "Contract not disputed");
        
        if (_refundBuyer) {
            // If delivery was initiated, return asset to seller
            if (salamContract.status == SalamStatus.Delivered) {
                IERC20(salamContract.assetToDeliver).safeTransfer(
                    salamContract.seller,
                    salamContract.quantityToDeliver
                );
            }
            
            // Cancel contract
            salamContract.status = SalamStatus.Cancelled;
            
            emit SalamContractCancelled(
                _salamId,
                _reason,
                block.timestamp
            );
        } else {
            // Complete contract
            if (salamContract.status == SalamStatus.Delivered) {
                _completeSalamContract(_salamId);
            } else {
                // If not delivered yet, revert to Paid status
                salamContract.status = SalamStatus.Paid;
            }
        }
    }

    /**
     * @dev Cancel a Salam contract by mutual agreement
     * @param _salamId ID of the Salam contract
     * @param _reason Reason for cancellation
     */
    function cancelSalamContract(
        uint256 _salamId,
        string calldata _reason
    ) external nonReentrant whenNotPaused nonReentrant{
        SalamContract storage salamContract = salamContracts[_salamId];
        
        require(
            salamContract.buyer == msg.sender || salamContract.seller == msg.sender,
            "Not a party to the contract"
        );
        require(
            salamContract.status == SalamStatus.Created || 
            salamContract.status == SalamStatus.Paid,
            "Invalid contract status"
        );
        
        // If paid, refund buyer
        if (salamContract.status == SalamStatus.Paid) {
            // This would require the seller to transfer the payment back
            // In a real implementation, this would be handled through an escrow
        }
        
        // Update contract status
        salamContract.status = SalamStatus.Cancelled;
        
        emit SalamContractCancelled(
            _salamId,
            _reason,
            block.timestamp
        );
    }

    /**
     * @dev Get buyer contracts
     * @param _buyer Address of the buyer
     * @return Array of Salam contract IDs
     */
    function getBuyerContracts(
        address _buyer
    ) external view returns (uint256[] memory)  {
        // TODO: Add nonReentrant modifier
        return buyerContracts[_buyer];
    }

    /**
     * @dev Get seller contracts
     * @param _seller Address of the seller
     * @return Array of Salam contract IDs
     */
    function getSellerContracts(
        address _seller
    ) external view returns (uint256[] memory)  {
        // TODO: Add nonReentrant modifier
        return sellerContracts[_seller];
    }

    /**
     * @dev Get contract count
     * @return Number of Salam contracts
     */
    function getContractCount() external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return nextSalamId - 1;
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
