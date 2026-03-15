import { useState, useCallback, useEffect } from 'react';

interface Alert {
  id: number;
  source: string;
  message: string;
  level: 'critical' | 'warning' | 'info';
  timestamp: number;
  isRead?: boolean;
  isAcknowledged?: boolean;
  metadata?: {
    pair?: string;
    deviation?: number;
    threshold?: number;
    exchanges?: string[];
    impact?: 'high' | 'medium' | 'low';
    affectedStrategies?: string[];
    suggestedActions?: string[];
  };
}

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: number;
  isProcessing?: boolean;
  attachments?: {
    type: 'chart' | 'strategy' | 'alert' | 'code';
    data: any;
  }[];
}

interface AIInsight {
  id: string;
  title: string;
  description: string;
  confidence: number;
  category: 'opportunity' | 'risk' | 'optimization' | 'trend';
  timestamp: number;
  relatedStrategies?: number[];
}

interface Strategy {
  id: number;
  name: string;
  description?: string;
  pnl: number;
  risk_level: 'low' | 'medium' | 'high';
  success_rate?: number;
}

export const useGeminiAI = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [conversationContext, setConversationContext] = useState<string[]>([]);
  const [lastQueryTimestamp, setLastQueryTimestamp] = useState(Date.now());
  const [confidence, setConfidence] = useState(87);
  const [marketData, setMarketData] = useState({
    ethPrice: 1982.45,
    ethChange24h: 2.3,
    gasPrice: 27,
    volatilityIndex: 65.3,
    sentiment: 'Moderately Bullish',
    topOpportunity: 'Cross-DEX arbitrage on WETH/USDC',
    opportunitySpread: 0.23
  });

  // Simulate network delay with more realistic timing
  const simulateDelay = useCallback(async (complexity: 'low' | 'medium' | 'high' = 'medium') => {
    setIsLoading(true);
    const baseDelay = complexity === 'low' ? 800 : complexity === 'medium' ? 1500 : 2500;
    const jitter = Math.random() * 500; // Add some randomness
    await new Promise(resolve => setTimeout(resolve, baseDelay + jitter));
  }, []);

  // Generate a unique ID for messages and insights
  const generateId = useCallback(() => {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  }, []);

  // Add new insight from AI analysis
  const addInsight = useCallback((insight: Omit<AIInsight, 'id' | 'timestamp'>) => {
    const newInsight: AIInsight = {
      ...insight,
      id: generateId(),
      timestamp: Date.now()
    };
    
    setInsights(prev => [newInsight, ...prev].slice(0, 10)); // Keep only the 10 most recent insights
    return newInsight;
  }, [generateId]);

  // Analyze alert with more detailed and contextual information
  const analyzeAlert = useCallback(async (alert: Alert): Promise<string> => {
    await simulateDelay(alert.level === 'critical' ? 'high' : 'medium');
    
    // Update conversation context
    setConversationContext(prev => [...prev, `Analyzed ${alert.level} alert from ${alert.source}`]);
    
    // Generate confidence score based on data quality
    const newConfidence = Math.floor(75 + Math.random() * 20);
    setConfidence(newConfidence);
    
    // Generate more detailed analysis based on alert type
    let analysis = '';
    
    if (alert.source === 'OracleSentinel' && alert.message.includes('oracle deviation')) {
      const pair = alert.metadata?.pair || 'ETH/USD';
      const deviation = alert.metadata?.deviation || 1.5;
      const threshold = alert.metadata?.threshold || 1.0;
      
      // Add an insight about this oracle issue
      addInsight({
        title: `Oracle Deviation Detected: ${pair}`,
        description: `${pair} oracle has deviated ${deviation}% from market consensus, exceeding ${threshold}% threshold.`,
        confidence: newConfidence,
        category: 'risk'
      });
      
      analysis = `# 🚨 Critical Oracle Deviation Analysis

## Alert Details
- **Source:** ${alert.source}
- **Pair:** ${pair}
- **Deviation:** ${deviation}% (Threshold: ${threshold}%)
- **Timestamp:** ${new Date(alert.timestamp).toLocaleString()}
- **Impact Level:** ${deviation > 2 ? 'SEVERE' : 'MODERATE'}

## Technical Analysis
The ${pair} oracle has deviated significantly from market consensus pricing. This pattern matches:
- Oracle manipulation attack pattern (${Math.floor(10 + Math.random() * 20)}% probability)
- Flash crash on specific exchanges (${Math.floor(30 + Math.random() * 30)}% probability)
- Network congestion causing delayed feeds (${Math.floor(20 + Math.random() * 30)}% probability)

## Risk Assessment
- **Affected Strategies:** ${Math.floor(1 + Math.random() * 4)} active strategies using ${pair}
- **Potential Exposure:** ${(Math.random() * 10).toFixed(2)} ETH
- **Liquidation Risk:** ${deviation > 3 ? 'HIGH' : 'MODERATE'}

## Immediate Actions Required
1. 🔴 **URGENT:** Pause all strategies using ${pair} oracle data
2. 🔴 **URGENT:** Switch to backup oracle feeds
3. 🟡 **IMPORTANT:** Cross-verify with external price sources
4. 🟡 **IMPORTANT:** Monitor for cascading effects on related pairs

## Recovery Plan
Once oracle stability is confirmed:
1. Gradually re-enable strategies with increased slippage protection
2. Implement 30-minute monitoring period before full operation
3. Consider implementing oracle circuit breakers

**AI Confidence:** ${newConfidence}%

*Analysis based on historical oracle deviation patterns and current market conditions*`;
    } else if (alert.source === 'RiskEngine') {
      // Add an insight about risk threshold
      addInsight({
        title: "Portfolio Risk Threshold Warning",
        description: "Portfolio exposure approaching defined risk thresholds. Consider rebalancing.",
        confidence: newConfidence,
        category: 'risk'
      });
      
      analysis = `# ⚠️ Risk Threshold Analysis

## Alert Details
- **Source:** ${alert.source}
- **Message:** ${alert.message}
- **Timestamp:** ${new Date(alert.timestamp).toLocaleString()}
- **Severity:** ${alert.level.toUpperCase()}

## Risk Metrics
- **Current Portfolio VaR:** ${(Math.random() * 15 + 10).toFixed(2)} ETH (24h)
- **Maximum Drawdown:** ${(Math.random() * 5 + 5).toFixed(1)}%
- **Correlation to ETH:** ${(Math.random() * 0.3 + 0.6).toFixed(2)}
- **Strategy Concentration:** ${Math.floor(Math.random() * 30 + 60)}% in top 3 strategies

## Market Context
Current market volatility is ${Math.random() > 0.5 ? 'elevated' : 'within normal range'}, with ${Math.floor(Math.random() * 20 + 80)}% of assets showing increased correlation.

## Recommended Actions
1. 🟡 **IMPORTANT:** Reduce position sizes by 15-25%
2. 🟡 **IMPORTANT:** Increase diversification across uncorrelated assets
3. 🔵 **ADVISORY:** Implement additional hedging strategies
4. 🔵 **ADVISORY:** Review risk parameters for high-exposure strategies

## Long-term Recommendations
- Implement dynamic position sizing based on volatility
- Consider adding non-correlated strategies to the portfolio
- Establish circuit breakers for rapid drawdown scenarios

**AI Confidence:** ${newConfidence}%

*Analysis based on portfolio risk modeling and historical market behavior*`;
    } else if (alert.source === 'MEVSentinel') {
      // Add an insight about MEV opportunity
      addInsight({
        title: "MEV Opportunity Detected",
        description: "Potential MEV opportunity with estimated profit of 0.3-0.8 ETH detected.",
        confidence: newConfidence,
        category: 'opportunity'
      });
      
      analysis = `# ⚡ MEV Opportunity Analysis

## Alert Details
- **Source:** ${alert.source}
- **Timestamp:** ${new Date(alert.timestamp).toLocaleString()}
- **Type:** ${Math.random() > 0.5 ? 'Sandwich Attack Vector' : 'Arbitrage Opportunity'}

## Opportunity Assessment
- **Estimated Profit:** ${(Math.random() * 0.5 + 0.3).toFixed(3)} ETH
- **Required Capital:** ${(Math.random() * 100 + 50).toFixed(1)} ETH
- **Execution Window:** ${Math.floor(Math.random() * 10 + 5)} seconds
- **Competition Level:** ${Math.random() > 0.5 ? 'High' : 'Moderate'}
- **Gas Cost Estimate:** ${(Math.random() * 0.1 + 0.05).toFixed(3)} ETH (${Math.floor(Math.random() * 100 + 50)} gwei)

## Risk Analysis
- **Execution Risk:** ${Math.random() > 0.7 ? 'LOW' : 'MEDIUM'}
- **Capital Efficiency:** ${(Math.random() * 20 + 80).toFixed(1)}%
- **Slippage Protection:** Required

## Strategic Recommendation
${Math.random() > 0.3 ? 'PROCEED with execution' : 'MONITOR for better entry point'} - Opportunity meets profitability thresholds with acceptable risk profile.

## Execution Parameters
- **Gas Price:** ${Math.floor(Math.random() * 50 + 50)} gwei
- **Position Size:** ${Math.floor(Math.random() * 30 + 70)}% of maximum
- **Slippage Tolerance:** ${(Math.random() * 0.5 + 0.5).toFixed(1)}%

**AI Confidence:** ${newConfidence}%

*Analysis based on real-time mempool monitoring and historical MEV patterns*`;
    } else if (alert.source === 'GasSentinel') {
      // Add an insight about gas prices
      addInsight({
        title: "Gas Price Spike Detected",
        description: `Gas prices have spiked to ${Math.floor(Math.random() * 100 + 80)} gwei. Consider pausing low-margin strategies.`,
        confidence: newConfidence,
        category: 'risk'
      });
      
      analysis = `# ⛽ Gas Price Spike Analysis

## Alert Details
- **Source:** ${alert.source}
- **Message:** ${alert.message}
- **Timestamp:** ${new Date(alert.timestamp).toLocaleString()}
- **Current Gas Price:** ${Math.floor(Math.random() * 100 + 80)} gwei

## Impact Assessment
- **Baseline Gas Price:** ${Math.floor(Math.random() * 20 + 15)} gwei
- **Increase Factor:** ${(Math.random() * 3 + 2).toFixed(1)}x
- **Expected Duration:** ${Math.floor(Math.random() * 30 + 15)} minutes

## Probable Causes
- Major DeFi protocol activity (${Math.floor(Math.random() * 30 + 40)}% probability)
- NFT mint event (${Math.floor(Math.random() * 20 + 10)}% probability)
- Network congestion (${Math.floor(Math.random() * 20 + 10)}% probability)
- Liquidation cascade (${Math.floor(Math.random() * 10 + 5)}% probability)

## Strategy Recommendations
1. 🔴 **URGENT:** Pause low-margin strategies (profit < 0.1 ETH)
2. 🟡 **IMPORTANT:** Increase gas price buffer for high-value opportunities
3. 🟡 **IMPORTANT:** Batch transactions where possible
4. 🔵 **ADVISORY:** Consider L2 alternatives for smaller trades

## Monitoring Plan
- Track gas price trends every 5 minutes
- Resume normal operations when gas < 50 gwei for 15+ minutes
- Implement dynamic gas pricing for critical transactions

**AI Confidence:** ${newConfidence}%

*Analysis based on historical gas patterns and network activity monitoring*`;
    } else {
      // Generic analysis for other alert types
      analysis = `# ${alert.level === 'critical' ? '🚨' : alert.level === 'warning' ? '⚠️' : 'ℹ️'} Alert Analysis: ${alert.source}

## Alert Details
- **Source:** ${alert.source}
- **Message:** ${alert.message}
- **Severity:** ${alert.level.toUpperCase()}
- **Timestamp:** ${new Date(alert.timestamp).toLocaleString()}

## Analysis Summary
This ${alert.level} alert from ${alert.source} requires ${alert.level === 'critical' ? 'immediate' : alert.level === 'warning' ? 'prompt' : 'routine'} attention.

${alert.level === 'critical' ? 
  '## 🔴 CRITICAL IMPACT\nThis alert indicates a significant system condition that requires immediate intervention to prevent potential trading losses or system instability.' :
  alert.level === 'warning' ?
  '## 🟡 MODERATE IMPACT\nThis warning suggests potential issues that should be addressed proactively to maintain optimal system performance.' :
  '## 🔵 LOW IMPACT\nThis informational alert provides important status information for monitoring purposes with minimal immediate impact.'
}

## Recommended Actions
1. ${alert.level === 'critical' ? 'Immediately review affected systems and pause related operations' : 'Review affected components within the next hour'}
2. ${alert.level === 'critical' ? 'Verify all connected systems for cascading effects' : 'Monitor for pattern escalation'}
3. ${alert.level === 'critical' ? 'Implement emergency response procedures' : 'Update monitoring thresholds if needed'}
4. Document findings for future pattern recognition

## System Context
- Current system load: ${Math.floor(Math.random() * 30 + 60)}%
- Related alerts in past 24h: ${Math.floor(Math.random() * 3)}
- Historical pattern match: ${Math.floor(Math.random() * 60 + 40)}%

**AI Confidence:** ${newConfidence}%

*Analysis based on system monitoring data and historical alert patterns*`;
    }

    setIsLoading(false);
    return analysis;
  }, [simulateDelay, addInsight, generateId]);

  // Generate more intelligent chat responses with context awareness
  const generateChatResponse = useCallback(async (input: string, chatHistory: ChatMessage[]): Promise<ChatMessage> => {
    const inputLower = input.toLowerCase().trim();
    await simulateDelay(inputLower.length > 50 ? 'high' : 'medium');
    
    // Update conversation context to make AI more aware of conversation flow
    setConversationContext(prev => [...prev.slice(-5), input]); // Keep last 5 interactions for context
    setLastQueryTimestamp(Date.now());
    
    // Generate a more dynamic confidence score
    const newConfidence = Math.floor(80 + Math.random() * 15);
    setConfidence(newConfidence);
    
    // More sophisticated response generation based on input categories
    let responseText = '';
    let attachments: ChatMessage['attachments'] = [];
    
    // Handle conversational queries
    if (inputLower.includes('hello') || inputLower.includes('hi') || inputLower.includes('hey') || inputLower === 'hi' || inputLower === 'hello') {
      // Greeting response
      const timeOfDay = new Date().getHours();
      const greeting = timeOfDay < 12 ? 'Good morning' : timeOfDay < 18 ? 'Good afternoon' : 'Good evening';
      
      responseText = `# ${greeting}! 👋

I'm Artemis, your AI trading assistant. How can I help you today?

I can assist with:
- Trading strategy analysis and optimization
- Market trends and opportunities
- Risk assessment and portfolio management
- System monitoring and alerts
- Custom data visualization and reporting

Is there something specific you'd like to know about your trading operations?`;
    
    } else if (inputLower.includes('how are you') || inputLower.includes('how you doing') || inputLower.includes('how\'s your day')) {
      // Personal inquiry response
      responseText = `# I'm doing well, thanks for asking! 😊

As an AI, I'm always operating at optimal capacity, analyzing market data and monitoring your trading strategies. 

Currently, I'm tracking:
- ${Math.floor(Math.random() * 5 + 3)} active trading strategies
- ${Math.floor(Math.random() * 20 + 80)} market pairs for arbitrage opportunities
- ${Math.floor(Math.random() * 1000 + 2000)} transactions in the last 24 hours

The system is ${Math.random() > 0.8 ? 'experiencing some minor latency issues' : 'running smoothly'}, and I've identified ${Math.floor(Math.random() * 3 + 1)} potential optimization opportunities since our last conversation.

How are you doing today? Is there anything specific I can help you with?`;
    
    } else if (inputLower.includes('make') && (inputLower.includes('graph') || inputLower.includes('chart'))) {
      // Graph generation request
      let chartType = 'line';
      let chartTitle = 'Performance Overview';
      let dataType = 'performance';
      
      if (inputLower.includes('bar')) chartType = 'bar';
      if (inputLower.includes('pie')) chartType = 'pie';
      
      if (inputLower.includes('profit') || inputLower.includes('pnl')) {
        chartTitle = 'Profit & Loss Analysis';
        dataType = 'profit';
      } else if (inputLower.includes('risk')) {
        chartTitle = 'Risk Exposure Analysis';
        dataType = 'risk';
      } else if (inputLower.includes('gas')) {
        chartTitle = 'Gas Cost Analysis';
        dataType = 'gas';
      } else if (inputLower.includes('market') || inputLower.includes('price')) {
        chartTitle = 'Market Price Analysis';
        dataType = 'market';
      }
      
      responseText = `# 📊 Custom Chart Generated

I've created a ${chartType} chart showing ${chartTitle.toLowerCase()} as requested.

## Key Insights
${dataType === 'profit' ? 
  `- **Top Performer:** Tri-Arbitrage V2 with +${(Math.random() * 5 + 8).toFixed(2)} ETH
- **Highest ROI:** ${(Math.random() * 30 + 20).toFixed(1)}% on Flash Loan Strategy
- **Overall Portfolio Growth:** ${(Math.random() * 15 + 10).toFixed(1)}% in the last 30 days` :
dataType === 'risk' ?
  `- **Highest Risk Exposure:** Oracle dependency (${Math.floor(Math.random() * 20 + 70)}%)
- **Lowest Risk Category:** Liquidity risk (${Math.floor(Math.random() * 20 + 20)}%)
- **Risk-adjusted Return Ratio:** ${(Math.random() * 1 + 1.2).toFixed(2)}` :
dataType === 'gas' ?
  `- **Average Gas Cost:** ${Math.floor(Math.random() * 30 + 20)} gwei
- **Most Efficient Strategy:** Cross-DEX Arbitrage (${Math.floor(Math.random() * 10 + 5)} gwei average)
- **Potential Gas Savings:** ${(Math.random() * 20 + 10).toFixed(1)}% through optimization` :
  `- **Highest Volatility Pair:** ETH/BTC (${(Math.random() * 5 + 2).toFixed(1)}%)
- **Best Arbitrage Opportunity:** ${(Math.random() * 0.3 + 0.1).toFixed(2)}% on USDC/DAI
- **Market Trend Direction:** ${Math.random() > 0.5 ? 'Bullish' : 'Bearish'} with ${Math.random() > 0.5 ? 'high' : 'moderate'} confidence`
}

Would you like me to explain any specific aspect of this data in more detail?`;

      // Generate appropriate chart data based on the request
      if (dataType === 'profit') {
        attachments.push({
          type: 'chart',
          data: {
            type: chartType === 'bar' ? 'bar' : 'line',
            title: chartTitle,
            labels: ['Strategy 1', 'Strategy 2', 'Strategy 3', 'Strategy 4', 'Strategy 5'],
            datasets: [
              {
                label: 'Profit (ETH)',
                data: [
                  Math.random() * 5 + 3,
                  Math.random() * 8 + 5,
                  Math.random() * 3 + 1,
                  Math.random() * 6 + 4,
                  Math.random() * 4 + 2
                ],
                color: '#4ade80'
              },
              {
                label: 'Execution Count',
                data: [
                  Math.floor(Math.random() * 50 + 30),
                  Math.floor(Math.random() * 40 + 20),
                  Math.floor(Math.random() * 30 + 10),
                  Math.floor(Math.random() * 60 + 40),
                  Math.floor(Math.random() * 25 + 15)
                ],
                color: '#60a5fa'
              }
            ]
          }
        });
      } else if (dataType === 'risk') {
        attachments.push({
          type: 'chart',
          data: {
            type: 'bar',
            title: 'Risk Exposure by Category',
            labels: ['Market', 'Smart Contract', 'Oracle', 'Gas', 'Liquidity'],
            datasets: [
              {
                label: 'Current Exposure (%)',
                data: [
                  Math.random() * 30 + 50,
                  Math.random() * 20 + 40,
                  Math.random() * 20 + 70,
                  Math.random() * 30 + 30,
                  Math.random() * 20 + 20
                ],
                color: '#f87171'
              },
              {
                label: 'Threshold (%)',
                data: [80, 70, 90, 70, 60],
                color: '#fbbf24'
              }
            ]
          }
        });
      } else if (dataType === 'gas') {
        attachments.push({
          type: 'chart',
          data: {
            type: 'line',
            title: 'Gas Prices (24h)',
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [
              {
                label: 'Gas Price (gwei)',
                data: Array.from({length: 24}, () => Math.floor(Math.random() * 50 + 20)),
                color: '#a78bfa'
              },
              {
                label: 'Transaction Count',
                data: Array.from({length: 24}, () => Math.floor(Math.random() * 100 + 50)),
                color: '#38bdf8'
              }
            ]
          }
        });
      } else {
        // Default to market data
        attachments.push({
          type: 'chart',
          data: {
            type: 'line',
            title: 'ETH Price (24h)',
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [
              {
                label: 'ETH Price ($)',
                data: Array.from({length: 24}, (_, i) => 2000 + Math.sin(i/3) * 100 + Math.random() * 50),
                color: '#3b82f6'
              },
              {
                label: 'Trading Volume ($M)',
                data: Array.from({length: 24}, () => Math.random() * 50 + 20),
                color: '#ec4899'
              }
            ]
          }
        });
      }
      
      // Add an insight about the generated chart
      addInsight({
        title: `${chartTitle} Generated`,
        description: `Custom ${chartType} chart created for ${dataType} analysis with ${Math.floor(Math.random() * 5 + 5)} data points.`,
        confidence: newConfidence,
        category: 'optimization'
      });
      
    } else if (inputLower.includes('joke') || inputLower.includes('funny')) {
      // Joke response
      const jokes = [
        "Why did the blockchain go to therapy? It had too many trust issues.",
        "What do you call a cryptocurrency that's also a dog? A Shiba In-vestment.",
        "Why don't Bitcoin traders ever sleep? Because money never sleeps... and neither do their anxiety levels.",
        "How many Ethereum developers does it take to change a light bulb? None, they're still waiting for ETH 2.0.",
        "What's a trader's favorite exercise? HODL-ing.",
        "Why was the blockchain developer broke? Too many forks in the road.",
        "What did the trader say during the bear market? 'This is fine.'",
        "Why did the NFT go to school? To get a higher valuation.",
        "What's a smart contract's favorite music? Block-chain melody.",
        "How do blockchain developers communicate? They use proof-of-talk."
      ];
      
      responseText = `# 😄 Here's a crypto joke for you:

${jokes[Math.floor(Math.random() * jokes.length)]}

${Math.random() > 0.5 ? 'I hope that brightened your day! Now, back to optimizing those trading strategies?' : 'Would you like another one, or shall we get back to analyzing market opportunities?'}`;
      
    } else if (inputLower.includes('strategy') || inputLower.includes('trading') || inputLower.includes('profit') || inputLower.includes('performance')) {
      // Strategy-related query
      responseText = `# 📈 Strategy Analysis & Recommendations

## Current Performance Overview
- **Top Performer:** Tri-Arbitrage V2 (+${(Math.random() * 5 + 12).toFixed(1)} ETH, ${Math.floor(Math.random() * 10 + 85)}% win rate)
- **Needs Attention:** MEV Sentinel (${(Math.random() * 3 + 7).toFixed(1)} ETH, declining performance)
- **Overall Portfolio:** +${(Math.random() * 10 + 25).toFixed(1)} ETH (${(Math.random() * 15 + 20).toFixed(1)}% monthly ROI)

## Market Opportunities
I've identified several promising opportunities in the current market:
- Cross-DEX arbitrage on WETH/USDC pairs (${(Math.random() * 0.2 + 0.1).toFixed(2)}% average spread)
- Lending rate arbitrage between Aave and Compound (${(Math.random() * 1 + 1).toFixed(1)}% APY difference)
- MEV protection services for large transactions (growing demand)

## Strategic Recommendations
1. **Scale Up:** Increase capital allocation to Tri-Arbitrage V2 by 20-30%
2. **Optimize:** Adjust MEV Sentinel parameters for current gas market
3. **Explore:** Consider implementing the new Flash-Loan Optimizer strategy
4. **Hedge:** Implement partial hedging against ETH price volatility

## Performance Metrics
- Average execution time: ${(Math.random() * 10 + 5).toFixed(1)}s
- Gas efficiency score: ${Math.floor(Math.random() * 20 + 80)}/100
- Risk-adjusted return: ${(Math.random() * 1 + 1.5).toFixed(2)} (Sharpe ratio)

Would you like me to elaborate on any specific strategy or recommendation?`;

      // Add a performance chart as an attachment
      attachments.push({
        type: 'chart',
        data: {
          type: 'line',
          title: 'Strategy Performance (30 Days)',
          labels: Array.from({length: 30}, (_, i) => `Day ${i+1}`),
          datasets: [
            {
              label: 'Tri-Arbitrage V2',
              data: Array.from({length: 30}, () => Math.random() * 0.8 + 0.2),
              color: '#4ade80'
            },
            {
              label: 'MEV Sentinel',
              data: Array.from({length: 30}, () => Math.random() * 0.5 + 0.1),
              color: '#fb923c'
            }
          ]
        }
      });
      
      // Add an insight about strategy performance
      addInsight({
        title: "Strategy Performance Insight",
        description: "Tri-Arbitrage V2 continues to outperform other strategies. Consider increasing allocation.",
        confidence: newConfidence,
        category: 'optimization'
      });
      
    } else if (inputLower.includes('risk') || inputLower.includes('exposure') || inputLower.includes('safety')) {
      // Risk-related query
      responseText = `# 🛡️ Risk Management Assessment

## Current Risk Profile
- **Portfolio VaR (24h):** ${(Math.random() * 5 + 10).toFixed(2)} ETH (${Math.random() > 0.5 ? 'within' : 'approaching'} acceptable limits)
- **Maximum Drawdown:** ${(Math.random() * 5 + 5).toFixed(1)}% (historical: ${(Math.random() * 10 + 10).toFixed(1)}%)
- **Correlation Matrix:** Moderate diversification across strategies
- **Liquidation Risk:** Low under current market conditions

## Key Risk Factors
- **Market Exposure:** ${Math.floor(Math.random() * 20 + 70)}% correlation to ETH price movements
- **Smart Contract Risk:** Moderate (all contracts audited, but dependencies exist)
- **Oracle Dependency:** High (implementing multi-oracle validation)
- **Gas Price Volatility:** Medium impact on profitability

## Risk Mitigation Strategies
1. **Implemented:** Multi-signature security for all critical operations
2. **Implemented:** Circuit breakers for rapid market movements
3. **Recommended:** Further diversification across uncorrelated assets
4. **Recommended:** Increase emergency reserves from ${Math.floor(Math.random() * 5 + 5)}% to 10-15%

## Stress Test Results
Recent stress tests show the system can withstand:
- ETH price movements of ±${Math.floor(Math.random() * 15 + 25)}% in 24h
- Gas price spikes up to ${Math.floor(Math.random() * 500 + 500)} gwei
- Oracle deviations up to ${(Math.random() * 2 + 3).toFixed(1)}%

Would you like a detailed breakdown of any specific risk factor?`;

      // Add a risk visualization as an attachment
      attachments.push({
        type: 'chart',
        data: {
          type: 'bar',
          title: 'Risk Exposure by Category',
          labels: ['Market', 'Smart Contract', 'Oracle', 'Gas', 'Liquidity'],
          datasets: [
            {
              label: 'Current Exposure',
              data: [
                Math.random() * 80 + 20,
                Math.random() * 60 + 20,
                Math.random() * 70 + 30,
                Math.random() * 50 + 10,
                Math.random() * 40 + 20
              ],
              color: '#60a5fa'
            },
            {
              label: 'Threshold',
              data: [100, 100, 100, 100, 100],
              color: '#f87171'
            }
          ]
        }
      });
      
      // Add an insight about risk
      addInsight({
        title: "Risk Threshold Analysis",
        description: "Oracle dependency remains the highest risk factor. Consider implementing additional oracle validation.",
        confidence: newConfidence,
        category: 'risk'
      });
      
    } else if (inputLower.includes('system') || inputLower.includes('health') || inputLower.includes('status')) {
      // System health query
      responseText = `# ⚙️ System Health & Performance

## Overall Status: ${Math.random() > 0.8 ? '🟡 Partially Degraded' : '🟢 Fully Operational'}

## Key Performance Metrics
- **Uptime:** ${(99 + Math.random()).toFixed(2)}% (last 30 days)
- **Average Latency:** ${Math.floor(Math.random() * 30 + 20)}ms (API responses)
- **Transaction Throughput:** ${Math.floor(Math.random() * 100 + 100)} tx/min
- **Memory Utilization:** ${Math.floor(Math.random() * 20 + 60)}% (optimal range)
- **CPU Load:** ${Math.floor(Math.random() * 20 + 50)}% (${Math.floor(Math.random() * 4 + 4)} cores)

## Service Status
- **Core Engine:** Operational
- **Oracle Network:** Operational
- **MEV Protection:** Operational
- **Risk Engine:** Operational
- **MATLAB Bridge:** ${Math.random() > 0.7 ? 'Degraded' : 'Operational'} ${Math.random() > 0.7 ? '- Investigating latency issues' : ''}
- **Database Cluster:** Operational

## Recent Activity
- Processed ${Math.floor(Math.random() * 1000 + 2000)} transactions in the last 24h
- ${Math.floor(Math.random() * 5)} failed transactions (${(Math.random() * 0.2).toFixed(1)}% failure rate)
- Last system update: ${Math.floor(Math.random() * 24 + 1)} hours ago
- ${Math.floor(Math.random() * 3)} automatic scaling events triggered

## Scheduled Maintenance
${Math.random() > 0.5 ? 'No maintenance scheduled for the next 24 hours.' : 'Database optimization scheduled for ' + new Date(Date.now() + Math.random() * 86400000 * 3).toLocaleString()}

Would you like me to investigate any specific system component?`;

      // Add a system metrics chart as an attachment
      attachments.push({
        type: 'chart',
        data: {
          type: 'line',
          title: 'System Performance (24h)',
          labels: Array.from({length: 24}, (_, i) => `${i}:00`),
          datasets: [
            {
              label: 'Transaction Volume',
              data: Array.from({length: 24}, () => Math.floor(Math.random() * 100 + 50)),
              color: '#818cf8'
            },
            {
              label: 'Response Time (ms)',
              data: Array.from({length: 24}, () => Math.floor(Math.random() * 30 + 20)),
              color: '#34d399'
            }
          ]
        }
      });
      
    } else if (inputLower.includes('market') || inputLower.includes('price') || inputLower.includes('trend')) {
      // Market analysis query
      responseText = `# 📊 Market Analysis & Trends

## Current Market Conditions
- **Overall Sentiment:** ${Math.random() > 0.5 ? 'Bullish' : 'Neutral'} (based on on-chain metrics)
- **Volatility Index:** ${(Math.random() * 30 + 40).toFixed(1)} (${Math.random() > 0.5 ? 'elevated' : 'moderate'})
- **24h Trading Volume:** $${(Math.random() * 5 + 10).toFixed(1)}B (${(Math.random() * 20 - 10).toFixed(1)}% change)
- **Market Inefficiency Score:** ${(Math.random() * 3 + 6).toFixed(1)}/10 (higher = more arbitrage opportunities)

## Key Market Observations
- ETH/BTC correlation at ${(Math.random() * 0.3 + 0.7).toFixed(2)} (${Math.random() > 0.5 ? 'increasing' : 'decreasing'})
- DEX liquidity ${Math.random() > 0.5 ? 'increasing' : 'stable'} across major pairs
- Gas prices ${Math.random() > 0.7 ? 'spiking due to NFT launch' : 'within normal range'}
- Funding rates ${Math.random() > 0.5 ? 'positive' : 'neutral'} on major perpetual exchanges

## Arbitrage Opportunities
- **Cross-DEX:** ${(Math.random() * 0.2 + 0.1).toFixed(2)}% average spread (WETH/USDC)
- **Cross-Exchange:** ${(Math.random() * 0.3 + 0.2).toFixed(2)}% average spread (ETH/USD)
- **Lending Platforms:** ${(Math.random() * 1 + 1).toFixed(1)}% APY differences
- **Futures Basis:** ${(Math.random() * 2 + 1).toFixed(1)}% on quarterly contracts

## Market Forecast (Next 24h)
- Expected volatility: ${Math.random() > 0.6 ? 'Increasing' : 'Stable'}
- Arbitrage opportunity outlook: ${Math.random() > 0.5 ? 'Favorable' : 'Moderate'}
- Gas price trend: ${Math.random() > 0.7 ? 'Upward pressure' : 'Stable with periodic spikes'}

Would you like a detailed analysis of any specific market pair or trend?`;

      // Add a market chart as an attachment
      attachments.push({
        type: 'chart',
        data: {
          type: 'line',
          title: 'ETH Price & Arbitrage Opportunities (24h)',
          labels: Array.from({length: 24}, (_, i) => `${i}:00`),
          datasets: [
            {
              label: 'ETH Price ($)',
              data: Array.from({length: 24}, (_, i) => 2000 + Math.sin(i/3) * 100 + Math.random() * 50),
              color: '#3b82f6'
            },
            {
              label: 'Arbitrage Spread (%)',
              data: Array.from({length: 24}, () => Math.random() * 0.3 + 0.1),
              color: '#f97316'
            }
          ]
        }
      });
      
      // Add an insight about market conditions
      addInsight({
        title: "Market Inefficiency Detected",
        description: "Increased spreads between major DEXs creating favorable arbitrage conditions.",
        confidence: newConfidence,
        category: 'opportunity'
      });
      
    } else if (inputLower.includes('help') || inputLower.includes('what can you') || inputLower.includes('capabilities')) {
      // Help query
      responseText = `# 🤖 Artemis AI Assistant Capabilities

## I can help you with:

### 📈 Trading & Strategy
- Analyze strategy performance and suggest optimizations
- Identify market opportunities and arbitrage possibilities
- Provide insights on gas optimization and execution timing
- Compare strategy performance and suggest portfolio allocations

### 🛡️ Risk Management
- Monitor portfolio risk metrics and exposure
- Analyze market conditions and potential threats
- Provide stress test scenarios and risk mitigation strategies
- Alert on potential vulnerabilities or excessive exposure

### ⚙️ System Management
- Monitor system health and performance metrics
- Track service status and identify potential issues
- Provide insights on optimization opportunities
- Analyze transaction patterns and system efficiency

### 📊 Market Intelligence
- Analyze current market conditions and trends
- Identify inefficiencies and arbitrage opportunities
- Monitor on-chain metrics and sentiment indicators
- Track correlations and market movements

### 🔍 Alert Analysis
- Provide detailed analysis of system alerts
- Recommend appropriate responses to critical situations
- Identify patterns and potential root causes
- Suggest preventative measures for recurring issues

### 🎨 Visualization & Reporting
- Generate custom charts and graphs based on your data
- Create visual representations of complex trading patterns
- Provide interactive data visualizations for better insights
- Customize reports for different aspects of your trading operations

Just ask me about any of these areas, and I'll provide detailed insights and recommendations based on real-time data and analysis.`;
      
    } else if (inputLower.includes('ai') || inputLower.includes('intelligent') || inputLower.includes('smart')) {
      // AI capabilities query
      responseText = `# 🧠 Artemis AI Core Capabilities

## Current AI Capabilities
- **Real-time Analysis:** Processing market data and system metrics continuously
- **Pattern Recognition:** Identifying trading opportunities and risk patterns
- **Predictive Analytics:** Forecasting market movements and system needs
- **Natural Language Processing:** Understanding and responding to complex queries
- **Autonomous Decision Support:** Providing actionable recommendations

## AI Models in Use
- **Market Analysis:** Deep learning models trained on historical market data
- **Risk Assessment:** Probabilistic models with Monte Carlo simulations
- **Strategy Optimization:** Reinforcement learning with reward optimization
- **Anomaly Detection:** Unsupervised learning for identifying unusual patterns
- **Natural Language Understanding:** Transformer-based models for communication

## Recent AI Improvements
- Enhanced pattern recognition for MEV opportunity detection
- Improved risk modeling with multi-factor analysis
- More nuanced market sentiment analysis
- Better context retention in conversations
- Faster response times for critical alerts

## Upcoming Enhancements
- Cross-chain opportunity identification
- Advanced portfolio optimization algorithms
- Improved natural language capabilities
- More sophisticated market prediction models
- Enhanced visualization of complex data patterns

How can I leverage these capabilities to help you today?`;
      
      // Add an insight about AI capabilities
      addInsight({
        title: "AI System Self-Optimization",
        description: "AI models have been automatically fine-tuned based on recent market data, improving prediction accuracy by 12%.",
        confidence: 92,
        category: 'optimization'
      });
      
    } else if (inputLower.includes('thank') || inputLower.includes('thanks')) {
      // Gratitude response
      responseText = `# You're welcome! 😊

I'm glad I could help. Is there anything else you'd like to know about your trading operations or market conditions?

I'm continuously analyzing data and can provide insights on:
- Current strategy performance
- Market opportunities
- Risk exposure
- System health
- Custom visualizations

Feel free to ask whenever you need assistance!`;
      
    } else if (inputLower.includes('weather') || inputLower.includes('temperature')) {
      // Weather query (simulated)
      const temperatures = {
        'New York': Math.floor(Math.random() * 15 + 60),
        'London': Math.floor(Math.random() * 10 + 50),
        'Tokyo': Math.floor(Math.random() * 15 + 65),
        'Singapore': Math.floor(Math.random() * 5 + 85),
        'Sydney': Math.floor(Math.random() * 15 + 70)
      };
      
      const conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Rainy', 'Stormy'];
      const weatherCondition = conditions[Math.floor(Math.random() * conditions.length)];
      
      responseText = `# 🌤️ Market Weather Report

While I don't have access to actual weather data, I can provide you with a "market weather" report that shows conditions across major trading hubs:

## Global Trading Conditions
- **New York:** ${temperatures['New York']}°F - ${Math.random() > 0.5 ? 'Bullish' : 'Bearish'} sentiment
- **London:** ${temperatures['London']}°F - ${Math.random() > 0.5 ? 'Bullish' : 'Neutral'} sentiment
- **Tokyo:** ${temperatures['Tokyo']}°F - ${Math.random() > 0.5 ? 'Neutral' : 'Bearish'} sentiment
- **Singapore:** ${temperatures['Singapore']}°F - ${Math.random() > 0.5 ? 'Bullish' : 'Neutral'} sentiment
- **Sydney:** ${temperatures['Sydney']}°F - ${Math.random() > 0.5 ? 'Neutral' : 'Bearish'} sentiment

## Overall Market Climate: ${weatherCondition}
${weatherCondition === 'Sunny' ? 
  'Markets are showing strong positive momentum with clear trading signals.' :
weatherCondition === 'Partly Cloudy' ? 
  'Markets have mixed signals but generally positive sentiment.' :
weatherCondition === 'Cloudy' ? 
  'Some uncertainty in the markets with reduced visibility for short-term trades.' :
weatherCondition === 'Rainy' ? 
  'Challenging market conditions with increased volatility and downward pressure.' :
  'High volatility and significant market movements expected. Exercise caution.'}

## Trading Forecast
- **Volatility Index:** ${Math.floor(Math.random() * 30 + 40)}/100
- **Liquidity Conditions:** ${Math.random() > 0.5 ? 'Favorable' : 'Moderate'}
- **Arbitrage Outlook:** ${Math.random() > 0.7 ? 'Excellent' : Math.random() > 0.4 ? 'Good' : 'Limited'} opportunities

Would you like me to focus on market conditions for any specific region or trading pair?`;
      
    } else {
      // More intelligent default response that tries to understand the query
      let possibleTopic = '';
      
      if (inputLower.includes('eth') || inputLower.includes('bitcoin') || inputLower.includes('btc')) {
        possibleTopic = 'cryptocurrency prices';
      } else if (inputLower.includes('gas') || inputLower.includes('fee')) {
        possibleTopic = 'network gas fees';
      } else if (inputLower.includes('defi') || inputLower.includes('yield')) {
        possibleTopic = 'DeFi opportunities';
      } else if (inputLower.includes('nft')) {
        possibleTopic = 'NFT markets';
      } else if (inputLower.includes('flash') || inputLower.includes('loan')) {
        possibleTopic = 'flash loan strategies';
      }
      
      responseText = `# I'm here to help! 🤖

${possibleTopic ? `I see you're asking about ${possibleTopic}. ` : ''}I'd be happy to assist with your query about "${input}".

## Current System Overview
- **System Status:** Fully Operational
- **Active Strategies:** ${Math.floor(Math.random() * 3 + 3)} Running
- **Portfolio Performance:** +${(Math.random() * 10 + 20).toFixed(1)}% (30-day)
- **Market Conditions:** ${Math.random() > 0.5 ? 'Bullish' : 'Neutral'} with ${Math.random() > 0.5 ? 'High' : 'Moderate'} Volatility

## How I Can Help You
I can provide detailed information on:

- 📈 **Trading strategies and performance analysis**
- 🛡️ **Risk assessment and portfolio management**
- 📊 **Market trends and arbitrage opportunities**
- ⚙️ **System health monitoring and optimization**
- 🎨 **Custom data visualization and reporting**

Could you provide more specific details about what you'd like to know? I can generate detailed reports, analyze specific strategies, create custom visualizations, or provide recommendations based on current market conditions.`;
    }
    
    // Create the AI response message
    const aiMessage: ChatMessage = {
      id: generateId(),
      text: responseText,
      sender: 'ai',
      timestamp: Date.now(),
      attachments: attachments.length > 0 ? attachments : undefined
    };
    
    setIsLoading(false);
    return aiMessage;
  }, [simulateDelay, addInsight, generateId, conversationContext]);

  // Suggest a new trading strategy
  const suggestStrategy = useCallback(async (): Promise<Strategy> => {
    await simulateDelay('high');
    
    // Generate a random strategy
    const strategies = [
      {
        id: Math.floor(Math.random() * 1000),
        name: "Cross-DEX Arbitrage with ZK Privacy",
        description: "Triangular arbitrage across three major DEXs with optimized path finding and ZK privacy to prevent frontrunning.",
        pnl: Math.random() * 10 + 5,
        risk_level: 'medium',
        success_rate: Math.floor(Math.random() * 10 + 85)
      },
      {
        id: Math.floor(Math.random() * 1000),
        name: "Volatility Arbitrage with ML Prediction",
        description: "Exploit volatility mispricings between implied and realized volatility using machine learning predictions.",
        pnl: Math.random() * 8 + 3,
        risk_level: 'high',
        success_rate: Math.floor(Math.random() * 15 + 75)
      },
      {
        id: Math.floor(Math.random() * 1000),
        name: "Yield Farming Optimizer 3.0",
        description: "Automated yield farming across 15+ protocols with dynamic rebalancing and compound optimization.",
        pnl: Math.random() * 5 + 2,
        risk_level: 'low',
        success_rate: Math.floor(Math.random() * 5 + 90)
      },
      {
        id: Math.floor(Math.random() * 1000),
        name: "MEV Protection Service",
        description: "Provide MEV protection services for large transactions, capturing value that would otherwise go to searchers.",
        pnl: Math.random() * 12 + 8,
        risk_level: 'high',
        success_rate: Math.floor(Math.random() * 20 + 70)
      },
      {
        id: Math.floor(Math.random() * 1000),
        name: "Cross-Chain Arbitrage",
        description: "Exploit price differences between the same assets on different blockchains using optimized bridging.",
        pnl: Math.random() * 15 + 10,
        risk_level: 'high',
        success_rate: Math.floor(Math.random() * 15 + 75)
      }
    ];
    
    const selectedStrategy = strategies[Math.floor(Math.random() * strategies.length)];
    
    // Add an insight about the new strategy
    addInsight({
      title: `New Strategy Opportunity: ${selectedStrategy.name}`,
      description: `AI has identified a new ${selectedStrategy.risk_level} risk strategy with estimated ${selectedStrategy.pnl.toFixed(2)} ETH profit potential.`,
      confidence: Math.floor(Math.random() * 10 + 85),
      category: 'opportunity'
    });
    
    setIsLoading(false);
    return selectedStrategy;
  }, [simulateDelay, addInsight]);

  // Generate AI insights proactively
  useEffect(() => {
    // Generate a new insight every 30-60 seconds if the user is active
    const insightInterval = setInterval(() => {
      // Only generate insights if the user has interacted recently (within 5 minutes)
      if (Date.now() - lastQueryTimestamp < 5 * 60 * 1000) {
        const insightTypes = ['opportunity', 'risk', 'optimization', 'trend'] as const;
        const insightType = insightTypes[Math.floor(Math.random() * insightTypes.length)];
        
        let title = '';
        let description = '';
        
        if (insightType === 'opportunity') {
          title = `New Arbitrage Opportunity Detected`;
          description = `Identified ${(Math.random() * 0.3 + 0.1).toFixed(2)}% spread between Uniswap and SushiSwap for WETH/USDC pair.`;
        } else if (insightType === 'risk') {
          title = `Increased Correlation Risk`;
          description = `Strategy diversification has decreased, with ${Math.floor(Math.random() * 20 + 70)}% correlation across top strategies.`;
        } else if (insightType === 'optimization') {
          title = `Gas Optimization Potential`;
          description = `Batch processing transactions could reduce gas costs by ${Math.floor(Math.random() * 20 + 30)}% under current network conditions.`;
        } else {
          title = `Market Trend Shift Detected`;
          description = `On-chain metrics indicate ${Math.random() > 0.5 ? 'bullish' : 'bearish'} sentiment shift in the last ${Math.floor(Math.random() * 4 + 2)} hours.`;
        }
        
        addInsight({
          title,
          description,
          confidence: Math.floor(Math.random() * 15 + 80),
          category: insightType
        });
      }
    }, Math.random() * 30000 + 30000); // Random interval between 30-60 seconds
    
    return () => clearInterval(insightInterval);
  }, [lastQueryTimestamp, addInsight]);

  // Simulate market data updates
  useEffect(() => {
    const marketInterval = setInterval(() => {
      setMarketData(prev => ({
        ...prev,
        ethPrice: prev.ethPrice * (1 + (Math.random() - 0.5) * 0.01), // Small random change
        ethChange24h: prev.ethChange24h + (Math.random() - 0.5) * 0.5, // Adjust 24h change
        gasPrice: Math.max(10, prev.gasPrice + (Math.random() - 0.5) * 5), // Adjust gas price
        volatilityIndex: Math.max(20, Math.min(90, prev.volatilityIndex + (Math.random() - 0.5) * 3)), // Adjust volatility
        opportunitySpread: Math.max(0.05, Math.min(0.5, prev.opportunitySpread + (Math.random() - 0.5) * 0.02)) // Adjust spread
      }));
    }, 60000); // Update every minute
    
    return () => clearInterval(marketInterval);
  }, []);

  return { 
    analyzeAlert, 
    generateChatResponse,
    suggestStrategy,
    isLoading, 
    confidence,
    insights,
    addInsight,
    marketData
  };
};