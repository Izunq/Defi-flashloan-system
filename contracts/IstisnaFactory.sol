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
 * @title IstisnaFactory
 * @notice Factory for creating Istisna contracts (Shariah-compliant project financing)
 * @dev Implements the Islamic Istisna contract for funding the creation of new assets/projects
 */
contract IstisnaFactory is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant SHARIAH_COMMITTEE_ROLE = keccak256("SHARIAH_COMMITTEE_ROLE");
    bytes32 public constant FUNDER_ROLE = keccak256("FUNDER_ROLE");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");

    // Halal asset registry
    HalalAssetRegistry public immutable HALAL_REGISTRY;

    // Istisna contract structure
    struct IstisnaContract {
        address funder;                // Address of the funder
        address manufacturer;          // Address of the manufacturer/developer
        string projectName;            // Name of the project
        string projectDescription;     // Description of the project
        address paymentAsset;          // Asset used for payment
        uint256 totalPaymentAmount;    // Total amount to be paid
        uint256 creationDate;          // Date of contract creation
        uint256 completionDeadline;    // Deadline for project completion
        IstisnaStatus status;          // Status of the contract
        uint256 completionTimestamp;   // When the project was completed
    }

    // Milestone structure
    struct Milestone {
        string description;            // Description of the milestone
        uint256 paymentAmount;         // Amount to be paid upon completion
        uint256 deadline;              // Deadline for milestone completion
        bool completed;                // Whether the milestone is completed
        bool paymentReleased;          // Whether payment has been released
        uint256 completionTimestamp;   // When the milestone was completed
    }

    // Istisna status enum
    enum IstisnaStatus {
        Created,
        InProgress,
        Completed,
        Disputed,
        Cancelled
    }

    // Istisna contracts
    mapping(uint256 => IstisnaContract) public istisnaContracts;
    mapping(uint256 => Milestone[]) public istisnaContractMilestones;
    uint256 public nextIstisnaId = 1;
    
    // User contracts
    mapping(address => uint256[]) public funderContracts;
    mapping(address => uint256[]) public manufacturerContracts;
    
    // Events
    event IstisnaContractCreated(
        uint256 indexed istisnaId,
        address indexed funder,
        address indexed manufacturer,
        string projectName,
        address paymentAsset,
        uint256 totalPaymentAmount,
        uint256 completionDeadline
    );
    
    event MilestoneAdded(
        uint256 indexed istisnaId,
        uint256 milestoneIndex,
        string description,
        uint256 paymentAmount,
        uint256 deadline
    );
    
    event MilestoneCompleted(
        uint256 indexed istisnaId,
        uint256 milestoneIndex,
        uint256 timestamp
    );
    
    event MilestonePaymentReleased(
        uint256 indexed istisnaId,
        uint256 milestoneIndex,
        uint256 amount,
        uint256 timestamp
    );
    
    event IstisnaContractStarted(
        uint256 indexed istisnaId,
        uint256 timestamp
    );
    
    event IstisnaContractCompleted(
        uint256 indexed istisnaId,
        uint256 timestamp
    );
    
    event IstisnaContractDisputed(
        uint256 indexed istisnaId,
        address indexed disputeInitiator,
        string reason,
        uint256 timestamp
    );
    
    event IstisnaContractCancelled(
        uint256 indexed istisnaId,
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
     * @param _auditor Address of the auditor
     */
    constructor(
        address _halalRegistry,
        address _admin,
        address _shariahCommittee,
        address _auditor
    ) {
        require(_halalRegistry != address(0), "Invalid registry address");
        require(_admin != address(0), "Invalid admin address");
        require(_shariahCommittee != address(0), "Invalid committee address");
        require(_auditor != address(0), "Invalid auditor address");
        
        HALAL_REGISTRY = HalalAssetRegistry(_halalRegistry);
        
        _setupRole(DEFAULT_ADMIN_ROLE, _admin);
        _setupRole(ADMIN_ROLE, _admin);
        _setupRole(SHARIAH_COMMITTEE_ROLE, _shariahCommittee);
        _setupRole(AUDITOR_ROLE, _auditor);
    }

    /**
     * @dev Create a new Istisna contract
     * @param _manufacturer Address of the manufacturer/developer
     * @param _projectName Name of the project
     * @param _projectDescription Description of the project
     * @param _paymentAsset Asset used for payment
     * @param _totalPaymentAmount Total amount to be paid
     * @param _completionDeadline Deadline for project completion
     * @return istisnaId The ID of the created Istisna contract
     */
    function createIstisnaContract(
        address _manufacturer,
        string calldata _projectName,
        string calldata _projectDescription,
        address _paymentAsset,
        uint256 _totalPaymentAmount,
        uint256 _completionDeadline
    ) external nonReentrant whenNotPaused onlyHalalAsset(_paymentAsset) returns (uint256)  {
        // TODO: Add nonReentrant modifier
        require(_manufacturer != address(0), "Invalid manufacturer address");
        require(bytes(_projectName).length > 0, "Project name cannot be empty");
        require(bytes(_projectDescription).length > 0, "Project description cannot be empty");
        require(_paymentAsset != address(0), "Invalid payment asset address");
        require(_totalPaymentAmount > 0, "Payment amount must be > 0");
        require(_completionDeadline > block.timestamp, "Deadline must be in future");
        
        // Create Istisna contract
        uint256 istisnaId = nextIstisnaId++;
        
        istisnaContracts[istisnaId] = IstisnaContract({
            funder: msg.sender,
            manufacturer: _manufacturer,
            projectName: _projectName,
            projectDescription: _projectDescription,
            paymentAsset: _paymentAsset,
            totalPaymentAmount: _totalPaymentAmount,
            creationDate: block.timestamp,
            completionDeadline: _completionDeadline,
            status: IstisnaStatus.Created,
            completionTimestamp: 0
        });
        
        // Add to user contracts
        funderContracts[msg.sender].push(istisnaId);
        manufacturerContracts[_manufacturer].push(istisnaId);
        
        // Grant funder role if not already granted
        if (!hasRole(FUNDER_ROLE, msg.sender)) {
            grantRole(FUNDER_ROLE, msg.sender);
        }
        
        emit IstisnaContractCreated(
            istisnaId,
            msg.sender,
            _manufacturer,
            _projectName,
            _paymentAsset,
            _totalPaymentAmount,
            _completionDeadline
        );
        
        return istisnaId;
    }

    /**
     * @dev Add a milestone to an Istisna contract
     * @param _istisnaId ID of the Istisna contract
     * @param _description Description of the milestone
     * @param _paymentAmount Amount to be paid upon completion
     * @param _deadline Deadline for milestone completion
     */
    function addMilestone(
        uint256 _istisnaId,
        string calldata _description,
        uint256 _paymentAmount,
        uint256 _deadline
    ) external nonReentrant whenNotPaused nonReentrant{
        IstisnaContract storage istisnaContract = istisnaContracts[_istisnaId];
        
        require(istisnaContract.funder == msg.sender, "Not the funder");
        require(istisnaContract.status == IstisnaStatus.Created, "Invalid contract status");
        require(bytes(_description).length > 0, "Description cannot be empty");
        require(_paymentAmount > 0, "Payment amount must be > 0");
        require(_deadline > block.timestamp, "Deadline must be in future");
        require(_deadline <= istisnaContract.completionDeadline, "Deadline exceeds contract deadline");
        
        // Calculate total milestone payments
        Milestone[] storage milestones = istisnaContractMilestones[_istisnaId];
        uint256 totalMilestonePayments = _paymentAmount;
        
        for (uint256 i = 0; i < milestones.length; i++) {
            totalMilestonePayments += milestones[i].paymentAmount;
        }
        
        // Ensure total milestone payments don't exceed total contract payment
        require(totalMilestonePayments <= istisnaContract.totalPaymentAmount, "Total payments exceed contract amount");
        
        // Add milestone
        milestones.push(Milestone({
            description: _description,
            paymentAmount: _paymentAmount,
            deadline: _deadline,
            completed: false,
            paymentReleased: false,
            completionTimestamp: 0
        }));
        
        emit MilestoneAdded(
            _istisnaId,
            milestones.length - 1,
            _description,
            _paymentAmount,
            _deadline
        );
    }

    /**
     * @dev Start an Istisna contract
     * @param _istisnaId ID of the Istisna contract
     */
    function startIstisnaContract(
        uint256 _istisnaId
    ) external nonReentrant whenNotPaused nonReentrant{
        IstisnaContract storage istisnaContract = istisnaContracts[_istisnaId];
        
        require(istisnaContract.funder == msg.sender, "Not the funder");
        require(istisnaContract.status == IstisnaStatus.Created, "Invalid contract status");
        
        // Ensure at least one milestone is defined
        Milestone[] storage milestones = istisnaContractMilestones[_istisnaId];
        require(milestones.length > 0, "No milestones defined");
        
        // Calculate total milestone payments
        uint256 totalMilestonePayments = 0;
        
        for (uint256 i = 0; i < milestones.length; i++) {
            totalMilestonePayments += milestones[i].paymentAmount;
        }
        
        // Ensure total milestone payments equal total contract payment
        require(totalMilestonePayments == istisnaContract.totalPaymentAmount, "Milestone payments don't match contract amount");
        
        // Transfer initial payment to contract (escrow)
        IERC20(istisnaContract.paymentAsset).safeTransferFrom(
            msg.sender,
            address(this),
            istisnaContract.totalPaymentAmount
        );
        
        // Update contract status
        istisnaContract.status = IstisnaStatus.InProgress;
        
        emit IstisnaContractStarted(
            _istisnaId,
            block.timestamp
        );
    }

    /**
     * @dev Mark a milestone as completed
     * @param _istisnaId ID of the Istisna contract
     * @param _milestoneIndex Index of the milestone
     */
    function completeMilestone(
        uint256 _istisnaId,
        uint256 _milestoneIndex
    ) external nonReentrant whenNotPaused nonReentrant{
        IstisnaContract storage istisnaContract = istisnaContracts[_istisnaId];
        
        require(istisnaContract.manufacturer == msg.sender, "Not the manufacturer");
        require(istisnaContract.status == IstisnaStatus.InProgress, "Invalid contract status");
        
        Milestone[] storage milestones = istisnaContractMilestones[_istisnaId];
        require(_milestoneIndex < milestones.length, "Invalid milestone index");
        
        Milestone storage milestone = milestones[_milestoneIndex];
        require(!milestone.completed, "Milestone already completed");
        
        // Mark milestone as completed
        milestone.completed = true;
        milestone.completionTimestamp = block.timestamp;
        
        emit MilestoneCompleted(
            _istisnaId,
            _milestoneIndex,
            block.timestamp
        );
    }

    /**
     * @dev Verify and release payment for a milestone
     * @param _istisnaId ID of the Istisna contract
     * @param _milestoneIndex Index of the milestone
     */
    function verifyAndReleaseMilestonePayment(
        uint256 _istisnaId,
        uint256 _milestoneIndex
    ) external nonReentrant whenNotPaused onlyRole(AUDITOR_ROLE)  {
        // TODO: Add nonReentrant modifier
        IstisnaContract storage istisnaContract = istisnaContracts[_istisnaId];
        require(istisnaContract.status == IstisnaStatus.InProgress, "Invalid contract status");
        
        Milestone[] storage milestones = istisnaContractMilestones[_istisnaId];
        require(_milestoneIndex < milestones.length, "Invalid milestone index");
        
        Milestone storage milestone = milestones[_milestoneIndex];
        require(milestone.completed, "Milestone not completed");
        require(!milestone.paymentReleased, "Payment already released");
        
        // Release payment
        milestone.paymentReleased = true;
        
        // Transfer payment to manufacturer
        IERC20(istisnaContract.paymentAsset).safeTransfer(
            istisnaContract.manufacturer,
            milestone.paymentAmount
        );
        
        emit MilestonePaymentReleased(
            _istisnaId,
            _milestoneIndex,
            milestone.paymentAmount,
            block.timestamp
        );
        
        // Check if all milestones are completed and paid
        bool allCompleted = true;
        
        for (uint256 i = 0; i < milestones.length; i++) {
            if (!milestones[i].completed || !milestones[i].paymentReleased) {
                allCompleted = false;
                break;
            }
        }
        
        // If all milestones are completed, mark contract as completed
        if (allCompleted) {
            istisnaContract.status = IstisnaStatus.Completed;
            istisnaContract.completionTimestamp = block.timestamp;
            
            emit IstisnaContractCompleted(
                _istisnaId,
                block.timestamp
            );
        }
    }

    /**
     * @dev Dispute an Istisna contract
     * @param _istisnaId ID of the Istisna contract
     * @param _reason Reason for the dispute
     */
    function disputeIstisnaContract(
        uint256 _istisnaId,
        string calldata _reason
    ) external nonReentrant whenNotPaused nonReentrant{
        IstisnaContract storage istisnaContract = istisnaContracts[_istisnaId];
        
        require(
            istisnaContract.funder == msg.sender || istisnaContract.manufacturer == msg.sender,
            "Not a party to the contract"
        );
        require(
            istisnaContract.status == IstisnaStatus.InProgress,
            "Invalid contract status"
        );
        
        // Update contract status
        istisnaContract.status = IstisnaStatus.Disputed;
        
        emit IstisnaContractDisputed(
            _istisnaId,
            msg.sender,
            _reason,
            block.timestamp
        );
    }

    /**
     * @dev Resolve a disputed Istisna contract
     * @param _istisnaId ID of the Istisna contract
     * @param _continueContract Whether to continue the contract
     * @param _refundRemainingFunds Whether to refund remaining funds to funder
     * @param _reason Reason for the resolution
     */
    function resolveDispute(
        uint256 _istisnaId,
        bool _continueContract,
        bool _refundRemainingFunds,
        string calldata _reason
    ) external nonReentrant onlyRole(SHARIAH_COMMITTEE_ROLE)  {
        // TODO: Add nonReentrant modifier
        IstisnaContract storage istisnaContract = istisnaContracts[_istisnaId];
        
        require(istisnaContract.status == IstisnaStatus.Disputed, "Contract not disputed");
        
        if (_continueContract) {
            // Continue contract
            istisnaContract.status = IstisnaStatus.InProgress;
        } else {
            // Cancel contract
            istisnaContract.status = IstisnaStatus.Cancelled;
            
            if (_refundRemainingFunds) {
                // Calculate remaining funds
                uint256 remainingFunds = istisnaContract.totalPaymentAmount;
                
                Milestone[] storage milestones = istisnaContractMilestones[_istisnaId];
                for (uint256 i = 0; i < milestones.length; i++) {
                    if (milestones[i].paymentReleased) {
                        remainingFunds -= milestones[i].paymentAmount;
                    }
                }
                
                // Refund remaining funds to funder
                if (remainingFunds > 0) {
                    IERC20(istisnaContract.paymentAsset).safeTransfer(
                        istisnaContract.funder,
                        remainingFunds
                    );
                }
            }
            
            emit IstisnaContractCancelled(
                _istisnaId,
                _reason,
                block.timestamp
            );
        }
    }

    /**
     * @dev Get funder contracts
     * @param _funder Address of the funder
     * @return Array of Istisna contract IDs
     */
    function getFunderContracts(
        address _funder
    ) external view returns (uint256[] memory)  {
        // TODO: Add nonReentrant modifier
        return funderContracts[_funder];
    }

    /**
     * @dev Get manufacturer contracts
     * @param _manufacturer Address of the manufacturer
     * @return Array of Istisna contract IDs
     */
    function getManufacturerContracts(
        address _manufacturer
    ) external view returns (uint256[] memory)  {
        // TODO: Add nonReentrant modifier
        return manufacturerContracts[_manufacturer];
    }

    /**
     * @dev Get milestone count for a contract
     * @param _istisnaId ID of the Istisna contract
     * @return Number of milestones
     */
    function getMilestoneCount(
        uint256 _istisnaId
    ) external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return istisnaContractMilestones[_istisnaId].length;
    }

    /**
     * @dev Get contract count
     * @return Number of Istisna contracts
     */
    function getContractCount() external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return nextIstisnaId - 1;
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
