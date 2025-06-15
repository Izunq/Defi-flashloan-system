import { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';

// Types
export enum StrategyStatus {
  Proposed = 0,
  Testing = 1,
  Approved = 2,
  Rejected = 3,
  Live = 4
}

export interface Strategy {
  id: string;
  strategyAddress: string;
  proposer: string;
  status: StrategyStatus;
  baseStrategyId: number;
  isVariant: boolean;
  proposalTimestamp: number;
  performanceScore: number;
  testsPassed: number;
  testsFailed: number;
  lastUpdated?: Date;
}

export interface IncubatorData {
  strategies: Strategy[];
  totalStrategies: number;
  activeStrategies: number;
  loading: boolean;
  error: string | null;
  walletConnected: boolean;
  walletAddress: string | null;
  connectWallet: () => Promise<void>;
  approveStrategy: (strategyId: string) => Promise<void>;
  rejectStrategy: (strategyId: string) => Promise<void>;
  promoteToLive: (strategyId: string) => Promise<void>;
  isAdmin: boolean;
}

// Contract addresses and ABIs (these would come from environment or config)
const INCUBATOR_ADDRESS = process.env.REACT_APP_INCUBATOR_ADDRESS || '';
const EXECUTOR_ADDRESS = process.env.REACT_APP_EXECUTOR_ADDRESS || '';
const RPC_URL = process.env.REACT_APP_RPC_URL || 'http://localhost:8545';

// Real ABI for StrategyIncubatorV33
const INCUBATOR_ABI = [
  "function strategyCounter() view returns (uint256)",
  "function getStrategy(uint256 _strategyId) view returns (tuple(address strategyAddress, address proposer, uint256 baseStrategyId, bool isVariant, uint8 status, uint256 proposalTimestamp, uint256 performanceScore, uint256 testsPassed, uint256 testsFailed))",
  "function getAllStrategies() view returns (tuple(address strategyAddress, address proposer, uint256 baseStrategyId, bool isVariant, uint8 status, uint256 proposalTimestamp, uint256 performanceScore, uint256 testsPassed, uint256 testsFailed)[])",
  "function getStrategiesByStatus(uint8 _status) view returns (uint256[])",
  "function approveStrategy(uint256 _strategyId) external",
  "function rejectStrategy(uint256 _strategyId) external",
  "function promoteToLive(uint256 _strategyId) external",
  "function hasRole(bytes32 role, address account) view returns (bool)",
  "event StrategyProposed(uint256 indexed strategyId, address indexed strategyAddress, address indexed proposer, uint256 baseStrategyId, bool isVariant)",
  "event StrategyStatusUpdated(uint256 indexed strategyId, uint8 newStatus)"
];

// ABI for ArbitrageExecutor
const EXECUTOR_ABI = [
  "function getStrategyStats(address strategy) view returns (uint256 totalProfit, uint256 totalExecutions)",
  "function getOverallStats() view returns (uint256 totalProfit, uint256 totalExecs)",
  "function withdrawFees(address _token, address _to, uint256 _amount) external",
  "function hasRole(bytes32 role, address account) view returns (bool)"
];

export const useIncubatorData = (): IncubatorData => {
  const [data, setData] = useState<IncubatorData>({
    strategies: [],
    totalStrategies: 0,
    activeStrategies: 0,
    loading: true,
    error: null,
    walletConnected: false,
    walletAddress: null,
    connectWallet: async () => {},
    approveStrategy: async () => {},
    rejectStrategy: async () => {},
    promoteToLive: async () => {},
    isAdmin: false
  });

  // Connect wallet function
  const connectWallet = useCallback(async () => {
    try {
      if (!window.ethereum) {
        throw new Error('MetaMask not installed');
      }

      // Request account access
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      const walletAddress = accounts[0];

      // Create ethers provider and signer
      const provider = new ethers.providers.Web3Provider(window.ethereum);
      const signer = provider.getSigner();

      // Check if user is admin
      const incubatorContract = new ethers.Contract(INCUBATOR_ADDRESS, INCUBATOR_ABI, signer);
      const adminRole = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("DEFAULT_ADMIN_ROLE"));
      const isAdmin = await incubatorContract.hasRole(adminRole, walletAddress);

      setData(prev => ({
        ...prev,
        walletConnected: true,
        walletAddress,
        isAdmin
      }));

      // Setup wallet event listeners
      window.ethereum.on('accountsChanged', (accounts: string[]) => {
        if (accounts.length === 0) {
          // User disconnected wallet
          setData(prev => ({
            ...prev,
            walletConnected: false,
            walletAddress: null,
            isAdmin: false
          }));
        } else {
          // User switched accounts
          setData(prev => ({
            ...prev,
            walletAddress: accounts[0]
          }));
          // Check admin status for new account
          checkAdminStatus(accounts[0], incubatorContract);
        }
      });

      window.ethereum.on('chainChanged', () => {
        // Refresh the page when chain changes
        window.location.reload();
      });

      return walletAddress;
    } catch (error) {
      console.error('Error connecting wallet:', error);
      setData(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to connect wallet'
      }));
      return null;
    }
  }, []);

  // Check if user is admin
  const checkAdminStatus = async (address: string, contract: ethers.Contract) => {
    try {
      const adminRole = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("DEFAULT_ADMIN_ROLE"));
      const isAdmin = await contract.hasRole(adminRole, address);
      setData(prev => ({
        ...prev,
        isAdmin
      }));
    } catch (error) {
      console.error('Error checking admin status:', error);
    }
  };

  // Governance functions
  const approveStrategy = useCallback(async (strategyId: string) => {
    try {
      if (!window.ethereum || !data.walletConnected) {
        throw new Error('Wallet not connected');
      }

      const provider = new ethers.providers.Web3Provider(window.ethereum);
      const signer = provider.getSigner();
      const contract = new ethers.Contract(INCUBATOR_ADDRESS, INCUBATOR_ABI, signer);

      // Send transaction
      const tx = await contract.approveStrategy(strategyId);
      await tx.wait();

      // Refresh data
      fetchStrategies();
    } catch (error) {
      console.error('Error approving strategy:', error);
      setData(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to approve strategy'
      }));
    }
  }, [data.walletConnected]);

  const rejectStrategy = useCallback(async (strategyId: string) => {
    try {
      if (!window.ethereum || !data.walletConnected) {
        throw new Error('Wallet not connected');
      }

      const provider = new ethers.providers.Web3Provider(window.ethereum);
      const signer = provider.getSigner();
      const contract = new ethers.Contract(INCUBATOR_ADDRESS, INCUBATOR_ABI, signer);

      // Send transaction
      const tx = await contract.rejectStrategy(strategyId);
      await tx.wait();

      // Refresh data
      fetchStrategies();
    } catch (error) {
      console.error('Error rejecting strategy:', error);
      setData(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to reject strategy'
      }));
    }
  }, [data.walletConnected]);

  const promoteToLive = useCallback(async (strategyId: string) => {
    try {
      if (!window.ethereum || !data.walletConnected) {
        throw new Error('Wallet not connected');
      }

      const provider = new ethers.providers.Web3Provider(window.ethereum);
      const signer = provider.getSigner();
      const contract = new ethers.Contract(INCUBATOR_ADDRESS, INCUBATOR_ABI, signer);

      // Send transaction
      const tx = await contract.promoteToLive(strategyId);
      await tx.wait();

      // Refresh data
      fetchStrategies();
    } catch (error) {
      console.error('Error promoting strategy:', error);
      setData(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to promote strategy'
      }));
    }
  }, [data.walletConnected]);

  const fetchStrategies = async () => {
    try {
      setData(prev => ({ ...prev, loading: true, error: null }));

      // Initialize provider
      let provider;
      let signer = null;
      
      if (window.ethereum && data.walletConnected) {
        // Use connected wallet
        provider = new ethers.providers.Web3Provider(window.ethereum);
        signer = provider.getSigner();
      } else {
        // Use RPC provider
        provider = new ethers.providers.JsonRpcProvider(RPC_URL);
      }
      
      if (!INCUBATOR_ADDRESS) {
        throw new Error('Incubator address not configured');
      }

      // Create contract instance
      const contract = new ethers.Contract(
        INCUBATOR_ADDRESS, 
        INCUBATOR_ABI, 
        signer || provider
      );

      // Get total strategy count
      const strategyCount = await contract.strategyCounter();
      const totalStrategies = strategyCount.toNumber();

      // Fetch all strategies
      const strategies: Strategy[] = [];
      let activeStrategies = 0;

      // Create executor contract instance for additional stats
      const executorContract = EXECUTOR_ADDRESS ? 
        new ethers.Contract(EXECUTOR_ADDRESS, EXECUTOR_ABI, signer || provider) : 
        null;

      for (let i = 1; i <= totalStrategies; i++) {
        try {
          const strategyData = await contract.getStrategy(i);
          
          const strategy: Strategy = {
            id: i.toString(),
            strategyAddress: strategyData.strategyAddress,
            proposer: strategyData.proposer,
            status: strategyData.status,
            baseStrategyId: strategyData.baseStrategyId.toNumber(),
            isVariant: strategyData.isVariant,
            proposalTimestamp: strategyData.proposalTimestamp.toNumber(),
            performanceScore: strategyData.performanceScore.toNumber(),
            testsPassed: strategyData.testsPassed.toNumber(),
            testsFailed: strategyData.testsFailed.toNumber(),
            lastUpdated: new Date()
          };

          // If executor contract is available, fetch additional stats
          if (executorContract && strategy.strategyAddress !== ethers.constants.AddressZero) {
            try {
              const [totalProfit, totalExecutions] = await executorContract.getStrategyStats(strategy.strategyAddress);
              
              // Add additional stats to strategy object
              (strategy as any).totalProfit = ethers.utils.formatEther(totalProfit);
              (strategy as any).totalExecutions = totalExecutions.toNumber();
            } catch (error) {
              console.warn(`Error fetching executor stats for strategy ${i}:`, error);
            }
          }

          strategies.push(strategy);

          // Count active strategies (Testing, Approved, or Live)
          if (strategy.status === StrategyStatus.Testing || 
              strategy.status === StrategyStatus.Approved || 
              strategy.status === StrategyStatus.Live) {
            activeStrategies++;
          }

        } catch (error) {
          console.error(`Error fetching strategy ${i}:`, error);
        }
      }

      // Get overall stats from executor if available
      let overallStats = null;
      if (executorContract) {
        try {
          const [totalProfit, totalExecs] = await executorContract.getOverallStats();
          overallStats = {
            totalProfit: ethers.utils.formatEther(totalProfit),
            totalExecutions: totalExecs.toNumber()
          };
        } catch (error) {
          console.warn('Error fetching overall executor stats:', error);
        }
      }

      setData(prev => ({
        ...prev,
        strategies,
        totalStrategies,
        activeStrategies,
        loading: false,
        error: null,
        overallStats,
        connectWallet,
        approveStrategy,
        rejectStrategy,
        promoteToLive
      }));

    } catch (error) {
      console.error('Error fetching incubator data:', error);
      setData(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
        connectWallet,
        approveStrategy,
        rejectStrategy,
        promoteToLive
      }));
    }
  };

  // Helper function to get status string
  const getStatusString = (status: StrategyStatus): string => {
    switch (status) {
      case StrategyStatus.Proposed:
        return 'Proposed';
      case StrategyStatus.Testing:
        return 'Testing';
      case StrategyStatus.Approved:
        return 'Approved';
      case StrategyStatus.Rejected:
        return 'Rejected';
      case StrategyStatus.Live:
        return 'Live';
      default:
        return 'Unknown';
    }
  };

  // Set up event listeners for real-time updates
  useEffect(() => {
    let contract: ethers.Contract | null = null;
    let provider: ethers.providers.Provider | null = null;

    const setupEventListeners = async () => {
      try {
        if (!INCUBATOR_ADDRESS) return;

        provider = new ethers.providers.JsonRpcProvider(RPC_URL);
        contract = new ethers.Contract(INCUBATOR_ADDRESS, INCUBATOR_ABI, provider);

        // Listen for strategy events
        contract.on('StrategyProposed', (strategyId, strategyAddress, proposer, baseStrategyId, isVariant) => {
          console.log(`New strategy proposed: ${strategyId}`);
          fetchStrategies();
        });

        contract.on('StrategyStatusUpdated', (strategyId, newStatus) => {
          console.log(`Strategy ${strategyId} status changed to ${getStatusString(newStatus)}`);
          fetchStrategies();
        });

      } catch (error) {
        console.error('Error setting up event listeners:', error);
      }
    };

    // Initial data fetch
    fetchStrategies();

    // Setup event listeners
    setupEventListeners();

    // Cleanup function
    return () => {
      if (contract) {
        contract.removeAllListeners();
      }
    };
  }, []);

  // Periodic refresh
  useEffect(() => {
    const interval = setInterval(() => {
      fetchStrategies();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Set initial functions
  useEffect(() => {
    setData(prev => ({
      ...prev,
      connectWallet,
      approveStrategy,
      rejectStrategy,
      promoteToLive
    }));
  }, [connectWallet, approveStrategy, rejectStrategy, promoteToLive]);

  return data;
};