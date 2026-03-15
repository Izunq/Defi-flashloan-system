import { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';
import axios from 'axios';

// Import ABIs
import AIStrategyV35ABI from '../../abi/AIStrategyV35.json';
import TrustCurveABI from '../../abi/TrustCurve.json';
import ProofAwareExecutorV35ABI from '../../abi/ProofAwareExecutorV35.json';
import ZKVerifierABI from '../../abi/ZKVerifier.json';

// Types for AI Strategy data
export interface AIInsight {
  strategyId: number;
  strategyName: string;
  predictedProfit: number;
  confidenceScore: number;
  sevenDayWinRate: number;
  modelVersion: string;
  timestamp: Date;
  riskScore: number;
  executionComplexity: number;
  chain: string;
}

export interface OnChainVerification {
  isValid: boolean;
  timestamp: number;
  totalProfitVerified: string;
  winRate: number;
}

export interface ZKProofStatus {
  proofHash: string;
  timestamp: number;
  verified: boolean;
  verifier: string;
  expirationTime: number;
  isValid: boolean;
}

export interface ZKProof {
  strategyId: number;
  strategyName: string;
  proofHash: string;
  timestamp: Date;
  isValid: boolean | null;
  verifiedAt: Date | null;
  modelVersion: string;
  backtestProfitability: number;
  backtestWinRate: number;
  strategyAddress?: string;
  onChainVerification?: OnChainVerification;
  zkProofStatus?: ZKProofStatus;
}

export interface PerformanceMetrics {
  totalExecutions: number;
  successRate: number;
  totalProfit: number;
  trustScore: number;
}

export interface RiskParameters {
  maxCapitalAtRisk: number;
  minProfitThreshold: number;
  maxSlippage: number;
  maxGasPrice: number;
  emergencyThreshold: number;
}

export interface VerifyProofResult {
  success: boolean;
  transactionHash?: string;
  proofHash?: string;
  verifier?: string;
  message?: string;
}

export interface SubmitProofResult {
  success: boolean;
  transactionHash?: string;
  proofHash?: string;
  timestamp?: number;
  expirationTime?: number;
  message?: string;
}

export interface AIStrategyData {
  insights: AIInsight[];
  proofs: ZKProof[];
  loading: boolean;
  error: string | null;
  fetchInsights: () => Promise<void>;
  fetchProofs: () => Promise<void>;
  verifyProof: (strategyId: number, publicInputs: number[], proof: string) => Promise<VerifyProofResult>;
  submitProof: (strategyId: number, publicInputs: number[], proof: string) => Promise<SubmitProofResult>;
  getStrategyMetrics: (strategyId: number) => Promise<PerformanceMetrics | null>;
  getRiskParameters: (strategyId: number) => Promise<RiskParameters | null>;
}

// Contract addresses (these would come from environment or config)
const TRUST_CURVE_ADDRESS = process.env.REACT_APP_TRUST_CURVE_ADDRESS || '';
const PROOF_EXECUTOR_ADDRESS = process.env.REACT_APP_PROOF_EXECUTOR_ADDRESS || '';
const ZK_VERIFIER_ADDRESS = process.env.REACT_APP_ZK_VERIFIER_ADDRESS || '';
const RPC_URL = process.env.REACT_APP_RPC_URL || 'http://localhost:8545';

// Backend proxy URL - all API calls go through our backend proxy
const BACKEND_PROXY_URL = process.env.REACT_APP_BACKEND_PROXY_URL || '/api';

// WebSocket endpoint for real-time updates
const WS_ENDPOINT = process.env.REACT_APP_WS_ENDPOINT || 'ws://localhost:8083';

export const useAIStrategyData = (): AIStrategyData => {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [proofs, setProofs] = useState<ZKProof[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    // Only connect in production environment
    if (process.env.NODE_ENV !== 'production') return;

    try {
      const ws = new WebSocket(WS_ENDPOINT);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        ws.send(JSON.stringify({ type: 'subscribe', channel: 'ai_insights' }));
        ws.send(JSON.stringify({ type: 'subscribe', channel: 'zk_proofs' }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.channel === 'ai_insights') {
            setInsights(data.insights);
          } else if (data.channel === 'zk_proofs') {
            setProofs(data.proofs);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      setSocket(ws);
      
      return () => {
        ws.close();
      };
    } catch (err) {
      console.error('Error setting up WebSocket:', err);
    }
  }, []);

  // Fetch AI insights from Python agent
  const fetchInsights = useCallback(async () => {
    try {
      setLoading(true);
      
      // In production, this would fetch from your API
      if (process.env.NODE_ENV === 'production') {
        // Use backend proxy to avoid exposing API keys in frontend
        const response = await axios.get(`${BACKEND_PROXY_URL}/ai/insights`);
        setInsights(response.data);
      } else {
        // Mock data for development
        const mockData: AIInsight[] = [
          {
            strategyId: 1,
            strategyName: "Flash Arbitrage V2 (Polygon)",
            predictedProfit: 43.20,
            confidenceScore: 92.1,
            sevenDayWinRate: 81.3,
            modelVersion: "V35-TensorX-G2",
            timestamp: new Date(),
            riskScore: 28,
            executionComplexity: 3,
            chain: "Polygon"
          },
          {
            strategyId: 2,
            strategyName: "Cross-Chain Arb (ETH-BSC)",
            predictedProfit: 67.85,
            confidenceScore: 87.4,
            sevenDayWinRate: 76.2,
            modelVersion: "V35-TensorX-G2",
            timestamp: new Date(Date.now() - 120000),
            riskScore: 42,
            executionComplexity: 7,
            chain: "Multi-Chain"
          },
          {
            strategyId: 3,
            strategyName: "Stable Swap Optimizer (Ethereum)",
            predictedProfit: 21.45,
            confidenceScore: 95.7,
            sevenDayWinRate: 93.8,
            modelVersion: "V35-TensorX-G2",
            timestamp: new Date(Date.now() - 300000),
            riskScore: 15,
            executionComplexity: 2,
            chain: "Ethereum"
          }
        ];
        
        setInsights(mockData);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching AI insights:', err);
      setError('Failed to fetch AI insights');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch ZK proofs
  const fetchProofs = useCallback(async () => {
    try {
      setLoading(true);
      
      // In production, this would fetch from your API
      if (process.env.NODE_ENV === 'production') {
        // Use backend proxy to avoid exposing API keys in frontend
        const response = await axios.get(`${BACKEND_PROXY_URL}/zk/proofs`);
        
        // Convert dates from strings to Date objects
        const proofs = response.data.map((proof: any) => ({
          ...proof,
          timestamp: new Date(proof.timestamp),
          verifiedAt: proof.verifiedAt ? new Date(proof.verifiedAt) : null
        }));
        
        setProofs(proofs);
      } else {
        // Mock data for development
        const mockData: ZKProof[] = [
          {
            strategyId: 1,
            strategyName: "Flash Arbitrage V2 (Polygon)",
            proofHash: "${CONTRACT_ADDRESS}7c8d9e0f1a2b3c4d5e6f7a8b9",
            timestamp: new Date(Date.now() - 3600000), // 1 hour ago
            isValid: true,
            verifiedAt: new Date(Date.now() - 3000000), // 50 minutes ago
            modelVersion: "V35-TensorX-G2",
            backtestProfitability: 12.5,
            backtestWinRate: 87.3,
            strategyAddress: "${CONTRACT_ADDRESS}",
            onChainVerification: {
              isValid: true,
              timestamp: Math.floor(Date.now() / 1000) - 3000,
              totalProfitVerified: "1.25",
              winRate: 87
            },
            zkProofStatus: {
              proofHash: "${CONTRACT_ADDRESS}7c8d9e0f1a2b3c4d5e6f7a8b9",
              timestamp: Math.floor(Date.now() / 1000) - 3600,
              verified: true,
              verifier: "${CONTRACT_ADDRESS}",
              expirationTime: Math.floor(Date.now() / 1000) + 604800, // 7 days from now
              isValid: true
            }
          },
          {
            strategyId: 2,
            strategyName: "Cross-Chain Arb (ETH-BSC)",
            proofHash: "${CONTRACT_ADDRESS}1c2d3e4f5a6b7c8d9e0f1a2b",
            timestamp: new Date(Date.now() - 86400000), // 1 day ago
            isValid: true,
            verifiedAt: new Date(Date.now() - 85000000), // 23.6 hours ago
            modelVersion: "V35-TensorX-G2",
            backtestProfitability: 18.7,
            backtestWinRate: 79.2,
            strategyAddress: "${CONTRACT_ADDRESS}",
            onChainVerification: {
              isValid: true,
              timestamp: Math.floor(Date.now() / 1000) - 85000,
              totalProfitVerified: "2.35",
              winRate: 79
            },
            zkProofStatus: {
              proofHash: "${CONTRACT_ADDRESS}1c2d3e4f5a6b7c8d9e0f1a2b",
              timestamp: Math.floor(Date.now() / 1000) - 86400,
              verified: true,
              verifier: "${CONTRACT_ADDRESS}",
              expirationTime: Math.floor(Date.now() / 1000) + 518400, // 6 days from now
              isValid: true
            }
          },
          {
            strategyId: 3,
            strategyName: "Stable Swap Optimizer (Ethereum)",
            proofHash: "${CONTRACT_ADDRESS}3e4f5a6b7c8d9e0f1a2b3c4d",
            timestamp: new Date(Date.now() - 172800000), // 2 days ago
            isValid: false,
            verifiedAt: new Date(Date.now() - 170000000), // 1.97 days ago
            modelVersion: "V35-TensorX-G2",
            backtestProfitability: 8.3,
            backtestWinRate: 65.8,
            strategyAddress: "${CONTRACT_ADDRESS}",
            onChainVerification: {
              isValid: false,
              timestamp: Math.floor(Date.now() / 1000) - 170000,
              totalProfitVerified: "0.0",
              winRate: 0
            },
            zkProofStatus: {
              proofHash: "${CONTRACT_ADDRESS}3e4f5a6b7c8d9e0f1a2b3c4d",
              timestamp: Math.floor(Date.now() / 1000) - 172800,
              verified: false,
              verifier: "${CONTRACT_ADDRESS}",
              expirationTime: Math.floor(Date.now() / 1000) - 86400, // Expired 1 day ago
              isValid: false
            }
          }
        ];
        
        setProofs(mockData);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching ZK proofs:', err);
      setError('Failed to fetch ZK proofs');
    } finally {
      setLoading(false);
    }
  }, []);

  // Verify a ZK proof cryptographically
  const verifyProofCryptographically = useCallback(async (publicInputs: number[], proof: string): Promise<boolean> => {
    try {
      // In production, this would use the ZK verifier contract
      if (process.env.NODE_ENV === 'production') {
        // Initialize provider
        const provider = new ethers.providers.JsonRpcProvider(RPC_URL);
        
        // Create contract instance for the ZK verifier
        const verifierContract = new ethers.Contract(ZK_VERIFIER_ADDRESS, ZKVerifierABI, provider);
        
        // Verify the proof
        return await verifierContract.verifyProof(publicInputs, proof);
      } else {
        // Mock verification for development
        return true;
      }
    } catch (err) {
      console.error('Error verifying ZK proof cryptographically:', err);
      return false;
    }
  }, []);

  // Submit a ZK proof
  const submitProof = useCallback(async (strategyId: number, publicInputs: number[], proof: string): Promise<SubmitProofResult> => {
    try {
      // First verify the proof cryptographically
      const isValid = await verifyProofCryptographically(publicInputs, proof);
      
      if (!isValid) {
        return {
          success: false,
          message: 'Proof is not cryptographically valid'
        };
      }
      
      // In production, this would submit to the API
      if (process.env.NODE_ENV === 'production') {
        // Use backend proxy to avoid exposing API keys in frontend
        const response = await axios.post(
          `${BACKEND_PROXY_URL}/zk/submit`,
          {
            strategyId,
            publicInputs,
            proof
          }
        );
        
        return {
          success: true,
          transactionHash: response.data.transactionHash,
          proofHash: response.data.proofHash,
          timestamp: response.data.timestamp,
          expirationTime: response.data.expirationTime
        };
      } else {
        // Mock response for development
        return {
          success: true,
          transactionHash: '0x' + Math.random().toString(16).substring(2, 66),
          proofHash: '0x' + Math.random().toString(16).substring(2, 66),
          timestamp: Math.floor(Date.now() / 1000),
          expirationTime: Math.floor(Date.now() / 1000) + 604800 // 7 days from now
        };
      }
    } catch (err) {
      console.error('Error submitting ZK proof:', err);
      return {
        success: false,
        message: 'Failed to submit proof'
      };
    }
  }, [verifyProofCryptographically]);

  // Verify a ZK proof on-chain
  const verifyProof = useCallback(async (strategyId: number, publicInputs: number[], proof: string): Promise<VerifyProofResult> => {
    try {
      // In production, this would verify on-chain
      if (process.env.NODE_ENV === 'production') {
        // Use backend proxy to avoid exposing API keys in frontend
        const response = await axios.post(
          `${BACKEND_PROXY_URL}/zk/verify`,
          {
            strategyId,
            publicInputs,
            proof
          }
        );
        
        return {
          success: response.data.success,
          transactionHash: response.data.transactionHash,
          proofHash: response.data.proofHash,
          verifier: response.data.verifier
        };
      } else {
        // Mock response for development
        return {
          success: true,
          transactionHash: '0x' + Math.random().toString(16).substring(2, 66),
          proofHash: '0x' + Math.random().toString(16).substring(2, 66),
          verifier: '${CONTRACT_ADDRESS}'
        };
      }
    } catch (err) {
      console.error('Error verifying ZK proof:', err);
      return {
        success: false,
        message: 'Failed to verify proof'
      };
    }
  }, []);

  // Get strategy performance metrics
  const getStrategyMetrics = useCallback(async (strategyId: number): Promise<PerformanceMetrics | null> => {
    try {
      // In production, this would fetch from your API
      if (process.env.NODE_ENV === 'production') {
        // Use backend proxy to avoid exposing API keys in frontend
        const response = await axios.get(`${BACKEND_PROXY_URL}/strategy/${strategyId}/metrics`);
        return response.data;
      } else {
        // Mock data for development
        return {
          totalExecutions: 128,
          successRate: 0.92,
          totalProfit: 1250.75,
          trustScore: 87
        };
      }
    } catch (err) {
      console.error('Error fetching strategy metrics:', err);
      return null;
    }
  }, []);

  // Get risk parameters
  const getRiskParameters = useCallback(async (strategyId: number): Promise<RiskParameters | null> => {
    try {
      // In production, this would fetch from your API
      if (process.env.NODE_ENV === 'production') {
        // Use backend proxy to avoid exposing API keys in frontend
        const response = await axios.get(`${BACKEND_PROXY_URL}/strategy/${strategyId}/risk`);
        return response.data;
      } else {
        // Mock data for development
        return {
          maxCapitalAtRisk: 5000,
          minProfitThreshold: 50,
          maxSlippage: 0.5,
          maxGasPrice: 100,
          emergencyThreshold: 0.8
        };
      }
    } catch (err) {
      console.error('Error fetching risk parameters:', err);
      return null;
    }
  }, []);

  // Load initial data
  useEffect(() => {
    fetchInsights();
    fetchProofs();
  }, [fetchInsights, fetchProofs]);

  return {
    insights,
    proofs,
    loading,
    error,
    fetchInsights,
    fetchProofs,
    verifyProof,
    submitProof,
    getStrategyMetrics,
    getRiskParameters
  };
};