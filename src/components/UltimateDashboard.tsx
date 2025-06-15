import React, { useState, useEffect, useCallback } from 'react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, PieChart, Pie, Cell,
  ScatterChart, Scatter, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import './UltimateDashboard.css';
import LiveAIInsightsPanel from './LiveAIInsightsPanel';
import ZKProofVerifier from './ZKProofVerifier';
import RiskConsole from './RiskConsole';

// Types for the ultimate dashboard
interface AIMetrics {
  neuralNetworkVersion: number;
  confidenceScore: number;
  predictionAccuracy: number;
  learningRate: number;
  explorationRate: number;
  qTableSize: number;
  lastModelUpdate: Date;
}

interface PerformanceMetrics {
  totalProfit: number;
  totalTrades: number;
  successRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  averageExecutionTime: number;
  gasEfficiency: number;
  riskAdjustedReturn: number;
}

interface MarketIntelligence {
  sentimentScore: number;
  whaleActivity: boolean;
  volatilityIndex: number;
  liquidityScore: number;
  mevRisk: number;
  newsImpact: number;
  technicalIndicators: {
    rsi: number;
    macd: number;
    momentum: number;
    volume: number;
  };
}

interface OpportunityData {
  id: string;
  timestamp: Date;
  profitUsd: number;
  confidenceScore: number;
  riskScore: number;
  executionComplexity: number;
  chain: string;
  dexPair: string;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  aiPrediction: {
    successProbability: number;
    profitAccuracy: number;
    riskAssessment: number;
  };
}

interface RealTimeData {
  aiMetrics: AIMetrics;
  performance: PerformanceMetrics;
  marketIntel: MarketIntelligence;
  opportunities: OpportunityData[];
  systemHealth: {
    cpuUsage: number;
    memoryUsage: number;
    networkLatency: number;
    blockchainSync: boolean;
    emergencyStatus: boolean;
  };
}

