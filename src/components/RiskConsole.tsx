import React, { useState, useEffect, useCallback } from 'react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, PieChart, Pie, Cell,
  ScatterChart, Scatter, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import SentinelAlertPanel from './SentinelAlertPanel';
import { SentinelAlert } from '../hooks/useSentinelAlerts';
import './RiskConsole.css';

// Types for the Risk Console
interface VaRData {
  valueAtRisk99: number;
  expectedShortfall: number;
  lastUpdateTime: Date;
}

interface StressTestScenario {
  id: number;
  name: string;
  description: string;
  creationTime: Date;
  creator: string;
  isActive: boolean;
  assetImpacts: Record<string, number>;
}

interface StressTestResult {
  scenarioId: number;
  portfolioValueBefore: number;
  portfolioValueAfter: number;
  impactPercentage: number;
  timestamp: Date;
}

interface AssetCorrelation {
  asset1: string;
  asset1Symbol: string;
  asset2: string;
  asset2Symbol: string;
  correlation: number;
  updateTime: Date;
}

interface PortfolioAsset {
  address: string;
  symbol: string;
  name: string;
  balance: number;
  valueUSD: number;
  allocation: number;
  risk: number;
}

interface RiskConsoleProps {
  portfolioValue: number;
  onRunStressTest?: (scenarioId: number) => void;
  showSentinelAlerts?: boolean;
}

