import React, { useState } from 'react';
import { useWeb3 } from './Web3Provider';
import useVaultData from '../hooks/useVaultData';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'react-toastify';
import './VaultDashboard.css';

const VaultDashboard: React.FC = () => {
  const { isConnected, account, connectWallet, isNetworkSupported, networkInfo } = useWeb3();
  const {
    vaultStats,
    vaultLimits,
    userPosition,
    assetSymbol,
    vaultName,
    vaultSymbol,
    loading,
    error,
    refreshData,
    deposit,
    withdraw,
    getMaxDeposit,
    getMaxWithdraw
  } = useVaultData();

  const [depositAmount, setDepositAmount] = useState<string>('');
  const [withdrawAmount, setWithdrawAmount] = useState<string>('');
  const [isDepositing, setIsDepositing] = useState<boolean>(false);
  const [isWithdrawing, setIsWithdrawing] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'deposit' | 'withdraw'>('deposit');

  // Format time ago
  const formatTimeAgo = (date: Date | null) => {
    if (!date) return 'Never';
    return formatDistanceToNow(date, { addSuffix: true });
  };

  // Format cooldown period
  const formatCooldown = (seconds: number) => {
    if (seconds === 0) return 'No cooldown';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days} day${days > 1 ? 's' : ''}`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''}`;
    return `${minutes} minute${minutes > 1 ? 's' : ''}`;
  };

  // Handle max deposit
  const handleMaxDeposit = async () => {
    try {
      const maxAmount = await getMaxDeposit();
      setDepositAmount(maxAmount);
    } catch (err) {
      console.error('Error getting max deposit:', err);
      toast.error('Failed to get maximum deposit amount');
    }
  };

  // Handle max withdraw
  const handleMaxWithdraw = async () => {
    try {
      const maxAmount = await getMaxWithdraw();
      setWithdrawAmount(maxAmount);
    } catch (err) {
      console.error('Error getting max withdraw:', err);
      toast.error('Failed to get maximum withdrawal amount');
    }
  };

  // Handle deposit
  const handleDeposit = async () => {
    if (!depositAmount || parseFloat(depositAmount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    try {
      setIsDepositing(true);
      await deposit(depositAmount);
      setDepositAmount('');
    } catch (err) {
      console.error('Deposit error:', err);
    } finally {
      setIsDepositing(false);
    }
  };

  // Handle withdraw
  const handleWithdraw = async () => {
    if (!withdrawAmount || parseFloat(withdrawAmount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    try {
      setIsWithdrawing(true);
      await withdraw(withdrawAmount);
      setWithdrawAmount('');
    } catch (err) {
      console.error('Withdraw error:', err);
    } finally {
      setIsWithdrawing(false);
    }
  };

  // Render loading state
  if (loading) {
    return (
      <div className="vault-dashboard loading">
        <div className="loading-spinner"></div>
        <p>Loading vault data...</p>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="vault-dashboard error">
        <h2>Error Loading Vault</h2>
        <p>{error}</p>
        <button onClick={refreshData}>Retry</button>
      </div>
    );
  }

  // Render not connected state
  if (!isConnected) {
    return (
      <div className="vault-dashboard not-connected">
        <h2>Arbitrage Vault</h2>
        <p>Connect your wallet to view and interact with the vault</p>
        <button onClick={connectWallet}>Connect Wallet</button>
      </div>
    );
  }

  // Render unsupported network state
  if (!isNetworkSupported) {
    return (
      <div className="vault-dashboard network-error">
        <h2>Unsupported Network</h2>
        <p>Please switch to a supported network to interact with the vault</p>
        <p>Current network: {networkInfo?.name || 'Unknown'}</p>
        <p>Supported networks: Ethereum, Polygon, BSC, Arbitrum, Optimism</p>
      </div>
    );
  }

  return (
    <div className="vault-dashboard">
      <div className="vault-header">
        <h2>{vaultName} ({vaultSymbol})</h2>
        <button className="refresh-button" onClick={refreshData}>
          <span className="refresh-icon">↻</span> Refresh
        </button>
      </div>

      {vaultStats?.isEmergencyActive && (
        <div className="emergency-banner">
          <span className="warning-icon">⚠️</span>
          <span>Emergency Shutdown Active - Withdrawals Only</span>
        </div>
      )}

      <div className="vault-stats">
        <div className="stat-card">
          <h3>Total Value Locked</h3>
          <p className="stat-value">{vaultStats?.totalAssets || '0'} {assetSymbol}</p>
        </div>
        <div className="stat-card">
          <h3>Total Profit Generated</h3>
          <p className="stat-value">{vaultStats?.totalProfit || '0'} {assetSymbol}</p>
          <p className="stat-subtitle">Last profit: {vaultStats?.lastProfitTime ? formatTimeAgo(vaultStats.lastProfitTime) : 'Never'}</p>
        </div>
        <div className="stat-card">
          <h3>Fees</h3>
          <p className="stat-value">Performance: {vaultStats?.performanceFee || '0%'}</p>
          <p className="stat-subtitle">Management: {vaultStats?.managementFee || '0%'}</p>
        </div>
      </div>

      <div className="user-position">
        <h3>Your Position</h3>
        {userPosition ? (
          <div className="position-details">
            <div className="position-stat">
              <span>Balance:</span>
              <span>{userPosition.assets} {assetSymbol}</span>
            </div>
            <div className="position-stat">
              <span>Shares:</span>
              <span>{userPosition.shares} {vaultSymbol}</span>
            </div>
            <div className="position-stat">
              <span>Last Deposit:</span>
              <span>{userPosition.depositTimestamp ? formatTimeAgo(userPosition.depositTimestamp) : 'Never'}</span>
            </div>
            <div className="position-stat">
              <span>Withdrawal Status:</span>
              <span className={userPosition.canWithdraw ? 'status-available' : 'status-locked'}>
                {userPosition.canWithdraw ? 'Available' : 'Locked'}
              </span>
            </div>
            {!userPosition.canWithdraw && userPosition.withdrawalAvailableTime && (
              <div className="position-stat">
                <span>Available In:</span>
                <span>{formatDistanceToNow(userPosition.withdrawalAvailableTime)}</span>
              </div>
            )}
          </div>
        ) : (
          <p className="no-position">You don't have any position in this vault</p>
        )}
      </div>

      <div className="vault-limits">
        <h3>Vault Limits</h3>
        <div className="limits-grid">
          <div className="limit-item">
            <span>Min Deposit:</span>
            <span>{vaultLimits?.minDeposit || '0'} {assetSymbol}</span>
          </div>
          <div className="limit-item">
            <span>Max Deposit:</span>
            <span>{vaultLimits?.maxDeposit || 'Unlimited'} {assetSymbol}</span>
          </div>
          <div className="limit-item">
            <span>Max Withdrawal:</span>
            <span>{vaultLimits?.maxWithdrawal || 'Unlimited'} {assetSymbol}</span>
          </div>
          <div className="limit-item">
            <span>Max Total Assets:</span>
            <span>{vaultLimits?.maxTotalAssets || 'Unlimited'} {assetSymbol}</span>
          </div>
          <div className="limit-item">
            <span>Withdrawal Cooldown:</span>
            <span>{vaultLimits ? formatCooldown(vaultLimits.cooldownPeriod) : 'N/A'}</span>
          </div>
        </div>
      </div>

      <div className="vault-actions">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'deposit' ? 'active' : ''}`}
            onClick={() => setActiveTab('deposit')}
            disabled={vaultStats?.isEmergencyActive}
          >
            Deposit
          </button>
          <button 
            className={`tab ${activeTab === 'withdraw' ? 'active' : ''}`}
            onClick={() => setActiveTab('withdraw')}
          >
            Withdraw
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'deposit' && (
            <div className="deposit-form">
              <div className="input-group">
                <input
                  type="number"
                  placeholder={`Amount in ${assetSymbol}`}
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  disabled={isDepositing || vaultStats?.isEmergencyActive}
                />
                <button 
                  className="max-button"
                  onClick={handleMaxDeposit}
                  disabled={isDepositing || vaultStats?.isEmergencyActive}
                >
                  MAX
                </button>
              </div>
              <button 
                className="action-button deposit-button"
                onClick={handleDeposit}
                disabled={isDepositing || !depositAmount || vaultStats?.isEmergencyActive}
              >
                {isDepositing ? 'Depositing...' : 'Deposit'}
              </button>
              {vaultStats?.isEmergencyActive && (
                <p className="action-note">Deposits are disabled during emergency shutdown</p>
              )}
            </div>
          )}

          {activeTab === 'withdraw' && (
            <div className="withdraw-form">
              <div className="input-group">
                <input
                  type="number"
                  placeholder={`Amount in ${assetSymbol}`}
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  disabled={isWithdrawing}
                />
                <button 
                  className="max-button"
                  onClick={handleMaxWithdraw}
                  disabled={isWithdrawing}
                >
                  MAX
                </button>
              </div>
              <button 
                className="action-button withdraw-button"
                onClick={handleWithdraw}
                disabled={
                  isWithdrawing || 
                  !withdrawAmount || 
                  (userPosition && !userPosition.canWithdraw && !vaultStats?.isEmergencyActive)
                }
              >
                {isWithdrawing ? 'Withdrawing...' : 'Withdraw'}
              </button>
              {userPosition && !userPosition.canWithdraw && !vaultStats?.isEmergencyActive && (
                <p className="action-note">
                  Withdrawal locked until {userPosition.withdrawalAvailableTime?.toLocaleString()}
                </p>
              )}
              {vaultStats?.isEmergencyActive && (
                <p className="action-note warning">
                  Emergency withdrawal fee: {vaultLimits?.emergencyWithdrawalFee || '1%'}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VaultDashboard;