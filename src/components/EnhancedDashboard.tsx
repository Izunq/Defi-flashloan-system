import React, { useState, useEffect } from 'react';
import { useIncubatorData, Strategy, StrategyStatus } from '../hooks/useIncubatorData';
import { useWeb3 } from './Web3Provider';
import { ethers } from 'ethers';
import './EnhancedDashboard.css';

// Helper to get status string
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

// Helper to get status color
const getStatusColor = (status: StrategyStatus): string => {
  switch (status) {
    case StrategyStatus.Proposed:
      return '#ffa500';
    case StrategyStatus.Testing:
      return '#2196f3';
    case StrategyStatus.Approved:
      return '#4caf50';
    case StrategyStatus.Rejected:
      return '#f44336';
    case StrategyStatus.Live:
      return '#00e676';
    default:
      return '#757575';
  }
};

interface StrategyCardProps {
  strategy: Strategy;
  isSelected: boolean;
  onSelect: (strategyId: string) => void;
}

const StrategyCard: React.FC<StrategyCardProps> = ({ strategy, isSelected, onSelect }) => {
  const statusColor = getStatusColor(strategy.status);
  
  return (
    <div 
      className={`strategy-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(strategy.id)}
    >
      <div className="strategy-header">
        <div className="strategy-id">#{strategy.id}</div>
        <div 
          className="strategy-status-badge"
          style={{ backgroundColor: statusColor }}
        >
          {getStatusString(strategy.status)}
        </div>
      </div>
      
      <div className="strategy-info">
        <div className="strategy-address">
          <strong>Address:</strong>
          <span className="address-text">
            {strategy.strategyAddress ? 
              `${strategy.strategyAddress.slice(0, 6)}...${strategy.strategyAddress.slice(-4)}` : 
              <span className="placeholder-dash">—</span>
            }
          </span>
        </div>
        
        <div className="strategy-metrics">
          <div className="metric">
            <span className="metric-label">Score:</span>
            <span className="metric-value">
              {strategy.performanceScore !== undefined ? 
                strategy.performanceScore : 
                <span className="placeholder-dash">—</span>
              }
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Tests:</span>
            <span className="metric-value">
              {strategy.testsPassed !== undefined && strategy.testsFailed !== undefined ? 
                `${strategy.testsPassed}/${strategy.testsPassed + strategy.testsFailed}` : 
                <span className="placeholder-dash">—</span>
              }
            </span>
          </div>
        </div>
        
        {strategy.isVariant && (
          <div className="variant-badge">
            Variant of {strategy.baseStrategyId ? 
              `#${strategy.baseStrategyId}` : 
              <span className="placeholder-dash">—</span>
            }
          </div>
        )}
      </div>
    </div>
  );
};

interface WalletConnectionProps {
  onConnect: () => void;
  isConnecting: boolean;
  error: string | null;
}

const WalletConnection: React.FC<WalletConnectionProps> = ({ onConnect, isConnecting, error }) => (
  <div className="wallet-connection">
    <div className="wallet-prompt">
      <h3>Connect Your Wallet</h3>
      <p>Connect your MetaMask wallet to interact with the Strategy Incubator</p>
      <button 
        onClick={onConnect} 
        disabled={isConnecting}
        className="connect-button"
      >
        {isConnecting ? 'Connecting...' : 'Connect MetaMask'}
      </button>
      {error && <div className="error-message">{error}</div>}
    </div>
  </div>
);

interface StrategyActionsProps {
  strategy: Strategy;
  onAction: (action: string, strategyId: string) => void;
  isProcessing: boolean;
}

