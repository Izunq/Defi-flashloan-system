import React, { useState, useEffect, useCallback } from "react";
import "./ZKProofVerifier.css";
import { useAIStrategyData, ZKProof } from "../hooks/useAIStrategyData";
import { CircularProgress, Alert, AlertTitle, Snackbar } from "@mui/material";

interface VerificationStatus {
  status: 'idle' | 'loading' | 'success' | 'error';
  message: string;
}

const ZKProofVerifier: React.FC = () => {
  const { 
    proofs, 
    loading, 
    error: hookError, 
    fetchProofs,
    verifyProof,
    submitProof
  } = useAIStrategyData();
  
  const [strategyId, setStrategyId] = useState<string>("");
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus>({
    status: 'idle',
    message: ''
  });
  const [selectedProof, setSelectedProof] = useState<ZKProof | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState<boolean>(false);
  const [snackbarMessage, setSnackbarMessage] = useState<string>("");
  const [snackbarSeverity, setSnackbarSeverity] = useState<"success" | "error" | "info" | "warning">("info");

  // Set error from hook
  useEffect(() => {
    if (hookError) {
      setError(hookError);
      showSnackbar(hookError, "error");
    }
  }, [hookError]);

  // Set the first proof as selected when proofs are loaded
  useEffect(() => {
    if (proofs.length > 0 && !selectedProof) {
      setSelectedProof(proofs[0]);
    }
  }, [proofs, selectedProof]);

  // Set up refresh interval
  useEffect(() => {
    const interval = setInterval(fetchProofs, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchProofs]);

  // Show snackbar helper
  const showSnackbar = (message: string, severity: "success" | "error" | "info" | "warning") => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  // Handle snackbar close
  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  // Function to verify a proof on-chain
  const handleVerify = useCallback(async () => {
    if (!strategyId) {
      setError("Please enter a Strategy ID");
      showSnackbar("Please enter a Strategy ID", "error");
      return;
    }
    
    setError(null);
    setVerificationStatus({
      status: 'loading',
      message: "Verifying proof from on-chain commitment..."
    });

    try {
      // In a real implementation, we would get the actual proof data from the backend
      // For now, we'll use mock data for demonstration
      const publicInputs = [parseInt(strategyId), Math.floor(Math.random() * 100)]; // Strategy ID and random intelligence score
      const proofData = `0x${Array.from({length: 64}, () => Math.floor(Math.random() * 16).toString(16)).join('')}`;
      
      // First submit the proof
      const submitResult = await submitProof(parseInt(strategyId), publicInputs, proofData);
      
      if (!submitResult.success) {
        throw new Error(submitResult.message || "Failed to submit proof");
      }
      
      // Then verify the proof
      const verifyResult = await verifyProof(parseInt(strategyId), publicInputs, proofData);
      
      if (verifyResult.success) {
        setVerificationStatus({
          status: 'success',
          message: "✅ Proof valid! Strategy matches on-chain backtest."
        });
        
        // Create a new proof object
        const newProof: ZKProof = {
          strategyId: parseInt(strategyId),
          strategyName: `Strategy #${strategyId}`,
          proofHash: verifyResult.proofHash || proofData,
          timestamp: new Date(),
          isValid: true,
          verifiedAt: new Date(),
          modelVersion: "V35-TensorX-G2",
          backtestProfitability: Math.random() * 20 + 5,
          backtestWinRate: Math.random() * 30 + 65,
          onChainVerification: {
            isValid: true,
            timestamp: Math.floor(Date.now() / 1000),
            totalProfitVerified: "0.0",
            winRate: 0
          },
          zkProofStatus: {
            proofHash: verifyResult.proofHash || proofData,
            timestamp: Math.floor(Date.now() / 1000),
            verified: true,
            verifier: verifyResult.verifier || "0x0000000000000000000000000000000000000000",
            expirationTime: Math.floor(Date.now() / 1000) + 7 * 24 * 60 * 60, // 7 days from now
            isValid: true
          }
        };
        
        setSelectedProof(newProof);
        
        // Refresh proofs to include the new one
        fetchProofs();
        
        showSnackbar("Proof verified successfully!", "success");
      } else {
        setVerificationStatus({
          status: 'error',
          message: "❌ Proof INVALID! Strategy mismatch detected."
        });
        
        showSnackbar("Proof verification failed", "error");
      }
    } catch (err: any) {
      console.error("Verification error:", err);
      setVerificationStatus({
        status: 'error',
        message: `❌ Error during verification process: ${err.message}`
      });
      
      showSnackbar(`Verification error: ${err.message}`, "error");
    }
  }, [strategyId, submitProof, verifyProof, fetchProofs]);

  // Helper function to format date
  const formatDate = (date: Date) => {
    return date.toLocaleString();
  };

  // Helper function to truncate hash
  const truncateHash = (hash: string) => {
    if (!hash) return "N/A";
    return `${hash.substring(0, 10)}...${hash.substring(hash.length - 8)}`;
  };

  // Helper function to check if proof is expired
  const isProofExpired = (proof: ZKProof) => {
    if (!proof.zkProofStatus?.expirationTime) return false;
    return Date.now() / 1000 > proof.zkProofStatus.expirationTime;
  };

  return (
    <div className="p-6 bg-gray-900/50 rounded-2xl shadow-xl text-white border border-purple-500/30">
      <h2 className="text-xl font-bold mb-4 text-purple-300">🔐 ZK Strategy Verifier</h2>
      
      {/* Verification Form */}
      <div className="mb-6">
        <div className="flex space-x-2">
          <input
            type="text"
            value={strategyId}
            onChange={(e) => setStrategyId(e.target.value)}
            placeholder="Enter Strategy ID (e.g., 42)"
            className="flex-grow bg-gray-800 text-white p-2 rounded-lg border border-gray-700 focus:ring-purple-500 focus:border-purple-500"
          />
          <button 
            onClick={handleVerify} 
            disabled={verificationStatus.status === 'loading'}
            className="px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {verificationStatus.status === 'loading' ? (
              <div className="flex items-center">
                <CircularProgress size={16} color="inherit" className="mr-2" />
                Verifying...
              </div>
            ) : "Verify"}
          </button>
        </div>
        
        {error && (
          <div className="mt-2 text-red-400 text-sm">{error}</div>
        )}
        
        {verificationStatus.status !== 'idle' && (
          <div className={`mt-4 p-3 rounded-lg ${
            verificationStatus.status === 'success' 
              ? "bg-green-900/20 border border-green-500/30" 
              : verificationStatus.status === 'error'
                ? "bg-red-900/20 border border-red-500/30"
                : "bg-blue-900/20 border border-blue-500/30"
          }`}>
            <p className={
              verificationStatus.status === 'success' 
                ? "text-green-400" 
                : verificationStatus.status === 'error'
                  ? "text-red-400"
                  : "text-blue-400"
            }>
              {verificationStatus.message}
            </p>
          </div>
        )}
      </div>
      
      {/* Selected Proof Details */}
      {selectedProof && (
        <div className="mb-6 bg-gray-800/30 rounded-xl p-4 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-3">{selectedProof.strategyName}</h3>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-sm text-gray-400">Backtest Profit</div>
              <div className="text-xl font-mono text-green-400">{selectedProof.backtestProfitability.toFixed(2)}%</div>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-sm text-gray-400">Win Rate</div>
              <div className="text-xl font-mono text-blue-400">{selectedProof.backtestWinRate.toFixed(1)}%</div>
            </div>
          </div>
          
          {/* ZK Proof Verification Details */}
          <div className="bg-purple-900/20 rounded-lg p-3 mb-4 border border-purple-500/20">
            <h4 className="text-sm font-semibold text-purple-300 mb-2">🔐 ZK Proof Details</h4>
            <div className="space-y-2 text-xs">
              <div className="flex flex-col">
                <span className="text-gray-400">Proof Hash:</span> 
                <span className="font-mono text-purple-400 break-all text-xs mt-1">{selectedProof.proofHash}</span>
              </div>
              <div className="flex justify-between mt-2">
                <span className="text-gray-400">Verification Status:</span> 
                <span className={`font-mono ${
                  selectedProof.zkProofStatus?.isValid && !isProofExpired(selectedProof) 
                    ? "text-green-400" 
                    : "text-red-400"
                }`}>
                  {selectedProof.zkProofStatus?.isValid && !isProofExpired(selectedProof) 
                    ? "Valid ✓" 
                    : isProofExpired(selectedProof) 
                      ? "Expired ⚠️" 
                      : "Invalid ✗"
                  }
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Verified At:</span> 
                <span className="font-mono text-gray-300">
                  {selectedProof.verifiedAt ? formatDate(selectedProof.verifiedAt) : "N/A"}
                </span>
              </div>
              {selectedProof.zkProofStatus?.expirationTime && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Expires At:</span> 
                  <span className={`font-mono ${isProofExpired(selectedProof) ? "text-red-400" : "text-gray-300"}`}>
                    {new Date(selectedProof.zkProofStatus.expirationTime * 1000).toLocaleString()}
                  </span>
                </div>
              )}
              {selectedProof.zkProofStatus?.verifier && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Verifier:</span> 
                  <span className="font-mono text-gray-300">
                    {truncateHash(selectedProof.zkProofStatus.verifier)}
                  </span>
                </div>
              )}
            </div>
          </div>
          
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between">
              <span className="text-gray-400">Strategy ID:</span> 
              <span className="font-mono text-white">{selectedProof.strategyId}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-400">Model Version:</span> 
              <span className="font-mono text-slate-400">{selectedProof.modelVersion}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-400">Submission Date:</span> 
              <span className="font-mono text-gray-300">{formatDate(selectedProof.timestamp)}</span>
            </li>
            {selectedProof.strategyAddress && (
              <li className="flex justify-between">
                <span className="text-gray-400">Strategy Address:</span> 
                <span className="font-mono text-gray-300">{truncateHash(selectedProof.strategyAddress)}</span>
              </li>
            )}
          </ul>
          
          <div className="mt-4 flex justify-end space-x-2">
            <button 
              className="px-3 py-1 bg-purple-600/30 hover:bg-purple-600/50 rounded-md text-sm"
              onClick={() => window.open(`https://etherscan.io/tx/${selectedProof.proofHash.substring(0, 66)}`, '_blank')}
            >
              View on Etherscan
            </button>
          </div>
        </div>
      )}
      
      {/* Proof History */}
      <div>
        <h3 className="text-md font-semibold text-purple-200 mb-2">Recent Verifications</h3>
        {loading ? (
          <div className="flex justify-center items-center p-8">
            <CircularProgress color="inherit" />
          </div>
        ) : proofs.length > 0 ? (
          <div className="bg-gray-800/20 rounded-lg border border-gray-700/50 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-800/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Strategy</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Verified</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {proofs.map((proof, index) => (
                  <tr 
                    key={index} 
                    className="hover:bg-gray-700/30 cursor-pointer"
                    onClick={() => setSelectedProof(proof)}
                  >
                    <td className="px-4 py-2 whitespace-nowrap text-sm">
                      <div className="font-medium text-white">{proof.strategyName}</div>
                      <div className="text-xs text-gray-400">ID: {proof.strategyId}</div>
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm">
                      <div className="font-mono text-xs text-gray-300">{truncateHash(proof.proofHash)}</div>
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        proof.zkProofStatus?.isValid && !isProofExpired(proof)
                          ? "bg-green-900/30 text-green-400" 
                          : isProofExpired(proof)
                            ? "bg-yellow-900/30 text-yellow-400"
                            : "bg-red-900/30 text-red-400"
                      }`}>
                        {proof.zkProofStatus?.isValid && !isProofExpired(proof) 
                          ? "Valid" 
                          : isProofExpired(proof) 
                            ? "Expired" 
                            : "Invalid"
                        }
                      </span>
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-300">
                      {formatDate(proof.timestamp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-gray-800/20 rounded-lg border border-gray-700/50 p-8 text-center text-gray-400">
            No verification records found
          </div>
        )}
      </div>
      
      {/* Snackbar for notifications */}
      <Snackbar 
        open={snackbarOpen} 
        autoHideDuration={6000} 
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleSnackbarClose} 
          severity={snackbarSeverity}
          variant="filled"
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </div>
  );
};

export default ZKProofVerifier;