const UltimateDashboard: React.FC = () => {
  const [data, setData] = useState<RealTimeData | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [selectedChain, setSelectedChain] = useState<'all' | 'ethereum' | 'polygon' | 'bsc'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'ai-alpha' | 'zk-verifier' | 'risk-console'>('dashboard');

  // Mock data for demonstration
  const generateMockData = useCallback((): RealTimeData => {
    return {
      aiMetrics: {
        neuralNetworkVersion: 34,
        confidenceScore: 87.5,
        predictionAccuracy: 82.3,
        learningRate: 0.001,
        explorationRate: 0.15,
        qTableSize: 15420,
        lastModelUpdate: new Date(Date.now() - 3600000)
      },
      performance: {
        totalProfit: 45678.90,
        totalTrades: 1247,
        successRate: 84.2,
        sharpeRatio: 2.34,
        maxDrawdown: 8.7,
        averageExecutionTime: 12.5,
        gasEfficiency: 92.1,
        riskAdjustedReturn: 156.7
      },
      marketIntel: {
        sentimentScore: 72.5,
        whaleActivity: true,
        volatilityIndex: 45.2,
        liquidityScore: 88.9,
        mevRisk: 23.4,
        newsImpact: 15.7,
        technicalIndicators: {
          rsi: 58.3,
          macd: 12.7,
          momentum: 67.8,
          volume: 89.2
        }
      },
      opportunities: Array.from({ length: 10 }, (_, i) => ({
        id: `opp_${i + 1}`,
        timestamp: new Date(Date.now() - Math.random() * 3600000),
        profitUsd: Math.random() * 1000 + 50,
        confidenceScore: Math.random() * 40 + 60,
        riskScore: Math.random() * 50 + 10,
        executionComplexity: Math.floor(Math.random() * 10) + 1,
        chain: ['ethereum', 'polygon', 'bsc'][Math.floor(Math.random() * 3)],
        dexPair: ['ETH/USDC', 'DAI/WETH', 'WBTC/USDT'][Math.floor(Math.random() * 3)],
        status: ['pending', 'executing', 'completed', 'failed'][Math.floor(Math.random() * 4)] as any,
        aiPrediction: {
          successProbability: Math.random() * 40 + 60,
          profitAccuracy: Math.random() * 30 + 70,
          riskAssessment: Math.random() * 50 + 25
        }
      })),
      systemHealth: {
        cpuUsage: Math.random() * 30 + 20,
        memoryUsage: Math.random() * 40 + 30,
        networkLatency: Math.random() * 50 + 10,
        blockchainSync: true,
        emergencyStatus: false
      }
    };
  }, []);

  // Fetch real-time data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      // In a real implementation, this would fetch from your API
      // const response = await fetch('/api/dashboard/realtime');
      // const realData = await response.json();
      
      // For now, use mock data
      const mockData = generateMockData();
      setData(mockData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch dashboard data');
      console.error('Dashboard data fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [generateMockData]);

  // Auto-refresh effect
  useEffect(() => {
    fetchData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [fetchData, autoRefresh]);

  if (loading && !data) {
    return (
      <div className="ultimate-dashboard loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading Ultimate Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ultimate-dashboard error">
        <div className="error-message">
          <h2>⚠️ Dashboard Error</h2>
          <p>{error}</p>
          <button onClick={fetchData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#27ae60';
      case 'executing': return '#3498db';
      case 'pending': return '#f39c12';
      case 'failed': return '#e74c3c';
      default: return '#95a5a6';
    }
  };

  const getRiskColor = (risk: number) => {
    if (risk < 30) return '#27ae60';
    if (risk < 60) return '#f39c12';
    return '#e74c3c';
  };

  return (
    <div className="ultimate-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <h1>🚀 Ultimate Arbitrage Bot V35</h1>
          
          {/* Tab Navigation */}
          <div className="tab-navigation">
            <button 
              className={`tab-button ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              📊 Dashboard
            </button>
            <button 
              className={`tab-button ${activeTab === 'risk-console' ? 'active' : ''}`}
              onClick={() => setActiveTab('risk-console')}
            >
              🛡️ Risk Console
            </button>
            <button 
              className={`tab-button ${activeTab === 'ai-alpha' ? 'active' : ''}`}
              onClick={() => setActiveTab('ai-alpha')}
            >
              🧠 AI Alpha Feed
            </button>
            <button 
              className={`tab-button ${activeTab === 'zk-verifier' ? 'active' : ''}`}
              onClick={() => setActiveTab('zk-verifier')}
            >
              🔐 ZK Verifier
            </button>
          </div>
          
          {activeTab === 'dashboard' && (
            <div className="header-controls">
              <select 
                value={selectedTimeframe} 
                onChange={(e) => setSelectedTimeframe(e.target.value as any)}
                className="timeframe-selector"
              >
                <option value="1h">1 Hour</option>
                <option value="24h">24 Hours</option>
                <option value="7d">7 Days</option>
                <option value="30d">30 Days</option>
              </select>
              
              <select 
                value={selectedChain} 
                onChange={(e) => setSelectedChain(e.target.value as any)}
                className="chain-selector"
              >
                <option value="all">All Chains</option>
                <option value="ethereum">Ethereum</option>
                <option value="polygon">Polygon</option>
                <option value="bsc">BSC</option>
              </select>
              
              <button 
                className={`auto-refresh ${autoRefresh ? 'active' : ''}`}
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? '⏸️' : '▶️'} Auto Refresh
              </button>
              
              <button onClick={fetchData} className="refresh-button">
                🔄 Refresh
              </button>
            </div>
          )}
        </div>
        
        {/* System Health Indicator */}
        <div className="system-health">
          <div className={`health-indicator ${data.systemHealth.emergencyStatus ? 'emergency' : 'healthy'}`}>
            {data.systemHealth.emergencyStatus ? '🚨 EMERGENCY' : '✅ HEALTHY'}
          </div>
          <div className="health-metrics">
            <span>CPU: {data.systemHealth.cpuUsage.toFixed(1)}%</span>
            <span>RAM: {data.systemHealth.memoryUsage.toFixed(1)}%</span>
            <span>Latency: {data.systemHealth.networkLatency.toFixed(0)}ms</span>
            <span>Sync: {data.systemHealth.blockchainSync ? '✅' : '❌'}</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      {activeTab === 'risk-console' && (
        <div className="risk-console-container">
          <RiskConsole portfolioValue={data?.performance.totalProfit || 100000} />
        </div>
      )}
      
      {activeTab === 'ai-alpha' && (
        <div className="ai-alpha-feed-container">
          <LiveAIInsightsPanel />
        </div>
      )}
      
      {activeTab === 'zk-verifier' && (
        <div className="zk-verifier-container">
          <ZKProofVerifier />
        </div>
      )}
      
      {activeTab === 'dashboard' && (
        <div className="dashboard-grid">
          {/* AI Metrics Section */}
          <section className="ai-metrics-section">
            <h2>🧠 AI Intelligence</h2>
            <div className="ai-metrics-grid">
              <div className="metric-card neural-network">
                <h3>Neural Network</h3>
                <div className="metric-value">v{data.aiMetrics.neuralNetworkVersion}</div>
                <div className="metric-label">Version</div>
                <div className="metric-detail">
                  Accuracy: {data.aiMetrics.predictionAccuracy.toFixed(1)}%
                </div>
              </div>
              
              <div className="metric-card confidence">
                <h3>AI Confidence</h3>
                <div className="metric-value">{data.aiMetrics.confidenceScore.toFixed(1)}%</div>
                <div className="confidence-bar">
                  <div 
                    className="confidence-fill" 
                    style={{ width: `${data.aiMetrics.confidenceScore}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="metric-card learning">
                <h3>Learning Progress</h3>
                <div className="learning-metrics">
                  <div>Q-Table: {data.aiMetrics.qTableSize.toLocaleString()}</div>
                  <div>Exploration: {(data.aiMetrics.explorationRate * 100).toFixed(1)}%</div>
                  <div>Learning Rate: {data.aiMetrics.learningRate}</div>
                </div>
              </div>
            </div>
            
            {/* AI Performance Chart */}
            <div className="ai-performance-chart">
              <h3>AI Prediction Accuracy Over Time</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={Array.from({ length: 24 }, (_, i) => ({
                  hour: i,
                  accuracy: 75 + Math.random() * 20,
                  confidence: 70 + Math.random() * 25
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="accuracy" stroke="#3498db" strokeWidth={2} />
                  <Line type="monotone" dataKey="confidence" stroke="#e74c3c" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

        {/* Performance Metrics */}
        <section className="performance-section">
          <h2>📊 Performance Analytics</h2>
          <div className="performance-grid">
            <div className="metric-card profit">
              <h3>Total Profit</h3>
              <div className="metric-value">${data.performance.totalProfit.toLocaleString()}</div>
              <div className="metric-change positive">+12.5% (24h)</div>
            </div>
            
            <div className="metric-card success-rate">
              <h3>Success Rate</h3>
              <div className="metric-value">{data.performance.successRate.toFixed(1)}%</div>
              <div className="success-rate-visual">
                <div className="success-bar">
                  <div 
                    className="success-fill" 
                    style={{ width: `${data.performance.successRate}%` }}
                  ></div>
                </div>
              </div>
            </div>
            
            <div className="metric-card sharpe-ratio">
              <h3>Sharpe Ratio</h3>
              <div className="metric-value">{data.performance.sharpeRatio.toFixed(2)}</div>
              <div className="metric-label">Risk-Adjusted Return</div>
            </div>
            
            <div className="metric-card trades">
              <h3>Total Trades</h3>
              <div className="metric-value">{data.performance.totalTrades.toLocaleString()}</div>
              <div className="metric-detail">
                Avg Time: {data.performance.averageExecutionTime.toFixed(1)}s
              </div>
            </div>
          </div>
          
          {/* Performance Chart */}
          <div className="performance-chart">
            <h3>Profit & Loss Over Time</h3>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={Array.from({ length: 30 }, (_, i) => ({
                day: i + 1,
                profit: Math.random() * 2000 + 500,
                loss: Math.random() * 500,
                cumulative: (i + 1) * 1500 + Math.random() * 5000
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="cumulative" stackId="1" stroke="#27ae60" fill="#27ae60" fillOpacity={0.3} />
                <Area type="monotone" dataKey="profit" stackId="2" stroke="#3498db" fill="#3498db" fillOpacity={0.6} />
                <Area type="monotone" dataKey="loss" stackId="3" stroke="#e74c3c" fill="#e74c3c" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Market Intelligence */}
        <section className="market-intel-section">
          <h2>🔍 Market Intelligence</h2>
          <div className="market-intel-grid">
            <div className="intel-card sentiment">
              <h3>Market Sentiment</h3>
              <div className="sentiment-gauge">
                <div className="gauge-container">
                  <div 
                    className="gauge-fill" 
                    style={{ 
                      transform: `rotate(${(data.marketIntel.sentimentScore - 50) * 1.8}deg)` 
                    }}
                  ></div>
                  <div className="gauge-value">{data.marketIntel.sentimentScore.toFixed(1)}</div>
                </div>
              </div>
            </div>
            
            <div className="intel-card whale-activity">
              <h3>Whale Activity</h3>
              <div className={`whale-indicator ${data.marketIntel.whaleActivity ? 'active' : 'inactive'}`}>
                {data.marketIntel.whaleActivity ? '🐋 ACTIVE' : '😴 QUIET'}
              </div>
              <div className="whale-details">
                <div>Volatility: {data.marketIntel.volatilityIndex.toFixed(1)}%</div>
                <div>MEV Risk: {data.marketIntel.mevRisk.toFixed(1)}%</div>
              </div>
            </div>
            
            <div className="intel-card technical-indicators">
              <h3>Technical Indicators</h3>
              <ResponsiveContainer width="100%" height={150}>
                <RadarChart data={[
                  { indicator: 'RSI', value: data.marketIntel.technicalIndicators.rsi },
                  { indicator: 'MACD', value: data.marketIntel.technicalIndicators.macd },
                  { indicator: 'Momentum', value: data.marketIntel.technicalIndicators.momentum },
                  { indicator: 'Volume', value: data.marketIntel.technicalIndicators.volume }
                ]}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="indicator" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} />
                  <Radar name="Indicators" dataKey="value" stroke="#3498db" fill="#3498db" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* Live Opportunities */}
        <section className="opportunities-section">
          <h2>⚡ Live Opportunities</h2>
          <div className="opportunities-header">
            <div className="opportunity-stats">
              <span>Total: {data.opportunities.length}</span>
              <span>Executing: {data.opportunities.filter(o => o.status === 'executing').length}</span>
              <span>Pending: {data.opportunities.filter(o => o.status === 'pending').length}</span>
            </div>
          </div>
          
          <div className="opportunities-list">
            {data.opportunities.slice(0, 8).map((opp) => (
              <div key={opp.id} className={`opportunity-card ${opp.status}`}>
                <div className="opportunity-header">
                  <div className="opportunity-id">{opp.id}</div>
                  <div className={`opportunity-status ${opp.status}`}>
                    {opp.status.toUpperCase()}
                  </div>
                </div>
                
                <div className="opportunity-details">
                  <div className="opportunity-profit">
                    ${opp.profitUsd.toFixed(2)}
                  </div>
                  <div className="opportunity-pair">
                    {opp.dexPair} on {opp.chain}
                  </div>
                </div>
                
                <div className="opportunity-metrics">
                  <div className="metric">
                    <span className="metric-label">Confidence</span>
                    <div className="metric-bar">
                      <div 
                        className="metric-fill confidence" 
                        style={{ width: `${opp.confidenceScore}%` }}
                      ></div>
                    </div>
                    <span className="metric-value">{opp.confidenceScore.toFixed(0)}%</span>
                  </div>
                  
                  <div className="metric">
                    <span className="metric-label">Risk</span>
                    <div className="metric-bar">
                      <div 
                        className="metric-fill risk" 
                        style={{ 
                          width: `${opp.riskScore}%`,
                          backgroundColor: getRiskColor(opp.riskScore)
                        }}
                      ></div>
                    </div>
                    <span className="metric-value">{opp.riskScore.toFixed(0)}%</span>
                  </div>
                </div>
                
                <div className="ai-prediction">
                  <div className="prediction-item">
                    <span>Success: {opp.aiPrediction.successProbability.toFixed(0)}%</span>
                  </div>
                  <div className="prediction-item">
                    <span>Accuracy: {opp.aiPrediction.profitAccuracy.toFixed(0)}%</span>
                  </div>
                </div>
                
                <div className="opportunity-timestamp">
                  {opp.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Risk Management */}
        <section className="risk-section">
          <h2>🛡️ Risk Management</h2>
          <div className="risk-grid">
            <div className="risk-card portfolio-risk">
              <h3>Portfolio Risk</h3>
              <div className="risk-gauge">
                <ResponsiveContainer width="100%" height={120}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Safe', value: 60, fill: '#27ae60' },
                        { name: 'Medium', value: 30, fill: '#f39c12' },
                        { name: 'High', value: 10, fill: '#e74c3c' }
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={30}
                      outerRadius={50}
                      dataKey="value"
                    >
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="risk-card drawdown">
              <h3>Max Drawdown</h3>
              <div className="drawdown-value">{data.performance.maxDrawdown.toFixed(1)}%</div>
              <div className="drawdown-bar">
                <div 
                  className="drawdown-fill" 
                  style={{ width: `${data.performance.maxDrawdown}%` }}
                ></div>
              </div>
            </div>
            
            <div className="risk-card var">
              <h3>Value at Risk (95%)</h3>
              <div className="var-value">$2,450</div>
              <div className="var-detail">Daily VaR</div>
            </div>
          </div>
        </section>

        {/* Multi-Chain Overview */}
        <section className="multichain-section">
          <h2>🌐 Multi-Chain Overview</h2>
          <div className="chain-grid">
            {['Ethereum', 'Polygon', 'BSC'].map((chain) => (
              <div key={chain} className="chain-card">
                <div className="chain-header">
                  <h3>{chain}</h3>
                  <div className="chain-status online">●</div>
                </div>
                <div className="chain-metrics">
                  <div className="chain-metric">
                    <span>Opportunities</span>
                    <span>{Math.floor(Math.random() * 20) + 5}</span>
                  </div>
                  <div className="chain-metric">
                    <span>Success Rate</span>
                    <span>{(Math.random() * 20 + 75).toFixed(1)}%</span>
                  </div>
                  <div className="chain-metric">
                    <span>Avg Gas</span>
                    <span>{Math.floor(Math.random() * 100) + 50} gwei</span>
                  </div>
                  <div className="chain-metric">
                    <span>Profit (24h)</span>
                    <span>${(Math.random() * 5000 + 1000).toFixed(0)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
        </div>
      )}

      {/* Footer */}
      <footer className="dashboard-footer">
        <div className="footer-content">
          <div className="footer-stats">
            <span>Last Update: {new Date().toLocaleTimeString()}</span>
            <span>Uptime: 99.8%</span>
            <span>Version: 35.0 (Cognitive Kernel)</span>
          </div>
          <div className="footer-links">
            <button className="footer-button">📊 Analytics</button>
            <button className="footer-button">⚙️ Settings</button>
            <button className="footer-button">🚨 Alerts</button>
            <button className="footer-button">📖 Docs</button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default UltimateDashboard;