const StrategyActions: React.FC<StrategyActionsProps> = ({ strategy, onAction, isProcessing }) => {
  const canApprove = strategy.status === StrategyStatus.Proposed || strategy.status === StrategyStatus.Testing;
  const canReject = strategy.status === StrategyStatus.Proposed || strategy.status === StrategyStatus.Testing;
  const canTest = strategy.status === StrategyStatus.Proposed;
  
  return (
    <div className="strategy-actions">
      <h4>Actions</h4>
      <div className="action-buttons">
        {canTest && (
          <button 
            onClick={() => onAction('test', strategy.id)}
            disabled={isProcessing}
            className="action-button test-button"
          >
            Run Test
          </button>
        )}
        {canApprove && (
          <button 
            onClick={() => onAction('approve', strategy.id)}
            disabled={isProcessing}
            className="action-button approve-button"
          >
            Approve
          </button>
        )}
        {canReject && (
          <button 
            onClick={() => onAction('reject', strategy.id)}
            disabled={isProcessing}
            className="action-button reject-button"
          >
            Reject
          </button>
        )}
      </div>
    </div>
  );
};

const EnhancedDashboard: React.FC = () => {
  const { strategies, loading, error, totalStrategies, activeStrategies } = useIncubatorData();
  const { 
    account, 
    chainId, 
    isConnected, 
    isConnecting, 
    error: web3Error, 
    connectWallet,
    signer 
  } = useWeb3();
  
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleSelectStrategy = (strategyId: string) => {
    setSelectedStrategyId(prevId => (prevId === strategyId ? null : strategyId));
  };

  const handleStrategyAction = async (action: string, strategyId: string) => {
    if (!signer || !isConnected) {
      setActionError('Wallet not connected');
      return;
    }

    setIsProcessing(true);
    setActionError(null);

    try {
      // Load incubator contract
      const incubatorAddress = process.env.REACT_APP_INCUBATOR_ADDRESS;
      if (!incubatorAddress) {
        throw new Error('Incubator address not configured');
      }

      // Simple ABI for the actions we need
      const incubatorABI = [
        "function updateStrategyStatus(uint256 _strategyId, uint8 _newStatus) external",
        "function recordTestResult(uint256 _strategyId, bool _passed) external"
      ];

      const contract = new ethers.Contract(incubatorAddress, incubatorABI, signer);

      let tx;
      switch (action) {
        case 'test':
          // Record a test result (for demo, always pass)
          tx = await contract.recordTestResult(parseInt(strategyId), true);
          break;
        case 'approve':
          tx = await contract.updateStrategyStatus(parseInt(strategyId), StrategyStatus.Approved);
          break;
        case 'reject':
          tx = await contract.updateStrategyStatus(parseInt(strategyId), StrategyStatus.Rejected);
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }

      // Wait for transaction confirmation
      await tx.wait();
      
      console.log(`Action ${action} completed for strategy ${strategyId}`);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Transaction failed';
      setActionError(errorMessage);
      console.error('Action error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const selectedStrategy = strategies.find(s => s.id === selectedStrategyId);

  // Show wallet connection if not connected
  if (!isConnected) {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <h1>Strategy Incubator Dashboard V33</h1>
          <div className="network-info">
            <span className="network-status disconnected">Wallet Disconnected</span>
          </div>
        </header>
        <main className="dashboard-main">
          <WalletConnection 
            onConnect={connectWallet}
            isConnecting={isConnecting}
            error={web3Error}
          />
        </main>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Strategy Incubator Dashboard V33</h1>
        <div className="header-info">
          <div className="network-info">
            <span className="network-status connected">
              Chain ID: {chainId}
            </span>
            <span className="account-info">
              {account?.slice(0, 6)}...{account?.slice(-4)}
            </span>
          </div>
          <div className="stats-summary">
            <div className="stat">
              <span className="stat-value">{totalStrategies}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat">
              <span className="stat-value">{activeStrategies}</span>
              <span className="stat-label">Active</span>
            </div>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        {loading && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <span>Loading strategies...</span>
          </div>
        )}

        {error && (
          <div className="error-container">
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          </div>
        )}

        {!loading && !error && (
          <div className="dashboard-content">
            <section className="strategies-section">
              <h2>Strategies ({strategies.length})</h2>
              
              {strategies.length === 0 ? (
                <div className="empty-state">
                  <p>No strategies found in the incubator.</p>
                </div>
              ) : (
                <div className="strategies-grid">
                  {strategies.map((strategy) => (
                    <StrategyCard
                      key={strategy.id}
                      strategy={strategy}
                      isSelected={selectedStrategyId === strategy.id}
                      onSelect={handleSelectStrategy}
                    />
                  ))}
                </div>
              )}
            </section>

            {selectedStrategy && (
              <section className="strategy-details-section">
                <h2>Strategy Details</h2>
                <div className="strategy-details">
                  <div className="detail-group">
                    <h3>Basic Information</h3>
                    <div className="detail-item">
                      <label>Strategy ID:</label>
                      <span>#{selectedStrategy.id}</span>
                    </div>
                    <div className="detail-item">
                      <label>Contract Address:</label>
                      <span className="address-full">
                        {selectedStrategy.strategyAddress || <span className="placeholder-dash">—</span>}
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>Proposer:</label>
                      <span className="address-full">
                        {selectedStrategy.proposer || <span className="placeholder-dash">—</span>}
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>Status:</label>
                      <span 
                        className="status-text"
                        style={{ color: getStatusColor(selectedStrategy.status) }}
                      >
                        {getStatusString(selectedStrategy.status)}
                      </span>
                    </div>
                  </div>

                  <div className="detail-group">
                    <h3>Performance Metrics</h3>
                    <div className="detail-item">
                      <label>Performance Score:</label>
                      <span>
                        {selectedStrategy.performanceScore !== undefined ? 
                          selectedStrategy.performanceScore : 
                          <span className="placeholder-dash">—</span>
                        }
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>Tests Passed:</label>
                      <span>
                        {selectedStrategy.testsPassed !== undefined ? 
                          selectedStrategy.testsPassed : 
                          <span className="placeholder-dash">—</span>
                        }
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>Tests Failed:</label>
                      <span>
                        {selectedStrategy.testsFailed !== undefined ? 
                          selectedStrategy.testsFailed : 
                          <span className="placeholder-dash">—</span>
                        }
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>Success Rate:</label>
                      <span>
                        {selectedStrategy.testsPassed !== undefined && selectedStrategy.testsFailed !== undefined && 
                         (selectedStrategy.testsPassed + selectedStrategy.testsFailed > 0)
                          ? `${((selectedStrategy.testsPassed / (selectedStrategy.testsPassed + selectedStrategy.testsFailed)) * 100).toFixed(1)}%`
                          : <span className="placeholder-dash">N/A</span>
                        }
                      </span>
                    </div>
                  </div>

                  <div className="detail-group">
                    <h3>Timeline</h3>
                    <div className="detail-item">
                      <label>Proposed At:</label>
                      <span>
                        {selectedStrategy.proposalTimestamp ? 
                          new Date(selectedStrategy.proposalTimestamp * 1000).toLocaleString() : 
                          <span className="placeholder-dash">—</span>
                        }
                      </span>
                    </div>
                    {selectedStrategy.isVariant && (
                      <div className="detail-item">
                        <label>Base Strategy:</label>
                        <span>
                          {selectedStrategy.baseStrategyId ? 
                            `#${selectedStrategy.baseStrategyId}` : 
                            <span className="placeholder-dash">—</span>
                          }
                        </span>
                      </div>
                    )}
                  </div>

                  <StrategyActions
                    strategy={selectedStrategy}
                    onAction={handleStrategyAction}
                    isProcessing={isProcessing}
                  />

                  {actionError && (
                    <div className="action-error">
                      <strong>Action Error:</strong> {actionError}
                    </div>
                  )}
                </div>
              </section>
            )}
          </div>
        )}
      </main>

      <footer className="dashboard-footer">
        <p>Enhanced Flash Loan Arbitrage System - V33</p>
        <p>Connected to Chain ID: {chainId}</p>
      </footer>
    </div>
  );
};

export default EnhancedDashboard;