const RiskConsole: React.FC<RiskConsoleProps> = ({ 
  portfolioValue, 
  onRunStressTest,
  showSentinelAlerts = true
}) => {
  const [varData, setVarData] = useState<VaRData | null>(null);
  const [stressTestScenarios, setStressTestScenarios] = useState<StressTestScenario[]>([]);
  const [stressTestResults, setStressTestResults] = useState<StressTestResult[]>([]);
  const [correlationMatrix, setCorrelationMatrix] = useState<AssetCorrelation[]>([]);
  const [portfolioAssets, setPortfolioAssets] = useState<PortfolioAsset[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<number | null>(null);
  const [customScenario, setCustomScenario] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'var' | 'stress' | 'correlation' | 'alerts'>('var');
  const [selectedAlert, setSelectedAlert] = useState<SentinelAlert | null>(null);

  // Mock data for demonstration
  const generateMockData = useCallback(() => {
    // Mock VaR data
    const mockVaR: VaRData = {
      valueAtRisk99: 25000,
      expectedShortfall: 32000,
      lastUpdateTime: new Date(Date.now() - 3600000)
    };

    // Mock portfolio assets
    const mockAssets: PortfolioAsset[] = [
      { address: '0x1234...', symbol: 'ETH', name: 'Ethereum', balance: 10.5, valueUSD: 35000, allocation: 35, risk: 65 },
      { address: '0x2345...', symbol: 'WBTC', name: 'Wrapped Bitcoin', balance: 1.2, valueUSD: 30000, allocation: 30, risk: 70 },
      { address: '0x3456...', symbol: 'USDC', name: 'USD Coin', balance: 20000, valueUSD: 20000, allocation: 20, risk: 10 },
      { address: '0x4567...', symbol: 'DAI', name: 'Dai Stablecoin', balance: 10000, valueUSD: 10000, allocation: 10, risk: 15 },
      { address: '0x5678...', symbol: 'LINK', name: 'Chainlink', balance: 500, valueUSD: 5000, allocation: 5, risk: 55 }
    ];

    // Mock stress test scenarios
    const mockScenarios: StressTestScenario[] = [
      { 
        id: 1, 
        name: 'ETH Price Drop 40%', 
        description: 'Simulates a severe drop in ETH price by 40%',
        creationTime: new Date(Date.now() - 86400000),
        creator: '0xAdmin...',
        isActive: true,
        assetImpacts: { 'ETH': -4000, 'WBTC': -2000, 'LINK': -3000 }
      },
      { 
        id: 2, 
        name: 'Stablecoin De-pegging', 
        description: 'Simulates a stablecoin losing its peg to USD',
        creationTime: new Date(Date.now() - 172800000),
        creator: '0xAdmin...',
        isActive: true,
        assetImpacts: { 'USDC': -1500, 'DAI': -2000 }
      },
      { 
        id: 3, 
        name: 'Market Crash', 
        description: 'Simulates a broad market crash affecting all assets',
        creationTime: new Date(Date.now() - 259200000),
        creator: '0xAdmin...',
        isActive: true,
        assetImpacts: { 'ETH': -5000, 'WBTC': -4500, 'LINK': -6000, 'USDC': -500, 'DAI': -800 }
      }
    ];

    // Mock stress test results
    const mockResults: StressTestResult[] = [
      {
        scenarioId: 1,
        portfolioValueBefore: 100000,
        portfolioValueAfter: 86000,
        impactPercentage: -14,
        timestamp: new Date(Date.now() - 43200000)
      },
      {
        scenarioId: 2,
        portfolioValueBefore: 100000,
        portfolioValueAfter: 94000,
        impactPercentage: -6,
        timestamp: new Date(Date.now() - 129600000)
      }
    ];

    // Mock correlation matrix
    const mockCorrelations: AssetCorrelation[] = [
      { asset1: '0x1234...', asset1Symbol: 'ETH', asset2: '0x2345...', asset2Symbol: 'WBTC', correlation: 0.85, updateTime: new Date(Date.now() - 3600000) },
      { asset1: '0x1234...', asset1Symbol: 'ETH', asset2: '0x3456...', asset2Symbol: 'USDC', correlation: -0.2, updateTime: new Date(Date.now() - 3600000) },
      { asset1: '0x1234...', asset1Symbol: 'ETH', asset2: '0x4567...', asset2Symbol: 'DAI', correlation: -0.15, updateTime: new Date(Date.now() - 3600000) },
      { asset1: '0x1234...', asset1Symbol: 'ETH', asset2: '0x5678...', asset2Symbol: 'LINK', correlation: 0.65, updateTime: new Date(Date.now() - 3600000) },
      { asset1: '0x2345...', asset1Symbol: 'WBTC', asset2: '0x3456...', asset2Symbol: 'USDC', correlation: -0.25, updateTime: new Date(Date.now() - 3600000) },
      { asset1: '0x2345...', asset1Symbol: 'WBTC', asset2: '0x4567...', asset2Symbol: 'DAI', correlation: -0.2, updateTime: new Date(Date.now() - 3600000) },
      { asset1: '0x2345...', asset1Symbol: 'WBTC', asset2: '0x5678...', asset2Symbol: 'LINK', correlation: 0.55, updateTime: new Date(Date.now() - 3600000) },
      { asset1: '0x3456...', asset1Symbol: 'USDC', asset2: '0x4567...', asset2Symbol: 'DAI', correlation: 0.9, updateTime: new Date(Date.now() - 3600000) },
      { asset1: '0x3456...', asset1Symbol: 'USDC', asset2: '0x5678...', asset2Symbol: 'LINK', correlation: -0.1, updateTime: new Date(Date.now() - 3600000) },
      { asset1: '0x4567...', asset1Symbol: 'DAI', asset2: '0x5678...', asset2Symbol: 'LINK', correlation: -0.05, updateTime: new Date(Date.now() - 3600000) }
    ];

    return {
      varData: mockVaR,
      portfolioAssets: mockAssets,
      stressTestScenarios: mockScenarios,
      stressTestResults: mockResults,
      correlationMatrix: mockCorrelations
    };
  }, []);

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      // In a real implementation, this would fetch from your API
      // const response = await fetch('/api/risk-console/data');
      // const realData = await response.json();
      
      // For now, use mock data
      const mockData = generateMockData();
      setVarData(mockData.varData);
      setPortfolioAssets(mockData.portfolioAssets);
      setStressTestScenarios(mockData.stressTestScenarios);
      setStressTestResults(mockData.stressTestResults);
      setCorrelationMatrix(mockData.correlationMatrix);
    } catch (err) {
      console.error('Risk console data fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [generateMockData]);

  // Initial data load
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Run a stress test
  const handleRunStressTest = (scenarioId: number) => {
    if (onRunStressTest) {
      onRunStressTest(scenarioId);
    } else {
      console.log(`Running stress test for scenario ${scenarioId}`);
      // Mock implementation
      const scenario = stressTestScenarios.find(s => s.id === scenarioId);
      if (scenario) {
        let newValue = portfolioValue;
        
        // Calculate impact based on asset allocations and scenario impacts
        portfolioAssets.forEach(asset => {
          const impact = scenario.assetImpacts[asset.symbol] || 0;
          if (impact !== 0) {
            const assetImpact = (asset.valueUSD * impact) / 10000;
            newValue += assetImpact;
          }
        });
        
        const impactPct = ((newValue - portfolioValue) / portfolioValue) * 100;
        
        // Add to results
        const newResult: StressTestResult = {
          scenarioId,
          portfolioValueBefore: portfolioValue,
          portfolioValueAfter: newValue,
          impactPercentage: impactPct,
          timestamp: new Date()
        };
        
        setStressTestResults([newResult, ...stressTestResults]);
      }
    }
  };

  // Create custom scenario
  const handleCreateCustomScenario = () => {
    const newScenario: StressTestScenario = {
      id: Math.max(...stressTestScenarios.map(s => s.id), 0) + 1,
      name: 'Custom Scenario',
      description: 'User-created custom scenario',
      creationTime: new Date(),
      creator: 'User',
      isActive: true,
      assetImpacts: { ...customScenario }
    };
    
    setStressTestScenarios([...stressTestScenarios, newScenario]);
    setSelectedScenario(newScenario.id);
    setCustomScenario({});
  };

  // Update custom scenario impact
  const handleUpdateCustomImpact = (asset: string, impact: number) => {
    setCustomScenario({
      ...customScenario,
      [asset]: impact
    });
  };

  // Get color based on correlation value
  const getCorrelationColor = (value: number) => {
    if (value >= 0.7) return '#e74c3c';  // High positive - red
    if (value >= 0.3) return '#f39c12';  // Medium positive - orange
    if (value >= -0.3) return '#3498db'; // Low correlation - blue
    if (value >= -0.7) return '#2ecc71'; // Medium negative - green
    return '#27ae60';                    // High negative - dark green
  };

  // Get color based on risk value
  const getRiskColor = (risk: number) => {
    if (risk >= 70) return '#e74c3c';    // High risk - red
    if (risk >= 40) return '#f39c12';    // Medium risk - orange
    if (risk >= 20) return '#3498db';    // Low risk - blue
    return '#2ecc71';                    // Very low risk - green
  };

  if (loading) {
    return (
      <div className="risk-console loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading Risk Console...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="risk-console">
      <header className="risk-console-header">
        <h1>🛡️ Advanced Risk & Portfolio Console</h1>
        
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'var' ? 'active' : ''}`}
            onClick={() => setActiveTab('var')}
          >
            📊 Value-at-Risk
          </button>
          <button 
            className={`tab-button ${activeTab === 'stress' ? 'active' : ''}`}
            onClick={() => setActiveTab('stress')}
          >
            🔥 Stress Testing
          </button>
          <button 
            className={`tab-button ${activeTab === 'correlation' ? 'active' : ''}`}
            onClick={() => setActiveTab('correlation')}
          >
            🔄 Correlation Matrix
          </button>
          {showSentinelAlerts && (
            <button 
              className={`tab-button ${activeTab === 'alerts' ? 'active' : ''}`}
              onClick={() => setActiveTab('alerts')}
            >
              ⚠️ Sentinel Alerts
            </button>
          )}
        </div>
      </header>

      {/* Portfolio Overview */}
      <section className="portfolio-overview">
        <h2>Portfolio Overview</h2>
        <div className="portfolio-metrics">
          <div className="metric-card total-value">
            <h3>Total Value</h3>
            <div className="metric-value">${portfolioValue.toLocaleString()}</div>
          </div>
          
          <div className="metric-card var-metric">
            <h3>Value at Risk (99%)</h3>
            <div className="metric-value">${varData?.valueAtRisk99.toLocaleString()}</div>
            <div className="metric-detail">{((varData?.valueAtRisk99 || 0) / portfolioValue * 100).toFixed(2)}% of portfolio</div>
          </div>
          
          <div className="metric-card expected-shortfall">
            <h3>Expected Shortfall</h3>
            <div className="metric-value">${varData?.expectedShortfall.toLocaleString()}</div>
            <div className="metric-detail">{((varData?.expectedShortfall || 0) / portfolioValue * 100).toFixed(2)}% of portfolio</div>
          </div>
        </div>
        
        <div className="portfolio-composition">
          <h3>Portfolio Composition</h3>
          <div className="composition-chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={portfolioAssets}
                  dataKey="valueUSD"
                  nameKey="symbol"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  fill="#8884d8"
                  label={({ symbol, allocation }) => `${symbol} ${allocation}%`}
                >
                  {portfolioAssets.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getRiskColor(entry.risk)} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* Value at Risk Tab */}
      {activeTab === 'var' && (
        <section className="var-section">
          <h2>Value-at-Risk Analysis</h2>
          
          <div className="var-details">
            <div className="var-explanation">
              <h3>What is VaR?</h3>
              <p>
                Value-at-Risk (VaR) represents the maximum potential loss on your portfolio over a specific time period, 
                at a given confidence level. Our system calculates 99% VaR, meaning there is only a 1% chance that your 
                losses will exceed this amount over a 24-hour period.
              </p>
              <p>
                <strong>Expected Shortfall</strong> (also known as Conditional VaR) represents the expected loss given that 
                the loss exceeds the VaR threshold. It provides a more conservative risk estimate.
              </p>
            </div>
            
            <div className="var-history-chart">
              <h3>VaR History (7 Days)</h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={Array.from({ length: 7 }, (_, i) => ({
                  day: 6 - i,
                  var: Math.round(20000 + Math.random() * 10000),
                  es: Math.round(25000 + Math.random() * 15000)
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" label={{ value: 'Days Ago', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'USD Value', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
                  <Legend />
                  <Line type="monotone" dataKey="var" name="Value at Risk (99%)" stroke="#3498db" strokeWidth={2} />
                  <Line type="monotone" dataKey="es" name="Expected Shortfall" stroke="#e74c3c" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="asset-risk-table">
            <h3>Asset Risk Breakdown</h3>
            <table>
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Allocation</th>
                  <th>Value (USD)</th>
                  <th>Risk Score</th>
                  <th>Contribution to VaR</th>
                </tr>
              </thead>
              <tbody>
                {portfolioAssets.map((asset) => (
                  <tr key={asset.address}>
                    <td>{asset.symbol}</td>
                    <td>{asset.allocation}%</td>
                    <td>${asset.valueUSD.toLocaleString()}</td>
                    <td>
                      <div className="risk-indicator" style={{ backgroundColor: getRiskColor(asset.risk) }}>
                        {asset.risk}%
                      </div>
                    </td>
                    <td>${Math.round(varData?.valueAtRisk99 || 0 * asset.allocation / 100).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Stress Testing Tab */}
      {activeTab === 'stress' && (
        <section className="stress-test-section">
          <h2>On-Demand Stress Testing</h2>
          
          <div className="stress-test-controls">
            <div className="scenario-selector">
              <h3>Select Scenario</h3>
              <select 
                value={selectedScenario || ''} 
                onChange={(e) => setSelectedScenario(Number(e.target.value))}
                className="scenario-dropdown"
              >
                <option value="">-- Select a scenario --</option>
                {stressTestScenarios.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name}
                  </option>
                ))}
              </select>
              
              {selectedScenario && (
                <div className="scenario-details">
                  <h4>{stressTestScenarios.find(s => s.id === selectedScenario)?.name}</h4>
                  <p>{stressTestScenarios.find(s => s.id === selectedScenario)?.description}</p>
                  
                  <h4>Asset Impacts:</h4>
                  <ul className="impact-list">
                    {Object.entries(stressTestScenarios.find(s => s.id === selectedScenario)?.assetImpacts || {}).map(([asset, impact]) => (
                      <li key={asset} className={impact < 0 ? 'negative' : 'positive'}>
                        {asset}: {impact / 100}%
                      </li>
                    ))}
                  </ul>
                  
                  <button 
                    className="run-test-button"
                    onClick={() => handleRunStressTest(selectedScenario)}
                  >
                    Run Stress Test
                  </button>
                </div>
              )}
            </div>
            
            <div className="custom-scenario-builder">
              <h3>Create Custom Scenario</h3>
              <div className="custom-impacts">
                {portfolioAssets.map((asset) => (
                  <div key={asset.symbol} className="custom-impact-control">
                    <label>{asset.symbol}</label>
                    <input 
                      type="range" 
                      min="-10000" 
                      max="5000" 
                      step="100"
                      value={customScenario[asset.symbol] || 0}
                      onChange={(e) => handleUpdateCustomImpact(asset.symbol, Number(e.target.value))}
                    />
                    <span className={customScenario[asset.symbol] < 0 ? 'negative' : 'positive'}>
                      {((customScenario[asset.symbol] || 0) / 100).toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
              
              <button 
                className="create-scenario-button"
                onClick={handleCreateCustomScenario}
              >
                Create & Run Scenario
              </button>
            </div>
          </div>
          
          <div className="stress-test-results">
            <h3>Test Results</h3>
            {stressTestResults.length > 0 ? (
              <div className="results-container">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>Scenario</th>
                      <th>Before</th>
                      <th>After</th>
                      <th>Impact</th>
                      <th>Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stressTestResults.map((result, index) => (
                      <tr key={index}>
                        <td>{stressTestScenarios.find(s => s.id === result.scenarioId)?.name || 'Unknown'}</td>
                        <td>${result.portfolioValueBefore.toLocaleString()}</td>
                        <td>${result.portfolioValueAfter.toLocaleString()}</td>
                        <td className={result.impactPercentage < 0 ? 'negative' : 'positive'}>
                          {result.impactPercentage.toFixed(2)}%
                        </td>
                        <td>{result.timestamp.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                <div className="results-chart">
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={stressTestResults.slice(0, 5).map(result => ({
                      name: stressTestScenarios.find(s => s.id === result.scenarioId)?.name || 'Unknown',
                      impact: result.impactPercentage
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis label={{ value: 'Impact (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${Number(value).toFixed(2)}%`} />
                      <Bar dataKey="impact" name="Portfolio Impact">
                        {stressTestResults.slice(0, 5).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.impactPercentage < 0 ? '#e74c3c' : '#2ecc71'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : (
              <div className="no-results">
                <p>No stress tests have been run yet. Select a scenario and run a test to see results.</p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Correlation Matrix Tab */}
      {activeTab === 'correlation' && (
        <section className="correlation-section">
          <h2>Asset Correlation Matrix</h2>
          
          <div className="correlation-explanation">
            <p>
              This matrix shows how different assets in your portfolio move in relation to each other. 
              A high positive correlation (close to 1.0) means assets tend to move together, while a 
              negative correlation means they move in opposite directions. Diversifying across assets 
              with low or negative correlations can reduce overall portfolio risk.
            </p>
          </div>
          
          <div className="correlation-matrix">
            <table className="matrix-table">
              <thead>
                <tr>
                  <th></th>
                  {portfolioAssets.map((asset) => (
                    <th key={asset.symbol}>{asset.symbol}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {portfolioAssets.map((asset1) => (
                  <tr key={asset1.symbol}>
                    <th>{asset1.symbol}</th>
                    {portfolioAssets.map((asset2) => {
                      if (asset1.symbol === asset2.symbol) {
                        return <td key={asset2.symbol} className="self-correlation">1.00</td>;
                      }
                      
                      const correlation = correlationMatrix.find(
                        c => (c.asset1Symbol === asset1.symbol && c.asset2Symbol === asset2.symbol) ||
                             (c.asset1Symbol === asset2.symbol && c.asset2Symbol === asset1.symbol)
                      );
                      
                      return (
                        <td 
                          key={asset2.symbol}
                          style={{ backgroundColor: getCorrelationColor(correlation?.correlation || 0) }}
                        >
                          {correlation ? correlation.correlation.toFixed(2) : 'N/A'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="correlation-visualization">
            <h3>Correlation Network</h3>
            <div className="network-chart">
              {/* This would be a network visualization in a real implementation */}
              <div className="network-placeholder">
                <p>Network visualization would be displayed here, showing connections between assets based on correlation strength.</p>
              </div>
            </div>
          </div>
          
          <div className="correlation-insights">
            <h3>Key Insights</h3>
            <ul className="insights-list">
              <li>
                <strong>Highest Positive Correlation:</strong> {
                  (() => {
                    const highest = [...correlationMatrix].sort((a, b) => b.correlation - a.correlation)[0];
                    return highest ? `${highest.asset1Symbol} & ${highest.asset2Symbol} (${highest.correlation.toFixed(2)})` : 'N/A';
                  })()
                }
              </li>
              <li>
                <strong>Highest Negative Correlation:</strong> {
                  (() => {
                    const lowest = [...correlationMatrix].sort((a, b) => a.correlation - b.correlation)[0];
                    return lowest ? `${lowest.asset1Symbol} & ${lowest.asset2Symbol} (${lowest.correlation.toFixed(2)})` : 'N/A';
                  })()
                }
              </li>
              <li>
                <strong>Diversification Opportunity:</strong> Consider increasing allocation to assets with negative correlations to your largest holdings.
              </li>
              <li>
                <strong>Concentration Risk:</strong> {
                  (() => {
                    const highCorr = correlationMatrix.filter(c => c.correlation > 0.7);
                    return highCorr.length > 0 
                      ? `High correlation between ${highCorr.length} asset pairs may increase portfolio risk.` 
                      : 'No significant concentration risk detected.';
                  })()
                }
              </li>
            </ul>
          </div>
        </section>
      )}
      
      {/* Sentinel Alerts Tab */}
      {activeTab === 'alerts' && showSentinelAlerts && (
        <section className="alerts-section">
          <h2>Sentinel Alerts</h2>
          
          <div className="alerts-explanation">
            <p>
              Real-time security alerts from the Sentinel Agent system. These alerts monitor for oracle manipulations,
              MEV attacks, and strategy anomalies to protect your assets and optimize performance.
            </p>
          </div>
          
          <div className="alerts-container">
            <SentinelAlertPanel 
              maxAlerts={20}
              showFilters={true}
              onAlertClick={(alert) => setSelectedAlert(alert)}
            />
          </div>
          
          {selectedAlert && (
            <div className="alert-details-modal">
              <div className="alert-details-content">
                <h3>{selectedAlert.title}</h3>
                <div className="alert-details-priority" style={{ 
                  backgroundColor: 
                    selectedAlert.priority === 'critical' ? '#e74c3c' :
                    selectedAlert.priority === 'high' ? '#e67e22' :
                    selectedAlert.priority === 'medium' ? '#f39c12' :
                    selectedAlert.priority === 'low' ? '#3498db' : '#95a5a6'
                }}>
                  {selectedAlert.priority.toUpperCase()}
                </div>
                
                <p className="alert-details-message">{selectedAlert.message}</p>
                
                <div className="alert-details-section">
                  <h4>Details</h4>
                  <div className="alert-details-data">
                    {Object.entries(selectedAlert.details).map(([key, value]) => (
                      <div key={key} className="alert-details-item">
                        <span className="alert-details-key">{key}:</span>
                        <span className="alert-details-value">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="alert-details-section">
                  <h4>Recommended Actions</h4>
                  <ul className="alert-recommended-actions">
                    {selectedAlert.recommended_actions.map((action, index) => (
                      <li key={index}>{action}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="alert-details-footer">
                  <button 
                    className="alert-details-close"
                    onClick={() => setSelectedAlert(null)}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
};

export default RiskConsole;