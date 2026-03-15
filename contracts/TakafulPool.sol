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
 * @title TakafulPool
 * @notice Islamic cooperative insurance model for hedging against specific operational risks
 * @dev Implements Takaful principles of mutual protection and shared responsibility
 */
contract TakafulPool is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant SHARIAH_COMMITTEE_ROLE = keccak256("SHARIAH_COMMITTEE_ROLE");
    bytes32 public constant CLAIM_MANAGER_ROLE = keccak256("CLAIM_MANAGER_ROLE");
    bytes32 public constant PARTICIPANT_ROLE = keccak256("PARTICIPANT_ROLE");

    // Halal asset registry
    HalalAssetRegistry public immutable HALAL_REGISTRY;

    // Takaful pool structure
    struct TakafulInfo {
        string name;                   // Name of the Takaful pool
        string description;            // Description of the pool
        address contributionToken;     // Token used for contributions
        uint256 totalContributions;    // Total contributions to the pool
        uint256 totalClaims;           // Total claims paid out
        uint256 participantCount;      // Number of participants
        uint256 creationTime;          // When the pool was created
        uint256 minContribution;       // Minimum contribution amount
        bool active;                   // Whether the pool is active
    }

    // Participant structure
    struct Participant {
        uint256 totalContribution;     // Total contribution to the pool
        uint256 claimsPaid;            // Total claims paid to the participant
        uint256 lastContributionTime;  // When the participant last contributed
        bool active;                   // Whether the participant is active
    }

    // Claim structure
    struct Claim {
        address participant;           // Participant making the claim
        uint256 amount;                // Amount claimed
        string reason;                 // Reason for the claim
        string evidence;               // Evidence supporting the claim
        uint256 submissionTime;        // When the claim was submitted
        uint256 resolutionTime;        // When the claim was resolved
        ClaimStatus status;            // Status of the claim
        string rejectionReason;        // Reason for rejection (if applicable)
    }

    // Claim status enum
    enum ClaimStatus {
        Pending,
        Approved,
        Rejected,
        Paid
    }

    // Insurable event structure
    struct InsurableEvent {
        string name;                   // Name of the event
        string description;            // Description of the event
        bool covered;                  // Whether the event is covered
        uint256 maxCoverageAmount;     // Maximum coverage amount
    }

    // Pool state
    TakafulInfo public poolInfo;
    
    // Participant tracking
    mapping(address => Participant) public participants;
    address[] public participantList;
    
    // Claim tracking
    Claim[] public claims;
    mapping(address => uint256[]) public participantClaims;
    
    // Insurable events
    mapping(bytes32 => InsurableEvent) public insurableEvents;
    bytes32[] public insurableEventIds;
    
    // Surplus distribution
    uint256 public lastSurplusDistribution;
    uint256 public surplusDistributionPeriod = 180 days; // 6 months
    
    // Events
    event ParticipantJoined(
        address indexed participant,
        uint256 contribution,
        uint256 timestamp
    );
    
    event ContributionAdded(
        address indexed participant,
        uint256 amount,
        uint256 timestamp
    );
    
    event ClaimSubmitted(
        uint256 indexed claimId,
        address indexed participant,
        uint256 amount,
        string reason,
        uint256 timestamp
    );
    
    event ClaimResolved(
        uint256 indexed claimId,
        address indexed participant,
        uint256 amount,
        ClaimStatus status,
        uint256 timestamp
    );
    
    event ClaimPaid(
        uint256 indexed claimId,
        address indexed participant,
        uint256 amount,
        uint256 timestamp
    );
    
    event InsurableEventAdded(
        bytes32 indexed eventId,
        string name,
        uint256 maxCoverageAmount,
        uint256 timestamp
    );
    
    event InsurableEventUpdated(
        bytes32 indexed eventId,
        string name,
        uint256 maxCoverageAmount,
        bool covered,
        uint256 timestamp
    );
    
    event SurplusDistributed(
        uint256 totalSurplus,
        uint256 participantCount,
        uint256 timestamp
    );
    
    event PoolActivated(uint256 timestamp);
    event PoolDeactivated(uint256 timestamp);

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
     * @param _claimManager Address of the claim manager
     * @param _name Name of the Takaful pool
     * @param _description Description of the pool
     * @param _contributionToken Token used for contributions
     * @param _minContribution Minimum contribution amount
     */
    constructor(
        address _halalRegistry,
        address _admin,
        address _shariahCommittee,
        address _claimManager,
        string memory _name,
        string memory _description,
        address _contributionToken,
        uint256 _minContribution
    ) {
        require(_halalRegistry != address(0), "Invalid registry address");
        require(_admin != address(0), "Invalid admin address");
        require(_shariahCommittee != address(0), "Invalid committee address");
        require(_claimManager != address(0), "Invalid claim manager address");
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_description).length > 0, "Description cannot be empty");
        require(_contributionToken != address(0), "Invalid token address");
        require(_minContribution > 0, "Min contribution must be > 0");
        
        HALAL_REGISTRY = HalalAssetRegistry(_halalRegistry);
        
        // Setup roles
        _setupRole(DEFAULT_ADMIN_ROLE, _admin);
        _setupRole(ADMIN_ROLE, _admin);
        _setupRole(SHARIAH_COMMITTEE_ROLE, _shariahCommittee);
        _setupRole(CLAIM_MANAGER_ROLE, _claimManager);
        
        // Initialize pool info
        poolInfo = TakafulInfo({
            name: _name,
            description: _description,
            contributionToken: _contributionToken,
            totalContributions: 0,
            totalClaims: 0,
            participantCount: 0,
            creationTime: block.timestamp,
            minContribution: _minContribution,
            active: true
        });
    }

    /**
     * @dev Join the Takaful pool as a participant
     * @param _contribution Initial contribution amount
     */
    function joinPool(
        uint256 _contribution
    ) external nonReentrant whenNotPaused onlyHalalAsset(poolInfo.contributionToken)  {
        // TODO: Add nonReentrant modifier
        require(poolInfo.active, "Pool is not active");
        require(_contribution >= poolInfo.minContribution, "Contribution too low");
        require(!participants[msg.sender].active, "Already a participant");
        
        // Transfer contribution
        IERC20(poolInfo.contributionToken).safeTransferFrom(
            msg.sender,
            address(this),
            _contribution
        );
        
        // Create participant record
        participants[msg.sender] = Participant({
            totalContribution: _contribution,
            claimsPaid: 0,
            lastContributionTime: block.timestamp,
            active: true
        });
        
        // Add to participant list
        participantList.push(msg.sender);
        
        // Update pool info
        poolInfo.totalContributions += _contribution;
        poolInfo.participantCount++;
        
        // Grant participant role
        _setupRole(PARTICIPANT_ROLE, msg.sender);
        
        emit ParticipantJoined(msg.sender, _contribution, block.timestamp);
    }

    /**
     * @dev Add contribution to the Takaful pool
     * @param _contribution Contribution amount
     */
    function addContribution(
        uint256 _contribution
    ) external nonReentrant whenNotPaused onlyRole(PARTICIPANT_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(poolInfo.active, "Pool is not active");
        require(_contribution > 0, "Contribution must be > 0");
        require(participants[msg.sender].active, "Not an active participant");
        
        // Transfer contribution
        IERC20(poolInfo.contributionToken).safeTransferFrom(
            msg.sender,
            address(this),
            _contribution
        );
        
        // Update participant record
        participants[msg.sender].totalContribution += _contribution;
        participants[msg.sender].lastContributionTime = block.timestamp;
        
        // Update pool info
        poolInfo.totalContributions += _contribution;
        
        emit ContributionAdded(msg.sender, _contribution, block.timestamp);
    }

    /**
     * @dev Submit a claim
     * @param _amount Claim amount
     * @param _reason Reason for the claim
     * @param _evidence Evidence supporting the claim
     * @param _eventId ID of the insurable event
     * @return claimId The ID of the submitted claim
     */
    function submitClaim(
        uint256 _amount,
        string calldata _reason,
        string calldata _evidence,
        bytes32 _eventId
    ) external nonReentrant whenNotPaused onlyRole(PARTICIPANT_ROLE) returns (uint256)  {
        // TODO: Add nonReentrant modifier
        require(poolInfo.active, "Pool is not active");
        require(_amount > 0, "Claim amount must be > 0");
        require(bytes(_reason).length > 0, "Reason cannot be empty");
        require(participants[msg.sender].active, "Not an active participant");
        
        // Check if the event is covered
        InsurableEvent storage event_ = insurableEvents[_eventId];
        require(event_.covered, "Event not covered");
        require(_amount <= event_.maxCoverageAmount, "Amount exceeds coverage");
        
        // Create claim
        uint256 claimId = claims.length;
        claims.push(Claim({
            participant: msg.sender,
            amount: _amount,
            reason: _reason,
            evidence: _evidence,
            submissionTime: block.timestamp,
            resolutionTime: 0,
            status: ClaimStatus.Pending,
            rejectionReason: ""
        }));
        
        // Add to participant claims
        participantClaims[msg.sender].push(claimId);
        
        emit ClaimSubmitted(claimId, msg.sender, _amount, _reason, block.timestamp);
        
        return claimId;
    }

    /**
     * @dev Resolve a claim (approve or reject)
     * @param _claimId ID of the claim
     * @param _approved Whether the claim is approved
     * @param _rejectionReason Reason for rejection (if applicable)
     */
    function resolveClaim(
        uint256 _claimId,
        bool _approved,
        string calldata _rejectionReason
    ) external nonReentrant onlyRole(CLAIM_MANAGER_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_claimId < claims.length, "Invalid claim ID");
        
        Claim storage claim = claims[_claimId];
        require(claim.status == ClaimStatus.Pending, "Claim already resolved");
        
        if (_approved) {
            // Approve claim
            claim.status = ClaimStatus.Approved;
            claim.resolutionTime = block.timestamp;
            
            // Pay claim
            _payClaim(_claimId);
        } else {
            // Reject claim
            claim.status = ClaimStatus.Rejected;
            claim.resolutionTime = block.timestamp;
            claim.rejectionReason = _rejectionReason;
        }
        
        emit ClaimResolved(
            _claimId,
            claim.participant,
            claim.amount,
            claim.status,
            block.timestamp
        );
    }

    /**
     * @dev Internal function to pay a claim
     * @param _claimId ID of the claim
     */
    function _payClaim(uint256 _claimId) internal {
        Claim storage claim = claims[_claimId];
        require(claim.status == ClaimStatus.Approved, "Claim not approved");
        
        // Check if pool has enough funds
        uint256 poolBalance = IERC20(poolInfo.contributionToken).balanceOf(address(this));
        require(poolBalance >= claim.amount, "Insufficient pool funds");
        
        // Update claim status
        claim.status = ClaimStatus.Paid;
        
        // Update participant record
        participants[claim.participant].claimsPaid += claim.amount;
        
        // Update pool info
        poolInfo.totalClaims += claim.amount;
        
        // Transfer funds to participant
        IERC20(poolInfo.contributionToken).safeTransfer(
            claim.participant,
            claim.amount
        );
        
        emit ClaimPaid(_claimId, claim.participant, claim.amount, block.timestamp);
    }

    /**
     * @dev Add an insurable event
     * @param _name Name of the event
     * @param _description Description of the event
     * @param _maxCoverageAmount Maximum coverage amount
     * @return eventId The ID of the added event
     */
    function addInsurableEvent(
        string calldata _name,
        string calldata _description,
        uint256 _maxCoverageAmount
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) returns (bytes32)  {
        // TODO: Add nonReentrant modifier
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_description).length > 0, "Description cannot be empty");
        require(_maxCoverageAmount > 0, "Max coverage must be > 0");
        
        // Generate event ID
        bytes32 eventId = keccak256(abi.encodePacked(
            _name,
            block.timestamp
        ));
        
        // Create event
        insurableEvents[eventId] = InsurableEvent({
            name: _name,
            description: _description,
            covered: true,
            maxCoverageAmount: _maxCoverageAmount
        });
        
        // Add to event IDs
        insurableEventIds.push(eventId);
        
        emit InsurableEventAdded(eventId, _name, _maxCoverageAmount, block.timestamp);
        
        return eventId;
    }

    /**
     * @dev Update an insurable event
     * @param _eventId ID of the event
     * @param _maxCoverageAmount New maximum coverage amount
     * @param _covered Whether the event is covered
     */
    function updateInsurableEvent(
        bytes32 _eventId,
        uint256 _maxCoverageAmount,
        bool _covered
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(insurableEvents[_eventId].maxCoverageAmount > 0, "Event does not exist");
        require(_maxCoverageAmount > 0, "Max coverage must be > 0");
        
        // Update event
        insurableEvents[_eventId].maxCoverageAmount = _maxCoverageAmount;
        insurableEvents[_eventId].covered = _covered;
        
        emit InsurableEventUpdated(
            _eventId,
            insurableEvents[_eventId].name,
            _maxCoverageAmount,
            _covered,
            block.timestamp
        );
    }

    /**
     * @dev Distribute surplus to participants
     */
    function distributeSurplus() external nonReentrant onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(poolInfo.active, "Pool is not active");
        require(
            block.timestamp >= lastSurplusDistribution + surplusDistributionPeriod,
            "Distribution period not elapsed"
        );
        
        // Calculate surplus
        uint256 poolBalance = IERC20(poolInfo.contributionToken).balanceOf(address(this));
        uint256 surplus = poolBalance - (poolInfo.totalContributions - poolInfo.totalClaims);
        
        require(surplus > 0, "No surplus to distribute");
        
        // Distribute surplus proportionally to participants
        uint256 totalActiveContributions = 0;
        
        // Calculate total active contributions
        for (uint256 i = 0; i < participantList.length; i++) {
            address participant = participantList[i];
            if (participants[participant].active) {
                totalActiveContributions += participants[participant].totalContribution;
            }
        }
        
        // Distribute surplus
        for (uint256 i = 0; i < participantList.length; i++) {
            address participant = participantList[i];
            if (participants[participant].active) {
                uint256 participantShare = (surplus * participants[participant].totalContribution) / totalActiveContributions;
                
                if (participantShare > 0) {
                    IERC20(poolInfo.contributionToken).safeTransfer(
                        participant,
                        participantShare
                    );
                }
            }
        }
        
        // Update last distribution time
        lastSurplusDistribution = block.timestamp;
        
        emit SurplusDistributed(surplus, poolInfo.participantCount, block.timestamp);
    }

    /**
     * @dev Activate the pool
     */
    function activatePool() external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(!poolInfo.active, "Pool already active");
        
        poolInfo.active = true;
        
        emit PoolActivated(block.timestamp);
    }

    /**
     * @dev Deactivate the pool
     */
    function deactivatePool() external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(poolInfo.active, "Pool already inactive");
        
        poolInfo.active = false;
        
        emit PoolDeactivated(block.timestamp);
    }

    /**
     * @dev Update minimum contribution
     * @param _minContribution New minimum contribution
     */
    function updateMinContribution(
        uint256 _minContribution
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_minContribution > 0, "Min contribution must be > 0");
        
        poolInfo.minContribution = _minContribution;
    }

    /**
     * @dev Update surplus distribution period
     * @param _period New distribution period in seconds
     */
    function updateSurplusDistributionPeriod(
        uint256 _period
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_period >= 30 days, "Period too short");
        
        surplusDistributionPeriod = _period;
    }

    /**
     * @dev Get all insurable events
     * @return Array of event IDs
     */
    function getAllInsurableEvents() external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return insurableEventIds;
    }

    /**
     * @dev Get participant claims
     * @param _participant Address of the participant
     * @return Array of claim IDs
     */
    function getParticipantClaims(
        address _participant
    ) external view returns (uint256[] memory)  {
        // TODO: Add nonReentrant modifier
        return participantClaims[_participant];
    }

    /**
     * @dev Get pool balance
     * @return Current balance of the pool
     */
    function getPoolBalance() external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return IERC20(poolInfo.contributionToken).balanceOf(address(this));
    }

    /**
     * @dev Get claim count
     * @return Number of claims
     */
    function getClaimCount() external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return claims.length;
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
