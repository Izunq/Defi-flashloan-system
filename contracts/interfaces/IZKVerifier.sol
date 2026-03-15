// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title IZKVerifier
 * @notice Interface for ZK proof verification
 * @dev Implement this

interface to verify ZK proofs
 */

interface IZKVerifier {
    /**
     * @dev Get the verification key hash
     * @return Hash of the verification key
     */
    function getVerificationKeyHash() external view returns (bytes32);
    
    /**
     * @dev Verify a ZK proof
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
    ) external returns (bool);
    
    /**
     * @dev Get the next nonce for a prover
     * @return The next nonce for the caller
     */
    function getNextNonce() external returns (uint256);
    
    /**
     * @dev Register a proof generation request
     * @param requestId Unique identifier for the proof request
     * @return Timestamp when the proof should be ready by
     */
    function registerProofRequest(bytes32 requestId) external returns (uint256);
    
    /**
     * @dev Check if a proof request has timed out
     * @param requestId The request ID to check
     * @return True if the request has timed out
     */
    function isProofRequestTimedOut(bytes32 requestId) external view returns (bool);
    
    /**
     * @dev Cancel a timed out proof request
     * @param requestId The request ID to cancel
     */
    function cancelTimedOutRequest(bytes32 requestId) external;
    
    /**
     * @dev Create a batch verification request
     * @param proofs Array of proofs to verify
     * @param publicInputsArray Array of public inputs for each proof
     * @return batchId Unique identifier for this batch
     */
    function createBatchVerification(
        bytes[] calldata proofs,
        uint256[][] calldata publicInputsArray
    ) external returns (bytes32);
    
    /**
     * @dev Process a batch verification
     * @param batchId Batch ID to process
     * @param proofs Array of proofs to verify
     * @param publicInputsArray Array of public inputs for each proof
     * @return successCount Number of successful verifications
     */
    function processBatchVerification(
        bytes32 batchId,
        bytes[] calldata proofs,
        uint256[][] calldata publicInputsArray
    ) external returns (uint256);
}
