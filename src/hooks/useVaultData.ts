import { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';
import { useWeb3 } from '../components/Web3Provider';
import { toast } from 'react-toastify';

// Import ABI
import ArbitrageVaultERC4626ABI from '../../abi/ArbitrageVaultERC4626.json';

interface VaultStats {
  totalAssets: string;
  totalShares: string;
  totalProfit: string;
  lastProfitTime: Date | null;
  performanceFee: string;
  managementFee: string;
  isEmergencyActive: boolean;
}

interface VaultLimits {
  minDeposit: string;
  maxDeposit: string;
  maxWithdrawal: string;
  maxTotalAssets: string;
  cooldownPeriod: number;
}

interface UserPosition {
  shares: string;
  assets: string;
  depositTimestamp: Date | null;
  canWithdraw: boolean;
  withdrawalAvailableTime: Date | null;
}

interface VaultData {
  vaultStats: VaultStats | null;
  vaultLimits: VaultLimits | null;
  userPosition: UserPosition | null;
  assetSymbol: string;
  assetDecimals: number;
  vaultName: string;
  vaultSymbol: string;
  loading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
  deposit: (amount: string) => Promise<string>;
  withdraw: (amount: string) => Promise<string>;
  getMaxDeposit: () => Promise<string>;
  getMaxWithdraw: () => Promise<string>;
}

export const useVaultData = (): VaultData => {
  const { provider, signer, account, contractAddresses, isConnected } = useWeb3();
  
  const [vaultStats, setVaultStats] = useState<VaultStats | null>(null);
  const [vaultLimits, setVaultLimits] = useState<VaultLimits | null>(null);
  const [userPosition, setUserPosition] = useState<UserPosition | null>(null);
  const [assetSymbol, setAssetSymbol] = useState<string>('');
  const [assetDecimals, setAssetDecimals] = useState<number>(18);
  const [vaultName, setVaultName] = useState<string>('');
  const [vaultSymbol, setVaultSymbol] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Initialize vault contract
  const getVaultContract = useCallback(() => {
    if (!provider || !contractAddresses?.arbitrageVault) {
      return null;
    }
    
    return new ethers.Contract(
      contractAddresses.arbitrageVault,
      ArbitrageVaultERC4626ABI,
      signer || provider
    );
  }, [provider, signer, contractAddresses]);
  
  // Get asset contract
  const getAssetContract = useCallback(async () => {
    const vaultContract = getVaultContract();
    if (!vaultContract || !provider) {
      return null;
    }
    
    try {
      const assetAddress = await vaultContract.asset();
      return new ethers.Contract(
        assetAddress,
        [
          'function symbol() view returns (string)',
          'function decimals() view returns (uint8)',
          'function balanceOf(address) view returns (uint256)',
          'function allowance(address, address) view returns (uint256)',
          'function approve(address, uint256) returns (bool)'
        ],
        signer || provider
      );
    } catch (err) {
      console.error('Error getting asset contract:', err);
      return null;
    }
  }, [provider, signer, getVaultContract]);
  
  // Refresh all data
  const refreshData = useCallback(async () => {
    if (!isConnected || !provider || !contractAddresses?.arbitrageVault) {
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const vaultContract = getVaultContract();
      if (!vaultContract) {
        throw new Error('Vault contract not initialized');
      }
      
      // Get vault name and symbol
      const [name, symbol] = await Promise.all([
        vaultContract.name(),
        vaultContract.symbol()
      ]);
      
      setVaultName(name);
      setVaultSymbol(symbol);
      
      // Get asset info
      const assetContract = await getAssetContract();
      if (assetContract) {
        const [symbol, decimals] = await Promise.all([
          assetContract.symbol(),
          assetContract.decimals()
        ]);
        
        setAssetSymbol(symbol);
        setAssetDecimals(decimals);
      }
      
      // Get vault stats
      const stats = await vaultContract.getVaultStats();
      setVaultStats({
        totalAssets: ethers.utils.formatUnits(stats.totalAssets, assetDecimals),
        totalShares: ethers.utils.formatEther(stats.totalShares),
        totalProfit: ethers.utils.formatUnits(stats.totalProfit, assetDecimals),
        lastProfitTime: stats.lastProfitTime.toNumber() > 0 ? new Date(stats.lastProfitTime.toNumber() * 1000) : null,
        performanceFee: (stats.currentPerformanceFee.toNumber() / 100).toFixed(2) + '%',
        managementFee: (stats.currentManagementFee.toNumber() / 100).toFixed(2) + '%',
        isEmergencyActive: stats.isEmergencyActive
      });
      
      // Get vault limits
      const limits = await vaultContract.getVaultLimits();
      setVaultLimits({
        minDeposit: ethers.utils.formatUnits(limits.minDepositAmount, assetDecimals),
        maxDeposit: limits.maxDepositAmount.eq(0) ? 'Unlimited' : ethers.utils.formatUnits(limits.maxDepositAmount, assetDecimals),
        maxWithdrawal: limits.maxWithdrawalAmount.eq(0) ? 'Unlimited' : ethers.utils.formatUnits(limits.maxWithdrawalAmount, assetDecimals),
        maxTotalAssets: limits.maxTotalAssetsAmount.eq(0) ? 'Unlimited' : ethers.utils.formatUnits(limits.maxTotalAssetsAmount, assetDecimals),
        cooldownPeriod: limits.cooldownPeriod.toNumber()
      });
      
      // Get user position if account is connected
      if (account) {
        const [shares, lastDepositTime] = await Promise.all([
          vaultContract.balanceOf(account),
          vaultContract.lastDepositTimestamp(account)
        ]);
        
        const assets = await vaultContract.convertToAssets(shares);
        const depositTime = lastDepositTime.toNumber() > 0 ? new Date(lastDepositTime.toNumber() * 1000) : null;
        
        // Calculate if user can withdraw
        let canWithdraw = true;
        let withdrawalAvailableTime = null;
        
        if (depositTime && limits.cooldownPeriod.toNumber() > 0) {
          const cooldownEnd = new Date(depositTime.getTime() + (limits.cooldownPeriod.toNumber() * 1000));
          canWithdraw = cooldownEnd <= new Date();
          withdrawalAvailableTime = cooldownEnd;
        }
        
        setUserPosition({
          shares: ethers.utils.formatEther(shares),
          assets: ethers.utils.formatUnits(assets, assetDecimals),
          depositTimestamp: depositTime,
          canWithdraw,
          withdrawalAvailableTime
        });
      }
      
    } catch (err) {
      console.error('Error fetching vault data:', err);
      setError('Failed to load vault data');
      toast.error('Failed to load vault data');
    } finally {
      setLoading(false);
    }
  }, [isConnected, provider, account, contractAddresses, assetDecimals, getVaultContract, getAssetContract]);
  
  // Get max deposit amount
  const getMaxDeposit = useCallback(async (): Promise<string> => {
    if (!account || !provider) {
      return '0';
    }
    
    try {
      const vaultContract = getVaultContract();
      if (!vaultContract) {
        return '0';
      }
      
      const assetContract = await getAssetContract();
      if (!assetContract) {
        return '0';
      }
      
      // Get user's asset balance
      const userBalance = await assetContract.balanceOf(account);
      
      // Get max deposit from vault
      const maxDepositFromVault = await vaultContract.maxDeposit(account);
      
      // Return the minimum of user balance and vault max deposit
      const maxAmount = userBalance.lt(maxDepositFromVault) ? userBalance : maxDepositFromVault;
      return ethers.utils.formatUnits(maxAmount, assetDecimals);
      
    } catch (err) {
      console.error('Error getting max deposit:', err);
      return '0';
    }
  }, [account, provider, assetDecimals, getVaultContract, getAssetContract]);
  
  // Get max withdraw amount
  const getMaxWithdraw = useCallback(async (): Promise<string> => {
    if (!account || !provider) {
      return '0';
    }
    
    try {
      const vaultContract = getVaultContract();
      if (!vaultContract) {
        return '0';
      }
      
      // Get max withdraw from vault
      const maxWithdrawAmount = await vaultContract.maxWithdraw(account);
      return ethers.utils.formatUnits(maxWithdrawAmount, assetDecimals);
      
    } catch (err) {
      console.error('Error getting max withdraw:', err);
      return '0';
    }
  }, [account, provider, assetDecimals, getVaultContract]);
  
  // Deposit assets
  const deposit = useCallback(async (amount: string): Promise<string> => {
    if (!signer || !account) {
      throw new Error('Wallet not connected');
    }
    
    const vaultContract = getVaultContract();
    if (!vaultContract) {
      throw new Error('Vault contract not initialized');
    }
    
    const assetContract = await getAssetContract();
    if (!assetContract) {
      throw new Error('Asset contract not initialized');
    }
    
    try {
      // Convert amount to wei
      const amountWei = ethers.utils.parseUnits(amount, assetDecimals);
      
      // Check allowance
      const allowance = await assetContract.allowance(account, vaultContract.address);
      
      // If allowance is insufficient, request approval
      if (allowance.lt(amountWei)) {
        const approveTx = await assetContract.approve(vaultContract.address, ethers.constants.MaxUint256);
        toast.info('Approving vault to spend your tokens...');
        await approveTx.wait();
        toast.success('Approval successful');
      }
      
      // Deposit assets
      const tx = await vaultContract.deposit(amountWei, account);
      toast.info('Depositing assets to vault...');
      const receipt = await tx.wait();
      
      // Refresh data
      await refreshData();
      
      toast.success('Deposit successful');
      return receipt.transactionHash;
      
    } catch (err) {
      console.error('Deposit error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Deposit failed';
      toast.error(errorMessage);
      throw err;
    }
  }, [signer, account, assetDecimals, getVaultContract, getAssetContract, refreshData]);
  
  // Withdraw assets
  const withdraw = useCallback(async (amount: string): Promise<string> => {
    if (!signer || !account) {
      throw new Error('Wallet not connected');
    }
    
    const vaultContract = getVaultContract();
    if (!vaultContract) {
      throw new Error('Vault contract not initialized');
    }
    
    try {
      // Convert amount to wei
      const amountWei = ethers.utils.parseUnits(amount, assetDecimals);
      
      // Withdraw assets
      const tx = await vaultContract.withdraw(amountWei, account, account);
      toast.info('Withdrawing assets from vault...');
      const receipt = await tx.wait();
      
      // Refresh data
      await refreshData();
      
      toast.success('Withdrawal successful');
      return receipt.transactionHash;
      
    } catch (err) {
      console.error('Withdrawal error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Withdrawal failed';
      toast.error(errorMessage);
      throw err;
    }
  }, [signer, account, assetDecimals, getVaultContract, refreshData]);
  
  // Load data on initial render and when dependencies change
  useEffect(() => {
    refreshData();
  }, [refreshData]);
  
  return {
    vaultStats,
    vaultLimits,
    userPosition,
    assetSymbol,
    assetDecimals,
    vaultName,
    vaultSymbol,
    loading,
    error,
    refreshData,
    deposit,
    withdraw,
    getMaxDeposit,
    getMaxWithdraw
  };
};

export default useVaultData;