import { useState, useCallback } from 'react';
import { Alert, ChatMessage, Insight } from '../types';

export const useArtemisAI = () => {
  const [isThinking, setIsThinking] = useState(false);
  const [confidence, setConfidence] = useState(85);
  const [conversationContext, setConversationContext] = useState<string[]>([]);
  const [aiInsights, setAiInsights] = useState<Insight[]>([]);

  const simulateThinking = useCallback(async (complexity: 'low' | 'medium' | 'high' = 'medium') => {
    const delay = complexity === 'low' ? 800 : complexity === 'medium' ? 1500 : 2500;
    await new Promise(resolve => setTimeout(resolve, delay));
  }, []);

  const generateId = useCallback(() => {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  }, []);

  const addInsight = useCallback((insight: Omit<Insight, 'id' | 'timestamp'>) => {
    const newInsight: Insight = {
      ...insight,
      id: generateId(),
      timestamp: Date.now()
    };
    
    setAiInsights(prev => [newInsight, ...prev].slice(0, 10));
    return newInsight;
  }, [generateId]);

  const analyzeAlert = useCallback(async (alert: Alert): Promise<string> => {
    setIsThinking(true);
    await simulateThinking(alert.level === 'critical' ? 'high' : 'medium');
    
    setConversationContext(prev => [...prev, `Analyzed ${alert.level} alert from ${alert.source}`]);
    
    const newConfidence = Math.floor(75 + Math.random() * 20);
    setConfidence(newConfidence);
    
    let analysis = '';
    
    if (alert.source === 'Oracle Sentinel' && alert.message.includes('oracle deviation')) {
      const pair = alert.metadata?.pair || 'ETH/USD';
      const deviation = alert.metadata?.deviation || 1.5;
      
      addInsight({
        title: `Oracle Deviation: ${pair}`,
        description: `${pair} oracle deviated ${deviation}% from consensus, exceeding threshold.`,
        confidence: newConfidence,
        category: 'risk'
      });
      
      analysis = `# 🚨 Critical Oracle Deviation Analysis

## Alert Summary
- **Pair**: ${pair}
- **Deviation**: ${deviation}%
- **Severity**: ${alert.level.toUpperCase()}
- **Time**: ${new Date(alert.timestamp).toLocaleString()}

## Risk Assessment
This deviation pattern suggests:
- **Oracle manipulation**: ${Math.floor(15 + Math.random() * 20)}% probability
- **Network congestion**: ${Math.floor(30 + Math.random() * 25)}% probability  
- **Legitimate price action**: ${Math.floor(20 + Math.random() * 30)}% probability

## Immediate Actions
1. 🔴 **CRITICAL**: Pause ${pair} strategies
2. 🔴 **CRITICAL**: Switch to backup oracles
3. 🟡 **URGENT**: Verify prices across exchanges
4. 🟡 **MONITOR**: Watch for cascading effects

**AI Confidence**: ${newConfidence}%`;

    } else if (alert.source === 'Risk Engine') {
      addInsight({
        title: "Portfolio Risk Warning",
        description: "Risk exposure approaching critical thresholds.",
        confidence: newConfidence,
        category: 'risk'
      });
      
      analysis = `# ⚠️ Risk Management Alert

## Risk Analysis
Current portfolio showing elevated risk metrics:

- **VaR (24h)**: ${(Math.random() * 10 + 15).toFixed(2)} ETH
- **Correlation Risk**: High ETH exposure detected
- **Diversification Score**: ${Math.floor(40 + Math.random() * 30)}/100

## Recommendations
1. Consider position rebalancing
2. Implement hedging strategies
3. Reduce leverage on correlated assets

**Risk Level**: ${alert.level.toUpperCase()}`;

    } else {
      analysis = `# 📊 Alert Analysis: ${alert.source}

**Message**: ${alert.message}
**Level**: ${alert.level.toUpperCase()}
**Time**: ${new Date(alert.timestamp).toLocaleString()}

## Analysis
This ${alert.level} alert requires ${alert.level === 'critical' ? 'immediate' : 'prompt'} attention. 

## Recommended Actions
${alert.metadata?.suggestedActions?.map(action => `- ${action}`).join('\n') || '- Review alert details\n- Assess impact on active strategies\n- Monitor for related issues'}

**AI Confidence**: ${newConfidence}%`;
    }
    
    setIsThinking(false);
    return analysis;
  }, [simulateThinking, addInsight]);

  const generateChatResponse = useCallback(async (input: string, chatHistory: ChatMessage[]): Promise<ChatMessage> => {
    setIsThinking(true);
    await simulateThinking('medium');
    
    setConversationContext(prev => [...prev, `User asked: ${input.substring(0, 50)}`]);
    
    const inputLower = input.toLowerCase();
    let responseText = '';
    let attachments: any[] = [];

    if (inputLower.includes('strategy') || inputLower.includes('profit')) {
      responseText = `# 📈 Strategy Performance Analysis

Based on current data, here's what I'm seeing:

## Top Performers
- **Tri-Arbitrage V2**: +14.23 ETH (89% success rate)
- **MEV Backrun**: +8.91 ETH (76% success rate)
- **Cross-DEX Arb**: +3.45 ETH (82% success rate)

## Key Insights
- Total portfolio PnL trending positive
- Gas efficiency could be improved on MEV strategies
- Consider scaling successful arbitrage strategies

## Recommendations
1. **Scale Up**: Increase allocation to Tri-Arbitrage V2
2. **Optimize**: Improve MEV Backrun gas efficiency
3. **Monitor**: Watch for new arbitrage opportunities

Would you like me to dive deeper into any specific strategy?`;

    } else if (inputLower.includes('risk') || inputLower.includes('exposure')) {
      responseText = `# 🛡️ Risk Assessment Overview

## Current Risk Profile
- **Portfolio VaR**: ${(Math.random() * 8 + 12).toFixed(2)} ETH (24h)
- **Max Drawdown**: ${(Math.random() * 5 + 8).toFixed(1)}%
- **Correlation Risk**: Moderate (${Math.floor(70 + Math.random() * 15)}% ETH exposure)

## Risk Factors
- **Oracle Dependency**: Primary risk vector
- **Gas Price Volatility**: Secondary concern
- **Market Correlation**: Within acceptable limits

## Mitigation Status
✅ Stop-loss mechanisms active
✅ Position size limits enforced
⚠️ Diversification could be improved

Current risk levels are **manageable** but warrant continued monitoring.`;

    } else if (inputLower.includes('gas') || inputLower.includes('fee')) {
      responseText = `# ⛽ Gas Analysis & Optimization

## Current Network Conditions
- **Base Fee**: ${Math.floor(20 + Math.random() * 30)} gwei
- **Priority Fee**: ${Math.floor(2 + Math.random() * 5)} gwei
- **Network Congestion**: ${Math.random() > 0.5 ? 'Moderate' : 'Low'}

## Strategy Impact
- **High-frequency trades**: ${Math.random() > 0.5 ? 'Profitable' : 'Marginal'}
- **Large arbitrage**: Active and profitable
- **MEV opportunities**: Gas-adjusted returns positive

## Optimization Tips
1. **Batch transactions** where possible
2. **Use L2 solutions** for smaller trades
3. **Time execution** during low-congestion periods

Gas costs are currently **${Math.random() > 0.6 ? 'favorable' : 'elevated'}** for most strategies.`;

    } else if (inputLower.includes('hello') || inputLower.includes('hi') || inputLower.includes('how are you')) {
      responseText = `# 👋 Hello! I'm Artemis AI

I'm doing excellent! My systems are running at peak performance and I'm actively monitoring your trading portfolio.

## Current Status
- **System Health**: All green ✅
- **Active Strategies**: ${Math.floor(3 + Math.random() * 3)} running
- **Recent Performance**: Strong positive trends
- **Market Conditions**: ${Math.random() > 0.5 ? 'Favorable' : 'Moderate'} for arbitrage

## How I Can Help
- 📊 **Strategy Analysis**: Performance insights and optimization
- 🛡️ **Risk Management**: Portfolio monitoring and alerts  
- 📈 **Market Intelligence**: Opportunities and trends
- ⚙️ **System Monitoring**: Health checks and diagnostics

What would you like to explore today?`;

    } else if (inputLower.includes('chart') || inputLower.includes('graph')) {
      responseText = `# 📊 Chart Analysis Request

I'd be happy to create visualizations for you! Here's a performance chart showing recent strategy returns:`;
      
      attachments.push({
        type: 'chart',
        data: {
          type: 'line',
          title: 'Strategy Performance (24h)',
          labels: Array.from({length: 24}, (_, i) => `${i}:00`),
          datasets: [
            {
              label: 'Tri-Arbitrage V2',
              data: Array.from({length: 24}, () => Math.random() * 0.5 + 0.3),
              color: '#4ade80'
            },
            {
              label: 'MEV Backrun', 
              data: Array.from({length: 24}, () => Math.random() * 0.8 + 0.1),
              color: '#60a5fa'
            }
          ]
        }
      });

    } else {
      responseText = `# 🤖 Artemis AI Response

I understand you're asking about "${input}". 

## Analysis
Based on current market conditions and system state, I can provide insights on various aspects of your trading operations.

## Available Topics
- **Trading Strategies**: Performance analysis and optimization
- **Risk Management**: Portfolio exposure and safety metrics
- **Market Analysis**: Opportunities and trend identification  
- **System Health**: Monitoring and diagnostics
- **Custom Analysis**: Specific questions about your operations

What specific aspect would you like me to analyze in detail?`;
    }

    const response: ChatMessage = {
      id: generateId(),
      text: responseText,
      sender: 'ai',
      timestamp: Date.now(),
      attachments: attachments.length > 0 ? attachments : undefined
    };

    setIsThinking(false);
    return response;
  }, [simulateThinking, generateId]);

  return {
    analyzeAlert,
    generateChatResponse,
    isThinking,
    confidence,
    conversationContext,
    aiInsights,
    addInsight
  };
};
