import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ethers } from 'ethers';
import { toast } from 'react-toastify';

// Define supported networks
const SUPPORTED_NETWORKS = {
  1: {
    name: 'Ethereum Mainnet',
    rpcUrl: 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY',
    blockExplorer: 'https://etherscan.io',
    nativeCurrency: {
      name: 'Ether',
      symbol: 'ETH',
      decimals: 18
    }
  },
  137: {
    name: 'Polygon Mainnet',
    rpcUrl: 'https://polygon-rpc.com',
    blockExplorer: 'https://polygonscan.com',
    nativeCurrency: {
      name: 'MATIC',
      symbol: 'MATIC',
      decimals: 18
    }
  },
  56: {
    name: 'Binance Smart Chain',
    rpcUrl: 'https://bsc-dataseed.binance.org',
    blockExplorer: 'https://bscscan.com',
    nativeCurrency: {
      name: 'BNB',
      symbol: 'BNB',
      decimals: 18
    }
  },
  42161: {
    name: 'Arbitrum One',
    rpcUrl: 'https://arb1.arbitrum.io/rpc',
    blockExplorer: 'https://arbiscan.io',
    nativeCurrency: {
      name: 'Ether',
      symbol: 'ETH',
      decimals: 18
    }
  },
  10: {
    name: 'Optimism',
    rpcUrl: 'https://mainnet.optimism.io',
    blockExplorer: 'https://optimistic.etherscan.io',
    nativeCurrency: {
      name: 'Ether',
      symbol: 'ETH',
      decimals: 18
    }
  },
  // Add testnet support
  5: {
    name: 'Goerli Testnet',
    rpcUrl: 'https://goerli.infura.io/v3/YOUR_INFURA_KEY',
    blockExplorer: 'https://goerli.etherscan.io',
    nativeCurrency: {
      name: 'Goerli Ether',
      symbol: 'ETH',
      decimals: 18
    }
  },
  80001: {
    name: 'Mumbai Testnet',
    rpcUrl: 'https://rpc-mumbai.maticvigil.com',
    blockExplorer: 'https://mumbai.polygonscan.com',
    nativeCurrency: {
      name: 'MATIC',
      symbol: 'MATIC',
      decimals: 18
    }
  }
};

// Contract addresses by network
const CONTRACT_ADDRESSES = {
  // Mainnet addresses
  1: {
    arbitrageExecutor: '0x0000000000000000000000000000000000000000',
    arbitrageVault: '0x0000000000000000000000000000000000000000',
    strategyIncubator: '0x0000000000000000000000000000000000000000',
    trustCurve: '0x0000000000000000000000000000000000000000'
  },
  137: {
    arbitrageExecutor: '0x0000000000000000000000000000000000000000',
    arbitrageVault: '0x0000000000000000000000000000000000000000',
    strategyIncubator: '0x0000000000000000000000000000000000000000',
    trustCurve: '0x0000000000000000000000000000000000000000'
  },
  // Testnet addresses
  5: {
    arbitrageExecutor: '0x0000000000000000000000000000000000000000',
    arbitrageVault: '0x0000000000000000000000000000000000000000',
    strategyIncubator: '0x0000000000000000000000000000000000000000',
    trustCurve: '0x0000000000000000000000000000000000000000'
  },
  80001: {
    arbitrageExecutor: '0x0000000000000000000000000000000000000000',
    arbitrageVault: '0x0000000000000000000000000000000000000000',
    strategyIncubator: '0x0000000000000000000000000000000000000000',
    trustCurve: '0x0000000000000000000000000000000000000000'
  }
};

// Network type
interface NetworkInfo {
  name: string;
  rpcUrl: string;
  blockExplorer: string;
  nativeCurrency: {
    name: string;
    symbol: string;
    decimals: number;
  };
}

// Contract addresses type
interface ContractAddresses {
  arbitrageExecutor: string;
  arbitrageVault: string;
  strategyIncubator: string;
  trustCurve: string;
}

