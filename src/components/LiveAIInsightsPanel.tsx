import React, { useState, useEffect } from "react";
import "./LiveAIInsightsPanel.css";
import { useAIStrategyData, AIInsight, PerformanceMetrics } from "../hooks/useAIStrategyData";

// This component subscribes to real-time AI insights from the Python Agent
const LiveAIInsightsPanel: React.FC = () => {
  const { 
    insights, 
    loading, 
    error: hookError, 
    fetchInsights,
    getStrategyMetrics 
  } = useAIStrategyData();
  
  const [selectedInsight, setSelectedInsight] = useState<AIInsight | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState<boolean>(false);

  // Fetch on-chain metrics when a strategy is selected
  useEffect(() => {
    if (selectedInsight) {
      const fetchMetrics = async () => {
        setLoadingMetrics(true);
        try {
          const strategyMetrics = await getStrategyMetrics(selectedInsight.strategyId);
          setMetrics(strategyMetrics);
        } catch (err) {
          console.error("Error fetching strategy metrics:", err);
        } finally {
          setLoadingMetrics(false);
        }
      };
      
      fetchMetrics();
    }
  }, [selectedInsight, getStrategyMetrics]);

  // Set the first insight as selected when insights are loaded
  useEffect(() => {
    if (insights.length > 0 && !selectedInsight) {
      setSelectedInsight(insights[0]);
    }
  }, [insights, selectedInsight]);

  // Set error from hook
  useEffect(() => {
    if (hookError) {
      setError(hookError);
    }
  }, [hookError]);

  // Set up refresh interval
  useEffect(() => {
    const interval = setInterval(fetchInsights, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [fetchInsights]);

  // Helper function to format time
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // Helper function to get color based on confidence score
  const getConfidenceColor = (score: number) => {
    if (score >= 90) return "text-green-400";
    if (score >= 75) return "text-blue-400";
    return "text-yellow-400";
  };

  // Helper function to get color based on risk score
  const getRiskColor = (score: number) => {
    if (score < 30) return "text-green-400";
    if (score < 60) return "text-yellow-400";
    return "text-red-400";
  };

  if (loading && insights.length === 0) {
    return (
      <div className="p-6 bg-gray-900/50 rounded-2xl shadow-xl text-white border border-blue-500/30 animate-pulse">
        <h2 className="text-xl font-bold mb-4 text-blue-300">🧠 AI Alpha Feed</h2>
        <div className="h-40 bg-gray-800/50 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-gray-900/50 rounded-2xl shadow-xl text-white border border-red-500/30">
        <h2 className="text-xl font-bold mb-4 text-blue-300">🧠 AI Alpha Feed</h2>
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
          <p className="text-red-400">{error}</p>
          <button 
            onClick={fetchAIInsights}
            className="mt-2 px-3 py-1 bg-red-600/30 hover:bg-red-600/50 rounded-md text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-900/50 rounded-2xl shadow-xl text-white border border-blue-500/30">
      <h2 className="text-xl font-bold mb-4 text-blue-300">🧠 AI Alpha Feed</h2>
      
      {/* Strategy List */}
      <div className="mb-4 overflow-x-auto">
        <div className="flex space-x-2">
          {insights.map((insight) => (
            <div 
              key={insight.strategyId}
              className={`p-2 rounded-lg cursor-pointer transition-all duration-200 min-w-[180px] ${
                selectedInsight?.strategyId === insight.strategyId 
                  ? 'bg-blue-900/50 border border-blue-500/50' 
                  : 'bg-gray-800/50 border border-gray-700/50 hover:bg-gray-800'
              }`}
              onClick={() => setSelectedInsight(insight)}
            >
              <div className="text-sm font-medium truncate">{insight.strategyName}</div>
              <div className="flex justify-between mt-1">
                <span className="text-xs text-gray-400">{insight.chain}</span>
                <span className={`text-xs ${getConfidenceColor(insight.confidenceScore)}`}>
                  {insight.confidenceScore}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Selected Strategy Details */}
      {selectedInsight && (
        <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/50">
          <div className="flex justify-between items-start mb-3">
            <h3 className="text-lg font-semibold text-white">{selectedInsight.strategyName}</h3>
            <span className="text-xs text-gray-400">
              {formatTime(selectedInsight.timestamp)}
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-sm text-gray-400">Predicted Profit</div>
              <div className="text-xl font-mono text-green-400">${selectedInsight.predictedProfit.toFixed(2)}</div>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-sm text-gray-400">Confidence Score</div>
              <div className={`text-xl font-mono ${getConfidenceColor(selectedInsight.confidenceScore)}`}>
                {selectedInsight.confidenceScore}%
              </div>
            </div>
          </div>
          
          {/* On-chain metrics section */}
          {metrics && (
            <div className="bg-gray-800/30 rounded-lg p-3 mb-4 border border-blue-500/20">
              <h4 className="text-sm font-semibold text-blue-300 mb-2">📊 On-Chain Performance</h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Executions:</span>
                  <span className="font-mono text-white">{metrics.totalExecutions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Success Rate:</span>
                  <span className="font-mono text-lime-400">{(metrics.successRate / 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Profit:</span>
                  <span className="font-mono text-green-400">${metrics.totalProfit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Trust Score:</span>
                  <span className="font-mono text-blue-400">{metrics.trustScore}/100</span>
                </div>
              </div>
            </div>
          )}
          
          {loadingMetrics && (
            <div className="bg-gray-800/30 rounded-lg p-3 mb-4 border border-blue-500/20 animate-pulse">
              <h4 className="text-sm font-semibold text-blue-300 mb-2">📊 Loading On-Chain Data...</h4>
              <div className="h-12 bg-gray-700/50 rounded"></div>
            </div>
          )}
          
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between">
              <span className="text-gray-400">7D Win Rate:</span> 
              <span className="font-mono text-lime-400">{selectedInsight.sevenDayWinRate}%</span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-400">Risk Score:</span> 
              <span className={`font-mono ${getRiskColor(selectedInsight.riskScore)}`}>
                {selectedInsight.riskScore}/100
              </span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-400">Complexity:</span> 
              <span className="font-mono text-purple-400">
                {selectedInsight.executionComplexity}/10
              </span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-400">Model Version:</span> 
              <span className="font-mono text-slate-400">{selectedInsight.modelVersion}</span>
            </li>
          </ul>
          
          <div className="mt-4 flex justify-end space-x-2">
            <button 
              className="px-3 py-1 bg-blue-600/30 hover:bg-blue-600/50 rounded-md text-sm"
              onClick={() => window.open(`/strategy/${selectedInsight.strategyId}`, '_blank')}
            >
              View Details
            </button>
            <button 
              className="px-3 py-1 bg-green-600/30 hover:bg-green-600/50 rounded-md text-sm"
              onClick={() => {
                // This would trigger the execution via the ProofAwareExecutorV35 contract
                if (window.confirm(`Execute strategy "${selectedInsight.strategyName}" with predicted profit of $${selectedInsight.predictedProfit.toFixed(2)}?`)) {
                  alert('Strategy execution initiated! Check the dashboard for execution status.');
                }
              }}
            >
              Execute Strategy
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveAIInsightsPanel;