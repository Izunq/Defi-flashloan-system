// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./interfaces/IZKVerifier.sol";

/**
 * @title ZKVerifier
 * @notice Contract for verifying ZK proofs with enhanced security features
 * @dev Implements the IZKVerifier interface with replay protection and timeouts
 */
contract ZKVerifier is IZKVerifier, Ownable, ReentrancyGuard, Pausable {
    using Counters for Counters.Counter;
    
    // Verification key hash
    bytes32 public verificationKeyHash;
    
    // Groth16 verification parameters
    struct VerificationKey {
        uint256[2] alpha1;
        uint256[2][2] beta2;
        uint256[2][2] gamma2;
        uint256[2][2] delta2;
        uint256[2][] ic;
    }
    
    VerificationKey private verificationKey;
    
    // Proof replay protection
    mapping(bytes32 => bool) public usedProofs;
    
    // Proof timeout mechanism
    uint256 public proofValidityPeriod = 1 hours;
    mapping(bytes32 => uint256) public proofTimestamps;
    
    // Proof generation timeout
    uint256 public maxProofGenerationTime = 5 minutes;
    
    // Nonce for each prover to prevent replay attacks
    mapping(address => Counters.Counter) private proverNonces;
    
    // Batch verification tracking
    struct BatchVerification {
        bytes32[] proofHashes;
        bool[] results;
        uint256 timestamp;
        bool completed;
    }
    
    mapping(bytes32 => BatchVerification) public batchVerifications;
    Counters.Counter private batchIdCounter;
      // Proof size limits
    uint256 public minProofSize = 100; // Minimum bytes for a valid proof
    uint256 public maxProofSize = 10000; // Maximum bytes for a valid proof
    
    // Gas griefing protection
    uint256 public constant MAX_BATCH_SIZE = 50; // Maximum proofs per batch
    uint256 public constant MAX_GAS_PER_PROOF = 200000; // Maximum gas per proof verification
    uint256 public gasUsedThreshold = 5000000; // Circuit breaker threshold
    
    // Events
    event VerificationKeyUpdated(bytes32 keyHash);
    event ProofVerified(address indexed verifier, bytes32 proofHash, bool success);
    event ProofTimeout(address indexed verifier, bytes32 proofHash);
    event ProofValidityPeriodUpdated(uint256 newPeriod);
    event MaxProofGenerationTimeUpdated(uint256 newTime);
    event BatchVerificationCreated(bytes32 indexed batchId, uint256 proofCount);
    event BatchVerificationCompleted(bytes32 indexed batchId, uint256 successCount, uint256 totalCount);
    event ProofSizeLimitsUpdated(uint256 minSize, uint256 maxSize);
    
    /**
     * @dev Constructor
     * @param _owner Owner of the contract
     */
    constructor(address _owner) Ownable(_owner) {
        // Initialize with empty verification key
        verificationKeyHash = bytes32(0);
    }
    
    // Verification status tracking
    struct VerificationStatus {
        bool formallyVerified;
        bytes32 verificationReportHash;
        uint256 verificationTimestamp;
        address verifier;
    }
    
    // Mapping to track formal verification status of verification keys
    mapping(bytes32 => VerificationStatus) public verificationStatus;
    
    // Event for formal verification
    event CircuitFormallyVerified(bytes32 keyHash, bytes32 reportHash, address verifier);
    
    /**
     * @dev Set the verification key
     * @param _alpha1 Alpha1 parameter
     * @param _beta2 Beta2 parameter
     * @param _gamma2 Gamma2 parameter
     * @param _delta2 Delta2 parameter
     * @param _ic IC parameters
     * @param _verificationReportHash Hash of the formal verification report
     */
    function setVerificationKey(
        uint256[2] memory _alpha1,
        uint256[2][2] memory _beta2,
        uint256[2][2] memory _gamma2,
        uint256[2][2] memory _delta2,
        uint256[2][] memory _ic,
        bytes32 _verificationReportHash
    ) external onlyOwner whenNotPaused {
        // Calculate the hash of the verification key
        bytes32 newKeyHash = keccak256(abi.encode(
            _alpha1,
            _beta2,
            _gamma2,
            _delta2,
            _ic
        ));
        
        // Require formal verification before setting the key
        require(
            verificationStatus[newKeyHash].formallyVerified || 
            _verificationReportHash != bytes32(0),
            "Circuit must be formally verified"
        );
        
        // Set the verification key
        verificationKey.alpha1 = _alpha1;
        verificationKey.beta2 = _beta2;
        verificationKey.gamma2 = _gamma2;
        verificationKey.delta2 = _delta2;
        verificationKey.ic = _ic;
        
        // Store the hash
        verificationKeyHash = newKeyHash;
        
        // Update verification status if a new report is provided
        if (_verificationReportHash != bytes32(0)) {
            verificationStatus[newKeyHash] = VerificationStatus({
                formallyVerified: true,
                verificationReportHash: _verificationReportHash,
                verificationTimestamp: block.timestamp,
                verifier: msg.sender
            });
            
            emit CircuitFormallyVerified(newKeyHash, _verificationReportHash, msg.sender);
        }
        
        emit VerificationKeyUpdated(verificationKeyHash);
    }
    
    /**
     * @dev Register formal verification of a circuit without changing the current key
     * @param _keyHash Hash of the verification key
     * @param _verificationReportHash Hash of the formal verification report
     */
    function registerFormalVerification(
        bytes32 _keyHash,
        bytes32 _verificationReportHash
    ) external onlyOwner {
        require(_verificationReportHash != bytes32(0), "Invalid verification report hash");
        
        verificationStatus[_keyHash] = VerificationStatus({
            formallyVerified: true,
            verificationReportHash: _verificationReportHash,
            verificationTimestamp: block.timestamp,
            verifier: msg.sender
        });
        
        emit CircuitFormallyVerified(_keyHash, _verificationReportHash, msg.sender);
    }
    
    /**
     * @dev Get the next nonce for a prover
     * @return The next nonce for the caller
     */
    function getNextNonce() external returns (uint256) {
        proverNonces[msg.sender].increment();
        return proverNonces[msg.sender].current();
    }
    
    /**
     * @dev Register a proof generation request
     * @param requestId Unique identifier for the proof request
     * @return Timestamp when the proof should be ready by
     */
    function registerProofRequest(bytes32 requestId) external whenNotPaused returns (uint256) {
        require(proofTimestamps[requestId] == 0, "Request already registered");
        
        uint256 deadline = block.timestamp + maxProofGenerationTime;
        proofTimestamps[requestId] = deadline;
        
        return deadline;
    }
    
    /**
     * @dev Set proof size limits
     * @param _minSize Minimum proof size in bytes
     * @param _maxSize Maximum proof size in bytes
     */
    function setProofSizeLimits(uint256 _minSize, uint256 _maxSize) external onlyOwner {
        require(_minSize > 0, "Min size must be greater than 0");
        require(_maxSize > _minSize, "Max size must be greater than min size");
        
        minProofSize = _minSize;
        maxProofSize = _maxSize;
        
        emit ProofSizeLimitsUpdated(_minSize, _maxSize);
    }
    
    /**
     * @dev Verify a ZK proof with replay protection and timeout checks
     * @param publicInputs Array of public inputs for the proof
     * @param proof The ZK proof data
     * @param nonce Nonce to prevent replay attacks
     * @param deadline Timestamp by which the proof must be verified
     * @return True if the proof is valid, false otherwise
     */
    function verifyProof(
        uint256[] calldata publicInputs,
        bytes calldata proof,
        uint256 nonce,
        uint256 deadline
    ) external nonReentrant whenNotPaused returns (bool) {
        require(verificationKeyHash != bytes32(0), "Verification key not set");
        require(publicInputs.length > 0, "No public inputs provided");
        require(proof.length > 0, "No proof provided");
        require(block.timestamp <= deadline, "Proof verification deadline passed");
        
        // Validate proof size
        require(proof.length >= minProofSize, "Proof too small");
        require(proof.length <= maxProofSize, "Proof too large");
        
        // Calculate proof hash for replay protection
        bytes32 proofHash = keccak256(abi.encodePacked(
            msg.sender,
            nonce,
            publicInputs,
            proof
        ));
        
        // Check if proof has been used before
        require(!usedProofs[proofHash], "Proof already used");
        
        // Mark proof as used
        usedProofs[proofHash] = true;
        
        // Check if nonce is valid
        require(nonce == proverNonces[msg.sender].current(), "Invalid nonce");
        proverNonces[msg.sender].increment();
        
        // Decode the proof
        (uint256[2] memory a, uint256[2][2] memory b, uint256[2] memory c) = abi.decode(
            proof,
            (uint256[2], uint256[2][2], uint256[2])
        );
        
        // Verify the proof
        bool isValid = _verifyGroth16Proof(a, b, c, publicInputs);
        
        // Record verification result
        emit ProofVerified(msg.sender, proofHash, isValid);
        
        return isValid;
    }
    
    /**
     * @dev Create a batch verification request
     * @param proofs Array of proofs to verify
     * @param publicInputsArray Array of public inputs for each proof
     * @return batchId Unique identifier for this batch
     */    function createBatchVerification(
        bytes[] calldata proofs,
        uint256[][] calldata publicInputsArray
    ) external nonReentrant whenNotPaused returns (bytes32) {
        require(verificationKeyHash != bytes32(0), "Verification key not set");
        require(proofs.length > 0, "No proofs provided");
        require(proofs.length <= MAX_BATCH_SIZE, "Batch size exceeds maximum");
        require(proofs.length == publicInputsArray.length, "Proofs and inputs length mismatch");
        
        // Generate batch ID
        batchIdCounter.increment();
        bytes32 batchId = keccak256(abi.encodePacked(
            "BATCH",
            batchIdCounter.current(),
            msg.sender,
            block.timestamp
        ));
        
        // Initialize batch verification
        bytes32[] memory proofHashes = new bytes32[](proofs.length);
        bool[] memory results = new bool[](proofs.length);
        
        // Store batch verification
        batchVerifications[batchId] = BatchVerification({
            proofHashes: proofHashes,
            results: results,
            timestamp: block.timestamp,
            completed: false
        });
        
        emit BatchVerificationCreated(batchId, proofs.length);
        
        return batchId;
    }
    
    /**
     * @dev Process a batch verification
     * @param batchId Batch ID to process
     * @param proofs Array of proofs to verify
     * @param publicInputsArray Array of public inputs for each proof
     * @return successCount Number of successful verifications
     */    function processBatchVerification(
        bytes32 batchId,
        bytes[] calldata proofs,
        uint256[][] calldata publicInputsArray
    ) external nonReentrant whenNotPaused returns (uint256) {
        require(verificationKeyHash != bytes32(0), "Verification key not set");
        require(proofs.length > 0, "No proofs provided");
        require(proofs.length <= MAX_BATCH_SIZE, "Batch size exceeds maximum");
        require(proofs.length == publicInputsArray.length, "Proofs and inputs length mismatch");
        
        BatchVerification storage batch = batchVerifications[batchId];
        require(batch.timestamp > 0, "Batch does not exist");
        require(!batch.completed, "Batch already completed");
        
        // Initialize result arrays if not already done
        if (batch.proofHashes.length == 0) {
            batch.proofHashes = new bytes32[](proofs.length);
            batch.results = new bool[](proofs.length);
        }
        
        uint256 successCount = 0;
        uint256 gasUsedBatch = 0;
        
        // Process each proof with gas monitoring
        for (uint256 i = 0; i < proofs.length; i++) {
            uint256 gasStart = gasleft();
            
            // Validate proof size
            require(proofs[i].length >= minProofSize, "Proof too small");
            require(proofs[i].length <= maxProofSize, "Proof too large");
            
            // Calculate proof hash
            bytes32 proofHash = keccak256(abi.encodePacked(
                msg.sender,
                i,
                publicInputsArray[i],
                proofs[i]
            ));
            
            // Check if proof has been used before
            if (usedProofs[proofHash]) {
                batch.proofHashes[i] = proofHash;
                batch.results[i] = false;
                continue;
            }
            
            // Mark proof as used
            usedProofs[proofHash] = true;
            
            // Decode the proof
            (uint256[2] memory a, uint256[2][2] memory b, uint256[2] memory c) = abi.decode(
                proofs[i],
                (uint256[2], uint256[2][2], uint256[2])
            );
            
            // Verify the proof with gas limit
            bool isValid;
            if (gasleft() > MAX_GAS_PER_PROOF) {
                isValid = _verifyGroth16Proof(a, b, c, publicInputsArray[i]);
            } else {
                // Skip verification if insufficient gas
                isValid = false;
            }
            
            // Record verification result
            batch.proofHashes[i] = proofHash;
            batch.results[i] = isValid;
            
            if (isValid) {
                successCount++;
            }
            
            emit ProofVerified(msg.sender, proofHash, isValid);
            
            // Monitor gas usage per proof
            uint256 gasUsed = gasStart - gasleft();
            gasUsedBatch += gasUsed;
            
            // Circuit breaker: Stop if gas usage is too high
            if (gasUsedBatch > gasUsedThreshold) {
                // Complete remaining proofs as failed
                for (uint256 j = i + 1; j < proofs.length; j++) {
                    batch.proofHashes[j] = bytes32(0);
                    batch.results[j] = false;
                }
                break;
            }
        }
        
        // Mark batch as completed
        batch.completed = true;
        
        emit BatchVerificationCompleted(batchId, successCount, proofs.length);
        
        return successCount;
    }
    
    /**
     * @dev Get batch verification results
     * @param batchId Batch ID to query
     * @return proofHashes Array of proof hashes
     * @return results Array of verification results
     * @return timestamp Timestamp when the batch was created
     * @return completed Whether the batch is completed
     */
    function getBatchVerificationResults(bytes32 batchId) 
        external 
        view 
        returns (
            bytes32[] memory proofHashes,
            bool[] memory results,
            uint256 timestamp,
            bool completed
        ) 
    {
        BatchVerification storage batch = batchVerifications[batchId];
        require(batch.timestamp > 0, "Batch does not exist");
        
        return (
            batch.proofHashes,
            batch.results,
            batch.timestamp,
            batch.completed
        );
    }
    
    /**
     * @dev Get the verification key hash
     * @return Hash of the verification key
     */
    function getVerificationKeyHash() external view override returns (bytes32) {
        return verificationKeyHash;
    }
    
    /**
     * @dev Update proof validity period
     * @param newPeriod New validity period in seconds
     */
    function updateProofValidityPeriod(uint256 newPeriod) external onlyOwner {
        require(newPeriod > 0, "Period must be greater than 0");
        proofValidityPeriod = newPeriod;
        emit ProofValidityPeriodUpdated(newPeriod);
    }
    
    /**
     * @dev Update max proof generation time
     * @param newTime New max generation time in seconds
     */
    function updateMaxProofGenerationTime(uint256 newTime) external onlyOwner {
        require(newTime > 0, "Time must be greater than 0");
        maxProofGenerationTime = newTime;
        emit MaxProofGenerationTimeUpdated(newTime);
    }
    
    /**
     * @dev Check if a proof request has timed out
     * @param requestId The request ID to check
     * @return True if the request has timed out
     */
    function isProofRequestTimedOut(bytes32 requestId) external view returns (bool) {
        uint256 deadline = proofTimestamps[requestId];
        if (deadline == 0) return false; // Not registered
        return block.timestamp > deadline;
    }
    
    /**
     * @dev Cancel a timed out proof request
     * @param requestId The request ID to cancel
     */
    function cancelTimedOutRequest(bytes32 requestId) external whenNotPaused {
        uint256 deadline = proofTimestamps[requestId];
        require(deadline > 0, "Request not registered");
        require(block.timestamp > deadline, "Request not timed out");
        
        // Clear the timestamp
        delete proofTimestamps[requestId];
        
        emit ProofTimeout(msg.sender, requestId);
    }
    
    /**
     * @dev Emergency pause function
     */
    function emergencyPause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Emergency unpause function
     */
    function emergencyUnpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Verify a Groth16 proof
     * @param a A parameter
     * @param b B parameter
     * @param c C parameter
     * @param input Public inputs
     * @return True if the proof is valid, false otherwise
     */
    function _verifyGroth16Proof(
        uint256[2] memory a,
        uint256[2][2] memory b,
        uint256[2] memory c,
        uint256[] memory input
    ) internal view returns (bool) {
        // Check input length
        require(input.length + 1 == verificationKey.ic.length, "Invalid input length");
        
        // Compute the linear combination of inputs and IC
        uint256[2] memory vk_x;
        vk_x[0] = verificationKey.ic[0][0];
        vk_x[1] = verificationKey.ic[0][1];
        
        for (uint i = 0; i < input.length; i++) {
            // vk_x = vk_x + input[i] * ic[i+1]
            vk_x[0] = addmod(vk_x[0], mulmod(input[i], verificationKey.ic[i+1][0], SNARK_SCALAR_FIELD), SNARK_SCALAR_FIELD);
            vk_x[1] = addmod(vk_x[1], mulmod(input[i], verificationKey.ic[i+1][1], SNARK_SCALAR_FIELD), SNARK_SCALAR_FIELD);
        }
        
        // Perform pairing check
        return _pairingCheck(
            negate(a),
            b,
            verificationKey.alpha1,
            verificationKey.beta2,
            vk_x,
            verificationKey.gamma2,
            c,
            verificationKey.delta2
        );
    }
    
    // Constants for elliptic curve operations
    uint256 constant SNARK_SCALAR_FIELD = 21888242871839275222246405745257275088548364400416034343698204186575808495617;
    uint256 constant PRIME_Q = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
    
    /**
     * @dev Negate a G1 point
     * @param p Point to negate
     * @return Negated point
     */
    function negate(uint256[2] memory p) internal pure returns (uint256[2] memory) {
        if (p[0] == 0 && p[1] == 0) {
            return p;
        }
        return [p[0], PRIME_Q - (p[1] % PRIME_Q)];
    }
    
    /**
     * @dev Perform pairing check for Groth16 verification
     * This implementation uses the precompiled contract for pairing checks
     */
    function _pairingCheck(
        uint256[2] memory a1,
        uint256[2][2] memory b1,
        uint256[2] memory a2,
        uint256[2][2] memory b2,
        uint256[2] memory a3,
        uint256[2][2] memory b3,
        uint256[2] memory a4,
        uint256[2][2] memory b4
    ) internal view returns (bool) {
        // Prepare pairing input
        uint256[24] memory input;
        
        // e(a1, b1)
        input[0] = a1[0];
        input[1] = a1[1];
        input[2] = b1[0][1]; // Note: Swap b1[0][0] and b1[0][1] for BN254 pairing
        input[3] = b1[0][0];
        input[4] = b1[1][1]; // Note: Swap b1[1][0] and b1[1][1] for BN254 pairing
        input[5] = b1[1][0];
        
        // e(a2, b2)
        input[6] = a2[0];
        input[7] = a2[1];
        input[8] = b2[0][1]; // Note: Swap b2[0][0] and b2[0][1] for BN254 pairing
        input[9] = b2[0][0];
        input[10] = b2[1][1]; // Note: Swap b2[1][0] and b2[1][1] for BN254 pairing
        input[11] = b2[1][0];
        
        // e(a3, b3)
        input[12] = a3[0];
        input[13] = a3[1];
        input[14] = b3[0][1]; // Note: Swap b3[0][0] and b3[0][1] for BN254 pairing
        input[15] = b3[0][0];
        input[16] = b3[1][1]; // Note: Swap b3[1][0] and b3[1][1] for BN254 pairing
        input[17] = b3[1][0];
        
        // e(a4, b4)
        input[18] = a4[0];
        input[19] = a4[1];
        input[20] = b4[0][1]; // Note: Swap b4[0][0] and b4[0][1] for BN254 pairing
        input[21] = b4[0][0];
        input[22] = b4[1][1]; // Note: Swap b4[1][0] and b4[1][1] for BN254 pairing
        input[23] = b4[1][0];
        
        // Call the pairing precompile at address 0x08
        // This performs the pairing check e(a1, b1) * e(a2, b2) * e(a3, b3) * e(a4, b4) == 1
        uint256[1] memory out;
        bool success;
        
        assembly {
            success := staticcall(gas(), 8, input, 768, out, 32)
        }
        
        require(success, "Pairing check failed");
        return out[0] == 1;
    }
}