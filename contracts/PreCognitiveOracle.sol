// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title PreCognitiveOracle
 * @notice Oracle contract that posts verifiable event probabilities on-chain
 * @dev Part of the V42 Pre-Cognitive Oracle & Causality Engine architecture
 */
contract PreCognitiveOracle is Ownable, AccessControl, ReentrancyGuard, Pausable {
    using ECDSA for bytes32;
    
    // Role definitions
    bytes32 public constant ORACLE_PROVIDER_ROLE = keccak256("ORACLE_PROVIDER_ROLE");
    bytes32 public constant EVENT_VERIFIER_ROLE = keccak256("EVENT_VERIFIER_ROLE");
    
    // Event type definitions
    struct EventType {
        string name;
        string description;
        bool isActive;
        uint256 creationTime;
    }
    
    // Event probability data
    struct EventProbability {
        bytes32 eventTypeId;
        uint256 probability;     // In basis points (0-10000)
        uint256 confidence;      // In basis points (0-10000)
        uint256 timestamp;       // When the probability was posted
        uint256 expirationTime;  // When the prediction expires
        address provider;        // Address that provided this probability
        bytes32 dataHash;        // Hash of supporting data
        bool isVerified;         // Whether the event has been verified
        bool eventOccurred;      // Whether the event actually occurred
    }
    
    // Mapping from event type ID to event type
    mapping(bytes32 => EventType) public eventTypes;
    
    // Array of all event type IDs
    bytes32[] public eventTypeIds;
    
    // Mapping from event type ID to time horizon to probability ID
    mapping(bytes32 => mapping(bytes32 => bytes32)) public latestProbabilities;
    
    // Mapping from probability ID to event probability
    mapping(bytes32 => EventProbability) public eventProbabilities;
    
    // Mapping from event type ID to time horizon to historical probability IDs
    mapping(bytes32 => mapping(bytes32 => bytes32[])) public historicalProbabilities;
    
    // Time horizon definitions
    struct TimeHorizon {
        string name;
        uint256 durationSeconds;
        bool isActive;
    }
    
    // Mapping from time horizon ID to time horizon
    mapping(bytes32 => TimeHorizon) public timeHorizons;
    
    // Array of all time horizon IDs
    bytes32[] public timeHorizonIds;
    
    // Multi-oracle consensus mechanism
    struct OracleProvider {
        string name;
        bool isActive;
        uint256 reputationScore;
        uint256 lastUpdateTime;
    }
    
    // Mapping of oracle provider addresses to their data
    mapping(address => OracleProvider) public oracleProviders;
    
    // Array of all oracle provider addresses
    address[] public oracleProviderAddresses;
    
    // Minimum number of oracle providers required for consensus
    uint256 public minOracleConsensus = 3;
    
    // Mapping of probability ID to oracle providers who have confirmed it
    mapping(bytes32 => address[]) public probabilityConfirmations;
      // Trusted signers for off-chain verification
    mapping(address => bool) public trustedSigners;
    
    // Gas griefing protection
    uint256 public constant MAX_BATCH_SIZE = 100; // Maximum probabilities per batch
    uint256 public constant MAX_ARRAY_LENGTH = 1000; // Maximum array length for any operation
    
    // Events
    event EventTypeRegistered(
        bytes32 indexed eventTypeId,
        string name,
        string description,
        uint256 timestamp
    );
    
    event EventTypeUpdated(
        bytes32 indexed eventTypeId,
        string name,
        string description,
        bool isActive,
        uint256 timestamp
    );
    
    event TimeHorizonRegistered(
        bytes32 indexed horizonId,
        string name,
        uint256 durationSeconds,
        uint256 timestamp
    );
    
    event TimeHorizonUpdated(
        bytes32 indexed horizonId,
        string name,
        uint256 durationSeconds,
        bool isActive,
        uint256 timestamp
    );
    
    event ProbabilityPosted(
        bytes32 indexed eventTypeId,
        bytes32 indexed horizonId,
        bytes32 indexed probabilityId,
        uint256 probability,
        uint256 confidence,
        uint256 expirationTime,
        uint256 timestamp
    );
    
    event EventVerified(
        bytes32 indexed eventTypeId,
        bytes32 indexed probabilityId,
        bool eventOccurred,
        address verifier,
        uint256 timestamp
    );
    
    event TrustedSignerAdded(
        address indexed signer,
        uint256 timestamp
    );
    
    event TrustedSignerRemoved(
        address indexed signer,
        uint256 timestamp
    );
    
    event OracleProviderRegistered(
        address indexed provider,
        string name,
        uint256 timestamp
    );
    
    event OracleProviderUpdated(
        address indexed provider,
        string name,
        bool isActive,
        uint256 reputationScore,
        uint256 timestamp
    );
    
    event OracleProviderRemoved(
        address indexed provider,
        uint256 timestamp
    );
    
    event ProbabilityConfirmed(
        bytes32 indexed probabilityId,
        address indexed provider,
        uint256 timestamp
    );
    
    event ConsensusReached(
        bytes32 indexed probabilityId,
        uint256 confirmations,
        uint256 timestamp
    );
    
    /**
     * @dev Constructor
     */
    constructor() Ownable(msg.sender) {
        // Setup roles
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), msg.sender);
        _grantRole(ORACLE_PROVIDER_ROLE, msg.sender);
        _grantRole(EVENT_VERIFIER_ROLE, msg.sender);
        
        // Add deployer as trusted signer
        trustedSigners[msg.sender] = true;
        emit TrustedSignerAdded(msg.sender, block.timestamp);
        
        // Register deployer as the first oracle provider
        _registerOracleProvider(msg.sender, "Primary Oracle Provider");
    }
    
    /**
     * @dev Register a new oracle provider
     * @param _provider Address of the oracle provider
     * @param _name Name of the oracle provider
     */
    function registerOracleProvider(
        address _provider,
        string memory _name
    ) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        _registerOracleProvider(_provider, _name);
    }
    
    /**
     * @dev Internal function to register a new oracle provider
     * @param _provider Address of the oracle provider
     * @param _name Name of the oracle provider
     */
    function _registerOracleProvider(
        address _provider,
        string memory _name
    ) internal {
        require(_provider != address(0), "Provider address cannot be zero");
        require(bytes(_name).length > 0, "Provider name cannot be empty");
        require(oracleProviders[_provider].lastUpdateTime == 0, "Provider already registered");
        
        // Register the provider
        oracleProviders[_provider] = OracleProvider({
            name: _name,
            isActive: true,
            reputationScore: 100, // Initial reputation score
            lastUpdateTime: block.timestamp
        });
        
        // Add to the array of provider addresses
        oracleProviderAddresses.push(_provider);
        
        // Grant the ORACLE_PROVIDER_ROLE
        _grantRole(ORACLE_PROVIDER_ROLE, _provider);
        
        emit OracleProviderRegistered(_provider, _name, block.timestamp);
    }
    
    /**
     * @dev Update an existing oracle provider
     * @param _provider Address of the oracle provider
     * @param _name New name
     * @param _isActive Whether the provider is active
     * @param _reputationScore New reputation score
     */
    function updateOracleProvider(
        address _provider,
        string memory _name,
        bool _isActive,
        uint256 _reputationScore
    ) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_provider != address(0), "Provider address cannot be zero");
        require(bytes(_name).length > 0, "Provider name cannot be empty");
        require(oracleProviders[_provider].lastUpdateTime > 0, "Provider not registered");
        
        OracleProvider storage provider = oracleProviders[_provider];
        
        provider.name = _name;
        provider.isActive = _isActive;
        provider.reputationScore = _reputationScore;
        provider.lastUpdateTime = block.timestamp;
        
        emit OracleProviderUpdated(
            _provider,
            _name,
            _isActive,
            _reputationScore,
            block.timestamp
        );
    }
    
    /**
     * @dev Remove an oracle provider
     * @param _provider Address of the oracle provider to remove
     */
    function removeOracleProvider(
        address _provider
    ) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(oracleProviders[_provider].lastUpdateTime > 0, "Provider not registered");
        
        // Deactivate the provider
        oracleProviders[_provider].isActive = false;
        oracleProviders[_provider].lastUpdateTime = block.timestamp;
        
        // Revoke the ORACLE_PROVIDER_ROLE
        _revokeRole(ORACLE_PROVIDER_ROLE, _provider);
        
        emit OracleProviderRemoved(_provider, block.timestamp);
    }
    
    /**
     * @dev Set the minimum number of oracle providers required for consensus
     * @param _minConsensus New minimum consensus value
     */
    function setMinOracleConsensus(
        uint256 _minConsensus
    ) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_minConsensus > 0, "Minimum consensus must be greater than zero");
        require(_minConsensus <= oracleProviderAddresses.length, "Minimum consensus cannot exceed number of providers");
        
        minOracleConsensus = _minConsensus;
    }
    
    /**
     * @dev Get the number of active oracle providers
     * @return count Number of active providers
     */
    function getActiveOracleProvidersCount() external view returns (uint256 count)  {
        // TODO: Add nonReentrant modifier
        for (uint256 i = 0; i < oracleProviderAddresses.length; i++) {
            if (oracleProviders[oracleProviderAddresses[i]].isActive) {
                count++;
            }
        }
        return count;
    }
    
    /**
     * @dev Register a new event type
     * @param _name Name of the event type
     * @param _description Description of the event type
     * @return eventTypeId ID of the registered event type
     */
    function registerEventType(
        string memory _name,
        string memory _description
    ) external onlyRole(ORACLE_PROVIDER_ROLE) returns (bytes32 eventTypeId)  {
        // TODO: Add nonReentrant modifier
        require(bytes(_name).length > 0, "Name cannot be empty");
        
        // Generate event type ID
        eventTypeId = keccak256(abi.encodePacked(_name, block.timestamp));
        
        // Ensure it doesn't already exist
        require(bytes(eventTypes[eventTypeId].name).length == 0, "Event type ID already exists");
        
        // Register event type
        eventTypes[eventTypeId] = EventType({
            name: _name,
            description: _description,
            isActive: true,
            creationTime: block.timestamp
        });
        
        // Add to array
        eventTypeIds.push(eventTypeId);
        
        emit EventTypeRegistered(
            eventTypeId,
            _name,
            _description,
            block.timestamp
        );
        
        return eventTypeId;
    }
    
    /**
     * @dev Update an existing event type
     * @param _eventTypeId ID of the event type
     * @param _name New name
     * @param _description New description
     * @param _isActive Whether the event type is active
     */
    function updateEventType(
        bytes32 _eventTypeId,
        string memory _name,
        string memory _description,
        bool _isActive
    ) external onlyRole(ORACLE_PROVIDER_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(bytes(eventTypes[_eventTypeId].name).length > 0, "Event type does not exist");
        require(bytes(_name).length > 0, "Name cannot be empty");
        
        EventType storage eventType = eventTypes[_eventTypeId];
        
        eventType.name = _name;
        eventType.description = _description;
        eventType.isActive = _isActive;
        
        emit EventTypeUpdated(
            _eventTypeId,
            _name,
            _description,
            _isActive,
            block.timestamp
        );
    }
    
    /**
     * @dev Register a new time horizon
     * @param _name Name of the time horizon
     * @param _durationSeconds Duration in seconds
     * @return horizonId ID of the registered time horizon
     */
    function registerTimeHorizon(
        string memory _name,
        uint256 _durationSeconds
    ) external onlyRole(ORACLE_PROVIDER_ROLE) returns (bytes32 horizonId)  {
        // TODO: Add nonReentrant modifier
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(_durationSeconds > 0, "Duration must be greater than zero");
        
        // Generate horizon ID
        horizonId = keccak256(abi.encodePacked(_name, _durationSeconds));
        
        // Ensure it doesn't already exist
        require(timeHorizons[horizonId].durationSeconds == 0, "Time horizon already exists");
        
        // Register time horizon
        timeHorizons[horizonId] = TimeHorizon({
            name: _name,
            durationSeconds: _durationSeconds,
            isActive: true
        });
        
        // Add to array
        timeHorizonIds.push(horizonId);
        
        emit TimeHorizonRegistered(
            horizonId,
            _name,
            _durationSeconds,
            block.timestamp
        );
        
        return horizonId;
    }
    
    /**
     * @dev Update an existing time horizon
     * @param _horizonId ID of the time horizon
     * @param _name New name
     * @param _durationSeconds New duration in seconds
     * @param _isActive Whether the time horizon is active
     */
    function updateTimeHorizon(
        bytes32 _horizonId,
        string memory _name,
        uint256 _durationSeconds,
        bool _isActive
    ) external onlyRole(ORACLE_PROVIDER_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(timeHorizons[_horizonId].durationSeconds > 0, "Time horizon does not exist");
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(_durationSeconds > 0, "Duration must be greater than zero");
        
        TimeHorizon storage horizon = timeHorizons[_horizonId];
        
        horizon.name = _name;
        horizon.durationSeconds = _durationSeconds;
        horizon.isActive = _isActive;
        
        emit TimeHorizonUpdated(
            _horizonId,
            _name,
            _durationSeconds,
            _isActive,
            block.timestamp
        );
    }
    
    /**
     * @dev Post a new event probability
     * @param _eventTypeId ID of the event type
     * @param _horizonId ID of the time horizon
     * @param _probability Probability in basis points (0-10000)
     * @param _confidence Confidence in basis points (0-10000)
     * @param _dataHash Hash of supporting data
     * @return probabilityId ID of the posted probability
     */
    function postProbability(
        bytes32 _eventTypeId,
        bytes32 _horizonId,
        uint256 _probability,
        uint256 _confidence,
        bytes32 _dataHash
    ) public onlyRole(ORACLE_PROVIDER_ROLE) whenNotPaused returns (bytes32 probabilityId)  {
        // TODO: Add nonReentrant modifier
        require(bytes(eventTypes[_eventTypeId].name).length > 0, "Event type does not exist");
        require(timeHorizons[_horizonId].durationSeconds > 0, "Time horizon does not exist");
        require(eventTypes[_eventTypeId].isActive, "Event type is not active");
        require(timeHorizons[_horizonId].isActive, "Time horizon is not active");
        require(_probability <= 10000, "Probability cannot exceed 10000 basis points");
        require(_confidence <= 10000, "Confidence cannot exceed 10000 basis points");
        
        // Verify the oracle provider is active
        require(oracleProviders[msg.sender].isActive, "Oracle provider is not active");
        
        // Calculate expiration time
        uint256 expirationTime = block.timestamp + timeHorizons[_horizonId].durationSeconds;
        
        // Check if there's an existing probability for this event type and horizon
        bytes32 existingProbabilityId = latestProbabilities[_eventTypeId][_horizonId];
        
        if (existingProbabilityId != bytes32(0)) {
            // If this is a confirmation of an existing probability
            if (_dataHash == eventProbabilities[existingProbabilityId].dataHash) {
                // Add this provider to the confirmations
                address[] storage confirmations = probabilityConfirmations[existingProbabilityId];
                
                // Check if this provider has already confirmed
                bool alreadyConfirmed = false;
                for (uint256 i = 0; i < confirmations.length; i++) {
                    if (confirmations[i] == msg.sender) {
                        alreadyConfirmed = true;
                        break;
                    }
                }
                
                if (!alreadyConfirmed) {
                    // Add confirmation
                    confirmations.push(msg.sender);
                    
                    emit ProbabilityConfirmed(
                        existingProbabilityId,
                        msg.sender,
                        block.timestamp
                    );
                    
                    // Check if consensus has been reached
                    if (confirmations.length >= minOracleConsensus) {
                        emit ConsensusReached(
                            existingProbabilityId,
                            confirmations.length,
                            block.timestamp
                        );
                    }
                }
                
                return existingProbabilityId;
            }
        }
        
        // Generate probability ID for a new probability
        probabilityId = keccak256(abi.encodePacked(
            _eventTypeId,
            _horizonId,
            _probability,
            _confidence,
            block.timestamp
        ));
        
        // Create event probability
        eventProbabilities[probabilityId] = EventProbability({
            eventTypeId: _eventTypeId,
            probability: _probability,
            confidence: _confidence,
            timestamp: block.timestamp,
            expirationTime: expirationTime,
            provider: msg.sender,
            dataHash: _dataHash,
            isVerified: false,
            eventOccurred: false
        });
        
        // Initialize confirmations with the current provider
        probabilityConfirmations[probabilityId] = [msg.sender];
        
        // Only update latest probability if we have enough confirmations or there's no existing one
        if (existingProbabilityId == bytes32(0) || 
            probabilityConfirmations[existingProbabilityId].length < minOracleConsensus) {
            latestProbabilities[_eventTypeId][_horizonId] = probabilityId;
        }
        
        // Add to historical probabilities
        historicalProbabilities[_eventTypeId][_horizonId].push(probabilityId);
        
        emit ProbabilityPosted(
            _eventTypeId,
            _horizonId,
            probabilityId,
            _probability,
            _confidence,
            expirationTime,
            block.timestamp
        );
        
        emit ProbabilityConfirmed(
            probabilityId,
            msg.sender,
            block.timestamp
        );
        
        return probabilityId;
    }
    
    /**
     * @dev Confirm an existing probability
     * @param _probabilityId ID of the probability to confirm
     * @return confirmations Number of confirmations after this one
     */
    function confirmProbability(
        bytes32 _probabilityId
    ) external onlyRole(ORACLE_PROVIDER_ROLE) whenNotPaused returns (uint256)  {
        // TODO: Add nonReentrant modifier
        require(oracleProviders[msg.sender].isActive, "Oracle provider is not active");
        
        EventProbability storage probability = eventProbabilities[_probabilityId];
        require(probability.timestamp > 0, "Probability does not exist");
        require(block.timestamp < probability.expirationTime, "Probability has expired");
        require(probability.provider != msg.sender, "Cannot confirm own probability");
        
        // Get confirmations
        address[] storage confirmations = probabilityConfirmations[_probabilityId];
        
        // Check if this provider has already confirmed
        for (uint256 i = 0; i < confirmations.length; i++) {
            if (confirmations[i] == msg.sender) {
                return confirmations.length;
            }
        }
        
        // Add confirmation
        confirmations.push(msg.sender);
        
        emit ProbabilityConfirmed(
            _probabilityId,
            msg.sender,
            block.timestamp
        );
        
        // Check if consensus has been reached
        if (confirmations.length >= minOracleConsensus) {
            emit ConsensusReached(
                _probabilityId,
                confirmations.length,
                block.timestamp
            );
        }
        
        return confirmations.length;
    }
    
    /**
     * @dev Post multiple event probabilities in a single transaction
     * @param _eventTypeIds Array of event type IDs
     * @param _horizonIds Array of time horizon IDs
     * @param _probabilities Array of probabilities in basis points
     * @param _confidences Array of confidences in basis points
     * @param _dataHashes Array of data hashes
     * @return probabilityIds Array of posted probability IDs
     */    function postMultipleProbabilities(
        bytes32[] memory _eventTypeIds,
        bytes32[] memory _horizonIds,
        uint256[] memory _probabilities,
        uint256[] memory _confidences,
        bytes32[] memory _dataHashes
    ) external onlyRole(ORACLE_PROVIDER_ROLE) whenNotPaused returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        require(
            _eventTypeIds.length == _horizonIds.length &&
            _eventTypeIds.length == _probabilities.length &&
            _eventTypeIds.length == _confidences.length &&
            _eventTypeIds.length == _dataHashes.length,
            "Array lengths must match"
        );
        require(_eventTypeIds.length <= MAX_BATCH_SIZE, "Batch size exceeds maximum");
        require(_eventTypeIds.length > 0, "No probabilities provided");
        
        bytes32[] memory probabilityIds = new bytes32[](_eventTypeIds.length);
        
        for (uint256 i = 0; i < _eventTypeIds.length; i++) {
            probabilityIds[i] = postProbability(
                _eventTypeIds[i],
                _horizonIds[i],
                _probabilities[i],
                _confidences[i],
                _dataHashes[i]
            );
        }
        
        return probabilityIds;
    }
    
    /**
     * @dev Verify whether an event occurred
     * @param _probabilityId ID of the probability
     * @param _eventOccurred Whether the event actually occurred
     */
    function verifyEvent(
        bytes32 _probabilityId,
        bool _eventOccurred
    ) external onlyRole(EVENT_VERIFIER_ROLE)  {
        // TODO: Add nonReentrant modifier
        EventProbability storage probability = eventProbabilities[_probabilityId];
        
        require(probability.timestamp > 0, "Probability does not exist");
        require(!probability.isVerified, "Event already verified");
        require(block.timestamp >= probability.expirationTime, "Event has not expired yet");
        
        // Mark as verified
        probability.isVerified = true;
        probability.eventOccurred = _eventOccurred;
        
        emit EventVerified(
            probability.eventTypeId,
            _probabilityId,
            _eventOccurred,
            msg.sender,
            block.timestamp
        );
    }
    
    /**
     * @dev Verify an event with a signature from a trusted signer
     * @param _probabilityId ID of the probability
     * @param _eventOccurred Whether the event actually occurred
     * @param _signature Signature from a trusted signer
     */
    function verifyEventWithSignature(
        bytes32 _probabilityId,
        bool _eventOccurred,
        bytes memory _signature
    ) external nonReentrant{
        EventProbability storage probability = eventProbabilities[_probabilityId];
        
        require(probability.timestamp > 0, "Probability does not exist");
        require(!probability.isVerified, "Event already verified");
        require(block.timestamp >= probability.expirationTime, "Event has not expired yet");
        
        // Verify signature
        bytes32 messageHash = keccak256(abi.encodePacked(
            _probabilityId,
            _eventOccurred,
            block.chainid
        ));
        
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        address signer = ethSignedMessageHash.recover(_signature);
        
        require(trustedSigners[signer], "Invalid signature");
        
        // Mark as verified
        probability.isVerified = true;
        probability.eventOccurred = _eventOccurred;
        
        emit EventVerified(
            probability.eventTypeId,
            _probabilityId,
            _eventOccurred,
            signer,
            block.timestamp
        );
    }
    
    /**
     * @dev Add a trusted signer
     * @param _signer Address of the signer
     */
    function addTrustedSigner(address _signer) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_signer != address(0), "Invalid signer address");
        require(!trustedSigners[_signer], "Signer already trusted");
        
        trustedSigners[_signer] = true;
        
        emit TrustedSignerAdded(_signer, block.timestamp);
    }
    
    /**
     * @dev Remove a trusted signer
     * @param _signer Address of the signer
     */
    function removeTrustedSigner(address _signer) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(trustedSigners[_signer], "Signer not trusted");
        
        trustedSigners[_signer] = false;
        
        emit TrustedSignerRemoved(_signer, block.timestamp);
    }
    
    /**
     * @dev Get the latest probability for an event type and time horizon
     * @param _eventTypeId ID of the event type
     * @param _horizonId ID of the time horizon
     * @return probabilityId ID of the latest probability
     * @return probability Probability in basis points
     * @return confidence Confidence in basis points
     * @return timestamp Timestamp when the probability was posted
     * @return expirationTime When the prediction expires
     */
    function getLatestProbability(
        bytes32 _eventTypeId,
        bytes32 _horizonId
    ) external view returns (
        bytes32 probabilityId,
        uint256 probability,
        uint256 confidence,
        uint256 timestamp,
        uint256 expirationTime
    ) {
        probabilityId = latestProbabilities[_eventTypeId][_horizonId];
        
        if (probabilityId == bytes32(0)) {
            return (bytes32(0), 0, 0, 0, 0);
        }
        
        EventProbability storage prob = eventProbabilities[probabilityId];
        
        return (
            probabilityId,
            prob.probability,
            prob.confidence,
            prob.timestamp,
            prob.expirationTime
        );
    }
    
    /**
     * @dev Get historical probabilities for an event type and time horizon
     * @param _eventTypeId ID of the event type
     * @param _horizonId ID of the time horizon
     * @return Array of probability IDs
     */
    function getHistoricalProbabilities(
        bytes32 _eventTypeId,
        bytes32 _horizonId
    ) external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return historicalProbabilities[_eventTypeId][_horizonId];
    }
    
    /**
     * @dev Get probability details
     * @param _probabilityId ID of the probability
     * @return eventTypeId ID of the event type
     * @return probability Probability in basis points
     * @return confidence Confidence in basis points
     * @return timestamp Timestamp when the probability was posted
     * @return expirationTime When the prediction expires
     * @return provider Address that provided this probability
     * @return dataHash Hash of supporting data
     * @return isVerified Whether the event has been verified
     * @return eventOccurred Whether the event actually occurred
     */
    function getProbabilityDetails(
        bytes32 _probabilityId
    ) external view returns (
        bytes32 eventTypeId,
        uint256 probability,
        uint256 confidence,
        uint256 timestamp,
        uint256 expirationTime,
        address provider,
        bytes32 dataHash,
        bool isVerified,
        bool eventOccurred
    ) {
        EventProbability storage prob = eventProbabilities[_probabilityId];
        
        return (
            prob.eventTypeId,
            prob.probability,
            prob.confidence,
            prob.timestamp,
            prob.expirationTime,
            prob.provider,
            prob.dataHash,
            prob.isVerified,
            prob.eventOccurred
        );
    }
    
    /**
     * @dev Get all event types
     * @return Array of event type IDs
     */
    function getAllEventTypes() external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return eventTypeIds;
    }
    
    /**
     * @dev Get all time horizons
     * @return Array of time horizon IDs
     */
    function getAllTimeHorizons() external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return timeHorizonIds;
    }
    
    /**
     * @dev Pause the contract
     */
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE)  nonReentrant onlyOwner{
        _pause();
    }
    
    /**
     * @dev Unpause the contract
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE)  nonReentrant onlyOwner{
        _unpause();
    }
}