// Web3 context type
interface Web3ContextType {
  provider: ethers.providers.Web3Provider | null;
  signer: ethers.Signer | null;
  account: string | null;
  chainId: number | null;
  networkInfo: NetworkInfo | null;
  contractAddresses: ContractAddresses | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  switchNetwork: (chainId: number) => Promise<void>;
  getBalance: () => Promise<string>;
  isNetworkSupported: boolean;
  getExplorerUrl: (txHashOrAddress: string) => string;
}

const Web3Context = createContext<Web3ContextType | undefined>(undefined);

interface Web3ProviderProps {
  children: ReactNode;
}

export const Web3Provider: React.FC<Web3ProviderProps> = ({ children }) => {
  const [provider, setProvider] = useState<ethers.providers.Web3Provider | null>(null);
  const [signer, setSigner] = useState<ethers.Signer | null>(null);
  const [account, setAccount] = useState<string | null>(null);
  const [chainId, setChainId] = useState<number | null>(null);
  const [networkInfo, setNetworkInfo] = useState<NetworkInfo | null>(null);
  const [contractAddresses, setContractAddresses] = useState<ContractAddresses | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isNetworkSupported, setIsNetworkSupported] = useState(false);

  // Connect wallet
  const connectWallet = async () => {
    try {
      setIsConnecting(true);
      setError(null);

      if (!window.ethereum) {
        throw new Error('MetaMask is not installed. Please install MetaMask to use this application.');
      }

      // Request account access
      await window.ethereum.request({ method: 'eth_requestAccounts' });

      // Create provider and signer
      const web3Provider = new ethers.providers.Web3Provider(window.ethereum);
      const web3Signer = web3Provider.getSigner();
      const userAccount = await web3Signer.getAddress();
      const network = await web3Provider.getNetwork();
      const currentChainId = network.chainId;

      // Check if network is supported
      const isSupported = Boolean(SUPPORTED_NETWORKS[currentChainId as keyof typeof SUPPORTED_NETWORKS]);
      setIsNetworkSupported(isSupported);

      // Set network info
      if (isSupported) {
        setNetworkInfo(SUPPORTED_NETWORKS[currentChainId as keyof typeof SUPPORTED_NETWORKS]);
        setContractAddresses(CONTRACT_ADDRESSES[currentChainId as keyof typeof CONTRACT_ADDRESSES] || null);
      } else {
        toast.warning(`Network not supported. Please switch to a supported network.`);
      }

      setProvider(web3Provider);
      setSigner(web3Signer);
      setAccount(userAccount);
      setChainId(currentChainId);
      setIsConnected(true);

      // Store connection state
      localStorage.setItem('walletConnected', 'true');

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect wallet';
      setError(errorMessage);
      toast.error(errorMessage);
      console.error('Wallet connection error:', err);
    } finally {
      setIsConnecting(false);
    }
  };

  // Disconnect wallet
  const disconnectWallet = () => {
    setProvider(null);
    setSigner(null);
    setAccount(null);
    setChainId(null);
    setNetworkInfo(null);
    setContractAddresses(null);
    setIsConnected(false);
    setIsNetworkSupported(false);
    setError(null);
    localStorage.removeItem('walletConnected');
    toast.info('Wallet disconnected');
  };

  // Switch network
  const switchNetwork = async (targetChainId: number) => {
    if (!window.ethereum) {
      throw new Error('MetaMask is not installed');
    }

    try {
      // Check if network is supported
      if (!SUPPORTED_NETWORKS[targetChainId as keyof typeof SUPPORTED_NETWORKS]) {
        throw new Error('Network not supported');
      }

      // Try to switch to the network
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: `0x${targetChainId.toString(16)}` }],
      });

      // Network switch will trigger chainChanged event which will update state

    } catch (switchError: any) {
      // This error code indicates that the chain has not been added to MetaMask
      if (switchError.code === 4902) {
        try {
          const network = SUPPORTED_NETWORKS[targetChainId as keyof typeof SUPPORTED_NETWORKS];
          
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [
              {
                chainId: `0x${targetChainId.toString(16)}`,
                chainName: network.name,
                nativeCurrency: network.nativeCurrency,
                rpcUrls: [network.rpcUrl],
                blockExplorerUrls: [network.blockExplorer],
              },
            ],
          });
          
          // Try switching again after adding
          await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: `0x${targetChainId.toString(16)}` }],
          });
          
        } catch (addError) {
          const errorMessage = addError instanceof Error ? addError.message : 'Failed to add network';
          setError(errorMessage);
          toast.error(errorMessage);
          throw addError;
        }
      } else {
        const errorMessage = switchError instanceof Error ? switchError.message : 'Failed to switch network';
        setError(errorMessage);
        toast.error(errorMessage);
        throw switchError;
      }
    }
  };

  // Get native token balance
  const getBalance = async (): Promise<string> => {
    if (!provider || !account) {
      return '0.0';
    }

    try {
      const balance = await provider.getBalance(account);
      return ethers.utils.formatEther(balance);
    } catch (error) {
      console.error('Error fetching balance:', error);
      return '0.0';
    }
  };

  // Get explorer URL for transaction or address
  const getExplorerUrl = (txHashOrAddress: string): string => {
    if (!networkInfo) {
      return '';
    }

    // Check if it's a transaction hash or address
    const isTxHash = txHashOrAddress.length === 66 && txHashOrAddress.startsWith('0x');
    
    if (isTxHash) {
      return `${networkInfo.blockExplorer}/tx/${txHashOrAddress}`;
    } else {
      return `${networkInfo.blockExplorer}/address/${txHashOrAddress}`;
    }
  };

  // Auto-connect if previously connected
  useEffect(() => {
    const autoConnect = async () => {
      if (localStorage.getItem('walletConnected') === 'true' && window.ethereum) {
        try {
          const accounts = await window.ethereum.request({ method: 'eth_accounts' });
          if (accounts.length > 0) {
            await connectWallet();
          }
        } catch (err) {
          console.error('Auto-connect failed:', err);
        }
      }
    };

    autoConnect();
  }, []);

  // Listen for account changes
  useEffect(() => {
    if (window.ethereum) {
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          disconnectWallet();
          toast.info('Wallet disconnected');
        } else if (accounts[0] !== account) {
          // Update account
          setAccount(accounts[0]);
          toast.info('Account changed');
        }
      };

      const handleChainChanged = (chainIdHex: string) => {
        const newChainId = parseInt(chainIdHex, 16);
        setChainId(newChainId);
        
        // Check if network is supported
        const isSupported = Boolean(SUPPORTED_NETWORKS[newChainId as keyof typeof SUPPORTED_NETWORKS]);
        setIsNetworkSupported(isSupported);
        
        // Update network info
        if (isSupported) {
          setNetworkInfo(SUPPORTED_NETWORKS[newChainId as keyof typeof SUPPORTED_NETWORKS]);
          setContractAddresses(CONTRACT_ADDRESSES[newChainId as keyof typeof CONTRACT_ADDRESSES] || null);
          toast.info(`Network changed to ${SUPPORTED_NETWORKS[newChainId as keyof typeof SUPPORTED_NETWORKS].name}`);
        } else {
          setNetworkInfo(null);
          setContractAddresses(null);
          toast.warning('Network not supported. Please switch to a supported network.');
        }
        
        // Reconnect with new chain
        connectWallet();
      };

      const handleDisconnect = (error: { code: number; message: string }) => {
        console.log('Wallet disconnected:', error);
        disconnectWallet();
        toast.error('Wallet disconnected: ' + error.message);
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);
      window.ethereum.on('disconnect', handleDisconnect);

      return () => {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
        window.ethereum.removeListener('chainChanged', handleChainChanged);
        window.ethereum.removeListener('disconnect', handleDisconnect);
      };
    }
  }, [account]);

  const value: Web3ContextType = {
    provider,
    signer,
    account,
    chainId,
    networkInfo,
    contractAddresses,
    isConnected,
    isConnecting,
    error,
    connectWallet,
    disconnectWallet,
    switchNetwork,
    getBalance,
    isNetworkSupported,
    getExplorerUrl
  };

  return <Web3Context.Provider value={value}>{children}</Web3Context.Provider>;
};

export const useWeb3 = (): Web3ContextType => {
  const context = useContext(Web3Context);
  if (context === undefined) {
    throw new Error('useWeb3 must be used within a Web3Provider');
  }
  return context;
};

// Extend Window interface for TypeScript
declare global {
  interface Window {
    ethereum?: any;
  }
}