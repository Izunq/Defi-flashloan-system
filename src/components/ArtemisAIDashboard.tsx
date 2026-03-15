import React, { useState, useEffect, useMemo, FC, ReactNode, useCallback } from 'react';
import { Line, Bar } from 'react-chartjs-2';

// --- MOCK ICONS (as SVGs to avoid external dependencies) ---
const IconComponents = {
    CheckCircleIcon: ({ className }: { className: string }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className={className}><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>,
    XCircleIcon: ({ className }: { className: string }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className={className}><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>,
    ExclamationTriangleIcon: ({ className }: { className: string }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className={className}><path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" /></svg>,
    SparklesIcon: ({ className }: { className: string }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.898 20.572L16.5 21.75l-.398-1.178a3.375 3.375 0 00-2.455-2.456L12.75 18l1.178-.398a3.375 3.375 0 002.455-2.456L16.5 14.25l.398 1.178a3.375 3.375 0 002.456 2.456L20.25 18l-1.178.398a3.375 3.375 0 00-2.456 2.456z" /></svg>,
    PaperAirplaneIcon: ({ className }: { className: string }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" /></svg>,
    ChartBarIcon: ({ className }: { className: string }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>,
    BoltIcon: ({ className }: { className: string }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" /></svg>,
    ArrowPathIcon: ({ className }: { className: string }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>,
};

// --- TYPE DEFINITIONS ---
interface Alert { id: number; source: string; message: string; level: 'critical' | 'warning' | 'info'; timestamp: number; metadata?: any; }
interface Strategy { id: number; name: string; pnl: number; active: boolean; risk_level: 'low' | 'medium' | 'high'; success_rate?: number; }
interface SystemHealth { [service: string]: 'Operational' | 'Degraded' | 'Outage'; }
interface AIInsight { confidence: number; summary: string; details: any; }
interface ZKProof { id: string; status: 'Verified' | 'Verifying' | 'Failed'; verificationTime: number; proofType: string; error?: string }
interface RiskMetrics { var: number; maxDrawdown: number; exposure: number; riskScore: number; portfolioBeta: number; sharpeRatio: number; }
interface ChatMessage { id: string; text: string; sender: 'user' | 'ai'; timestamp: number; isProcessing?: boolean; attachments?: any[] }

// --- MOCK DATA HOOKS (Simulating backend services) ---
const useSystemHealth = () => useMemo(() => ({ 
    data: { 
        'Node.js BFF': 'Operational', 
        'Postgres DB': 'Operational', 
        'Python AI Agent': 'Operational', 
        'MATLAB RiskEngine': 'Degraded', 
        'Artemis AI Core': 'Operational', 
        'Sentinel Agents': 'Operational', 
        'Blockchain Node': 'Operational' 
    }, 
    isLoading: false, 
    error: null,
    metrics: {
        timestamps: Array.from({length: 24}, (_, i) => Date.now() - (23-i) * 3600000),
        cpu: Array.from({length: 24}, () => Math.floor(Math.random() * 30) + 20),
        memory: Array.from({length: 24}, () => Math.floor(Math.random() * 25) + 40),
    }
}), []);

const useSentinelAlerts = () => {
    const [alerts, setAlerts] = useState<Alert[]>([
        { id: 1, source: 'Oracle Sentinel', message: 'ETH/USD price deviation detected: 1.7% above consensus.', level: 'critical', timestamp: Date.now() - 45000, metadata: { pair: 'ETH/USD', deviation: 1.7, threshold: 1.5 } },
        { id: 2, source: 'MEV Sentinel', message: 'Large sandwich opportunity: $547K USDC swap detected.', level: 'warning', timestamp: Date.now() - 180000 },
        { id: 3, source: 'Risk Engine', message: 'Portfolio correlation risk increased by 15%.', level: 'warning', timestamp: Date.now() - 360000 },
        { id: 4, source: 'Gas Sentinel', message: 'Gas price spike detected: 89 gwei (normal: 27 gwei)', level: 'info', timestamp: Date.now() - 420000 }
    ]);

    const markAsRead = useCallback((id: number) => {
        setAlerts(prev => prev.filter(alert => alert.id !== id));
    }, []);

    const acknowledge = useCallback((id: number) => {
        setAlerts(prev => prev.map(alert => 
            alert.id === id ? {...alert, level: 'info' as const} : alert
        ));
    }, []);

    return { data: alerts, markAsRead, acknowledge, isLoading: false, error: null };
};

const useAIStrategyData = () => useMemo(() => ({ 
    data: { 
        confidence: 0.87, 
        summary: 'High-confidence triangular arbitrage opportunity detected across Uniswap V3, SushiSwap, and Balancer.', 
        details: { 
            pair: 'USDC/WETH/WBTC', 
            potentialProfit: 1.23, 
            requiredCapital: 180000, 
            risk_assessment: 'Medium' 
        } 
    }, 
    isLoading: false, 
    error: null 
}), []);

const useZKProofData = () => useMemo(() => ({ 
    data: [ 
        { id: 'zk-a4b8c1', status: 'Verified', verificationTime: 187, proofType: 'Strategy V35' }, 
        { id: 'zk-d9e2f7', status: 'Verifying', verificationTime: -1, proofType: 'Compliance Circuit' }, 
        { id: 'zk-g5h1i3', status: 'Failed', verificationTime: 210, proofType: 'Strategy V34', error: 'Invalid witness' } 
    ], 
    isLoading: false, 
    error: null 
}), []);

const useRiskMetrics = () => useMemo(() => ({ 
    data: { 
        var: 12.54, 
        maxDrawdown: 0.152, 
        exposure: 1247800, 
        riskScore: 68, 
        portfolioBeta: 0.85, 
        sharpeRatio: 2.1 
    }, 
    isLoading: false, 
    error: null 
}), []);

const useStrategies = () => {
    const [strategies, setStrategies] = useState<Strategy[]>([
        { id: 1, name: 'Tri-Arbitrage V2', pnl: 14.23, active: true, risk_level: 'medium', success_rate: 89 },
        { id: 2, name: 'Flash-Mint Hedge', pnl: 5.12, active: false, risk_level: 'low', success_rate: 94 },
        { id: 3, name: 'MEV Backrun', pnl: 8.87, active: true, risk_level: 'high', success_rate: 76 }
    ]);

    const toggleActive = useCallback((id: number) => {
        setStrategies(prev => prev.map(strategy => 
            strategy.id === id ? {...strategy, active: !strategy.active} : strategy
        ));
    }, []);

    const stats = useMemo(() => ({
        totalPnl: strategies.reduce((sum, s) => sum + s.pnl, 0),
        activeCount: strategies.filter(s => s.active).length,
        avgSuccessRate: strategies.reduce((sum, s) => sum + (s.success_rate || 0), 0) / strategies.length
    }), [strategies]);

    return { data: strategies, toggleActive, stats, isLoading: false, error: null };
};

const useWebSocket = () => useMemo(() => ({ connectionStatus: 'connected' }), []);

// --- ARTEMIS AI CORE ---
const useArtemisAI = () => {
    const [isThinking, setIsThinking] = useState(false);
    const [insights, setInsights] = useState<any[]>([]);
    const [capabilities, setCapabilities] = useState([
        { id: 'analysis', name: 'Data Analysis', description: 'Analyze market data, transactions, and patterns' },
        { id: 'strategy', name: 'Strategy Development', description: 'Create and optimize trading strategies' },
        { id: 'risk', name: 'Risk Management', description: 'Assess and mitigate portfolio risks' },
        { id: 'monitoring', name: 'System Monitoring', description: 'Monitor system health and performance' },
        { id: 'research', name: 'Market Research', description: 'Research market trends and opportunities' },
        { id: 'automation', name: 'Workflow Automation', description: 'Automate repetitive tasks and processes' },
        { id: 'learning', name: 'Continuous Learning', description: 'Learn from new data and improve over time' }
    ]);

    // Simulate AI thinking time
    const simulateThinking = useCallback(async (complexity: 'low' | 'medium' | 'high' = 'medium') => {
        setIsThinking(true);
        const delay = complexity === 'low' ? 800 : complexity === 'medium' ? 1500 : 2500;
        await new Promise(resolve => setTimeout(resolve, delay + Math.random() * 500));
        setIsThinking(false);
    }, []);
    
    // Analyze alerts with context-aware responses
    const analyzeAlert = useCallback(async (alert: Alert) => {
        await simulateThinking(alert.level === 'critical' ? 'high' : 'medium');
        
        let analysis = {
            text: '',
            recommendations: [] as string[]
        };
        
        if (alert.source === 'Oracle Sentinel' && alert.message.includes('deviation')) {
            analysis.text = `**🚨 Critical Oracle Price Deviation Analysis**\n\n**IMMEDIATE THREAT ASSESSMENT: HIGH RISK**\n\n**1. Technical Analysis:**\nThe ETH/USD oracle has deviated ${alert.metadata?.deviation}% from consensus, exceeding our ${alert.metadata?.threshold}% threshold. This pattern matches:\n- Oracle manipulation attack (likelihood: 15%)\n- Exchange-specific flash crash (likelihood: 40%)\n- Network congestion causing feed delays (35%)\n\n**2. Risk Impact:**\n- **Potential Loss Exposure:** $250,000 - $1,200,000 (based on current positions)\n- **Liquidation Risk:** MODERATE (if deviation persists >5 minutes)\n\n**3. Immediate Actions Required:**\n🔴 **CRITICAL:** Pause all active arbitrage strategies using ETH/USD.\n🟡 **URGENT:** Cross-verify prices on Coinbase Pro, Binance, Kraken.\n\n**Confidence Score: 87%**`;
            analysis.recommendations = [
                'Pause all active arbitrage strategies using ETH/USD',
                'Cross-verify prices on Coinbase Pro, Binance, Kraken',
                'Prepare emergency liquidity for potential liquidation events',
                'Activate oracle fallback mechanism'
            ];
        } else {
            analysis.text = `**🔍 Alert Analysis: ${alert.source}**\n\n**Risk Level:** ${alert.level.toUpperCase()}\n\nBased on current market conditions and historical patterns from our database, this ${alert.level} alert requires your attention.\n\n**Recommended Actions:**\n1. Evaluate exposure to related trading pairs/protocols.\n2. Increase surveillance on correlated metrics.\n3. ${alert.level === 'critical' ? 'Execute emergency protocols immediately.' : 'Monitor and prepare contingency plans.'}`;
            analysis.recommendations = [
                'Evaluate exposure to related trading pairs/protocols',
                'Increase surveillance on correlated metrics',
                alert.level === 'critical' ? 'Execute emergency protocols immediately' : 'Monitor and prepare contingency plans'
            ];
        }
        
        return analysis;
    }, [simulateThinking]);

    // Generate strategy suggestions
    const suggestStrategy = useCallback(async () => {
        await simulateThinking('high');
        return `**💡 AI Strategy Suggestion: Cross-Chain Volatility Arbitrage**\n\n**Market Opportunity:**\nCurrent analysis shows a significant volatility pricing difference between Ethereum Mainnet and Arbitrum for the ETH/GMX pair.\n\n**Strategy Mechanics:**\n1. **Monitor:** Use Sentinel agents to watch for a volatility spread > 3%.\n2. **Execute:** Take a long volatility position on the lower-vol chain and a short position on the higher-vol chain.\n3. **Hedge:** Use dynamic hedging to remain delta-neutral.\n\n**Projected Performance:**\n- **Sharpe Ratio:** ~2.1\n- **Annualized Return:** 35-50%\n- **Max Drawdown:** 7.5%`;
    }, [simulateThinking]);

    // Main chat response generator
    const generateChatResponse = useCallback(async (input: string, previousMessages: ChatMessage[]) => {
        await simulateThinking();
        const lowerInput = input.toLowerCase();
        let responseText = '';

        // Context-aware response generation
        if (lowerInput.includes('help') || lowerInput.includes('what can you do')) {
            responseText = `**Hello! I'm Artemis, your AI assistant.**\n\nI can help you with a wide range of tasks:\n\n**💹 Trading & Investment**\n- Analyze market trends and opportunities\n- Develop and optimize trading strategies\n- Monitor portfolio performance\n\n**🔍 Data Analysis**\n- Process and visualize complex datasets\n- Identify patterns and anomalies\n- Generate insights from transaction data\n\n**🛡️ Security & Risk Management**\n- Monitor for suspicious activities\n- Assess portfolio risk exposure\n- Recommend risk mitigation strategies\n\n**🔧 System Management**\n- Monitor system health and performance\n- Alert on critical issues\n- Suggest optimization opportunities\n\n**🤖 Automation**\n- Create automated workflows\n- Schedule recurring tasks\n- Integrate with external systems\n\nHow can I assist you today?`;
        } 
        else if (lowerInput.includes('health') || lowerInput.includes('status') || lowerInput.includes('system')) {
            responseText = `**System Health Overview:**\n\nMost services are **Operational**.\n\n⚠️ **Degraded Service:** The **RiskEngine Bridge** is showing increased latency. Our backup models are handling calculations as a fallback, but with slightly lower precision.\n\nAll other systems are functioning normally. Would you like me to:\n\n1. Show detailed system metrics\n2. Investigate the RiskEngine issue\n3. Run a full system diagnostic`;
        } 
        else if (lowerInput.includes('risk') || lowerInput.includes('exposure')) {
            responseText = `**Current Risk Profile:**\n\n- **Portfolio VaR (99%):** 12.54%\n- **Max Drawdown:** 15.2%\n- **Current Exposure:** $1,247,800\n- **Risk Score:** 68/100 (Moderate)\n\nYour current risk profile is within acceptable parameters, but I'm noticing increased correlation between your active strategies. Consider diversifying to reduce systemic risk.\n\nWould you like me to:\n\n1. Suggest diversification strategies\n2. Run a stress test simulation\n3. Analyze specific risk factors`;
        } 
        else if (lowerInput.includes('strategy') || lowerInput.includes('suggest') || lowerInput.includes('recommend')) {
            responseText = `**Strategy Recommendations**\n\nBased on current market conditions and your risk profile, here are three potential strategies:\n\n**1. Cross-Chain Arbitrage**\n- Exploit price differences between L1 and L2 chains\n- Moderate risk, potential 15-20% APY\n\n**2. Liquidity Provision**\n- Provide liquidity to stable pairs on DEXs\n- Lower risk, potential 8-12% APY\n\n**3. Yield Farming Rotation**\n- Algorithmically rotate between top yield farms\n- Higher risk, potential 25-40% APY\n\nWould you like me to elaborate on any of these strategies?`;
        } 
        else if (lowerInput.includes('alert') || lowerInput.includes('warning') || lowerInput.includes('notification')) {
            responseText = `**Active Alerts Summary:**\n\n🚨 **Critical (1):** ETH/USD price deviation detected\n⚠️ **Warnings (2):** Large sandwich opportunity, Portfolio correlation risk\n📊 **Info (1):** Gas price spike\n\nThe most urgent issue is the ETH/USD price deviation. Would you like me to:\n\n1. Analyze this alert in detail\n2. Show all active alerts\n3. Suggest response actions`;
        } 
        else if (lowerInput.includes('market') || lowerInput.includes('trend') || lowerInput.includes('analysis')) {
            responseText = `**Market Analysis**\n\nRecent market trends show:\n\n- **ETH:** Consolidating in the $3,200-3,500 range with decreasing volatility\n- **DeFi:** TVL increasing 8.2% over the past week\n- **L2s:** Transaction volume up 23% month-over-month\n\nNotable opportunities:\n\n1. Increased options activity suggesting bullish sentiment for Q4\n2. Growing liquidity in newer L2 ecosystems\n3. Decreasing correlation between BTC and altcoin markets\n\nWould you like a deeper analysis of any specific sector?`;
        }
        else if (lowerInput.includes('optimize') || lowerInput.includes('improve') || lowerInput.includes('enhance')) {
            responseText = `**Optimization Opportunities**\n\nI've identified several areas for potential improvement:\n\n**1. Gas Optimization**\n- Current average: 45 gwei per transaction\n- Potential savings: ~15% by implementing batching\n\n**2. Execution Timing**\n- Transactions clustering during high-fee periods\n- Potential improvement: Time-based execution strategy\n\n**3. Portfolio Allocation**\n- Current allocation has 62% correlation\n- Suggested: Rebalance to reduce correlation to <40%\n\nWhich area would you like me to focus on first?`;
        }
        else if (lowerInput.includes('learn') || lowerInput.includes('explain') || lowerInput.includes('how')) {
            responseText = `**Learning Resources**\n\nI'd be happy to explain concepts or provide learning resources. Some popular topics include:\n\n**1. DeFi Fundamentals**\n- Liquidity pools, impermanent loss, yield farming\n\n**2. Trading Strategies**\n- Arbitrage, grid trading, statistical arbitrage\n\n**3. Risk Management**\n- Position sizing, hedging, portfolio diversification\n\n**4. Technical Concepts**\n- MEV, flash loans, cross-chain bridges\n\nWhat specific topic would you like to learn more about?`;
        }
        else {
            // Default response for other queries
            responseText = `I'm here to help with a wide range of tasks including market analysis, strategy development, risk management, system monitoring, and more.\n\nYou can ask me about:\n\n- Market trends and opportunities\n- Trading strategy suggestions\n- Portfolio risk assessment\n- System health and alerts\n- Data analysis and visualization\n- Automation opportunities\n\nHow can I assist you today?`;
        }

        return {
            id: Date.now().toString(36),
            text: responseText,
            sender: 'ai',
            timestamp: Date.now()
        } as ChatMessage;
    }, [simulateThinking, suggestStrategy]);

    return { 
        analyzeAlert, 
        generateChatResponse, 
        suggestStrategy, 
        isThinking, 
        insights,
        capabilities
    };
};

// --- UI COMPONENTS ---
const Card: FC<{ className?: string; children: ReactNode }> = ({ className = '', children }) => (
    <div className={`bg-gray-800/60 rounded-lg border border-gray-700/50 ${className}`}>
        {children}
    </div>
);

const Badge: FC<{ 
    type?: 'info' | 'success' | 'warning' | 'error' | 'neutral';
    children: ReactNode;
    className?: string;
}> = ({ type = 'info', children, className = '' }) => {
    const colors = {
        info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        success: 'bg-green-500/20 text-green-400 border-green-500/30',
        warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        error: 'bg-red-500/20 text-red-400 border-red-500/30',
        neutral: 'bg-gray-500/20 text-gray-300 border-gray-500/30'
    };
    
    return (
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${colors[type]} ${className}`}>
            {children}
        </span>
    );
};

const Widget: FC<{
    title: ReactNode;
    children: ReactNode;
    className?: string;
    headerActions?: ReactNode;
    loading?: boolean;
}> = ({ title, children, className = '', headerActions, loading = false }) => {
    return (
        <Card className={`overflow-hidden ${className}`}>
            <div className="flex items-center justify-between p-3 border-b border-gray-700/50">
                <div className="flex items-center space-x-2 font-medium">
                    {title}
                </div>
                <div className="flex items-center space-x-2">
                    {headerActions}
                    {loading && (
                        <div className="animate-spin">
                            <IconComponents.ArrowPathIcon className="w-4 h-4 text-gray-400" />
                        </div>
                    )}
                </div>
            </div>
            <div className="p-3">
                {children}
            </div>
        </Card>
    );
};

// --- MARKDOWN RENDERER ---
const MarkdownRenderer: FC<{ content: string }> = ({ content }) => {
    // Simple markdown renderer (just for demo)
    const formattedContent = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '<br/><br/>')
        .replace(/\n/g, '<br/>');
    
    return <div dangerouslySetInnerHTML={{ __html: formattedContent }} />;
};

// --- MAIN DASHBOARD ---
const ArtemisAIDashboard: FC = () => {
    // Hooks for data
    const { data: systemHealth, metrics: systemMetrics } = useSystemHealth();
    const { data: alerts, markAsRead, acknowledge } = useSentinelAlerts();
    const { data: strategies, stats: strategyStats, toggleActive } = useStrategies();
    const { data: aiStrategyData } = useAIStrategyData();
    const { data: zkProofs } = useZKProofData();
    const { data: riskMetrics } = useRiskMetrics();
    const { analyzeAlert, generateChatResponse, isThinking } = useArtemisAI();
    
    // State
    const [showModal, setShowModal] = useState(false);
    const [modalContent, setModalContent] = useState<{ title: string; content: ReactNode }>({ title: '', content: null });
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
        { 
            id: 'welcome',
            text: `**Hello! 👋 Welcome to Artemis AI**\n\nI'm your versatile AI assistant designed to help with a wide range of tasks:\n\n**💹 Trading & Investment**\n- Market analysis and opportunity detection\n- Strategy development and optimization\n- Portfolio management and risk assessment\n\n**🔍 Data Analysis**\n- Process and visualize complex datasets\n- Identify patterns and anomalies\n- Generate actionable insights\n\n**🛡️ Security & System Management**\n- Monitor system health and performance\n- Alert on critical issues\n- Suggest optimization opportunities\n\n**🤖 Automation & Learning**\n- Create automated workflows\n- Provide educational resources\n- Continuously improve from feedback\n\nHow can I assist you today?`, 
            sender: 'ai', 
            timestamp: Date.now() 
        }
    ]);
    const [chatInput, setChatInput] = useState('');
    
    // Chart data
    const systemMetricsChartData = systemMetrics ? {
        labels: systemMetrics.timestamps.map(t => new Date(t).toLocaleTimeString()),
        datasets: [
            {
                label: 'CPU Load (%)',
                data: systemMetrics.cpu,
                borderColor: '#60a5fa',
                backgroundColor: 'rgba(96, 165, 250, 0.1)',
                tension: 0.3,
            },
            {
                label: 'Memory Usage (%)',
                data: systemMetrics.memory,
                borderColor: '#34d399',
                backgroundColor: 'rgba(52, 211, 153, 0.1)',
                tension: 0.3,
            }
        ]
    } : null;
    
    // Handle alert analysis
    const handleAlertAnalysis = useCallback(async (alert: Alert) => {
        const analysis = await analyzeAlert(alert);
        setModalContent({
            title: `AI Analysis: ${alert.source} Alert`,
            content: (
                <div>
                    <div className="mb-4">
                        <Badge 
                            type={
                                alert.level === 'critical' ? 'error' :
                                alert.level === 'warning' ? 'warning' : 'info'
                            }
                            className="mb-2"
                        >
                            {alert.level.toUpperCase()}
                        </Badge>
                        <p className="text-lg font-medium mb-1">{alert.message}</p>
                        <p className="text-sm text-gray-400">
                            {new Date(alert.timestamp).toLocaleString()} • {alert.source}
                        </p>
                    </div>
                    
                    <div className="mb-4 p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
                        <h3 className="text-sm font-medium text-gray-300 mb-2">AI Analysis</h3>
                        <MarkdownRenderer content={analysis.text} />
                    </div>
                    
                    <div className="mb-4">
                        <h3 className="text-sm font-medium text-gray-300 mb-2">Recommended Actions</h3>
                        <ul className="space-y-2">
                            {analysis.recommendations.map((rec: string, index: number) => (
                                <li key={index} className="flex items-start space-x-2">
                                    <IconComponents.CheckCircleIcon className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                                    <span>{rec}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                    
                    <div className="flex justify-end space-x-3">
                        <button 
                            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded font-medium transition-colors"
                            onClick={() => {
                                acknowledge(alert.id);
                                setShowModal(false);
                            }}
                        >
                            Acknowledge
                        </button>
                        <button 
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium transition-colors"
                            onClick={() => {
                                markAsRead(alert.id);
                                setShowModal(false);
                            }}
                        >
                            Mark as Resolved
                        </button>
                    </div>
                </div>
            )
        });
        setShowModal(true);
    }, [analyzeAlert, acknowledge, markAsRead]);
    
    // Handle sending chat messages
    const handleSendMessage = useCallback(async () => {
        if (!chatInput.trim() || isThinking) return;
        
        // Add user message
        const userMessage: ChatMessage = { 
            id: Date.now().toString(36),
            text: chatInput, 
            sender: 'user', 
            timestamp: Date.now() 
        };
        setChatMessages(prev => [...prev, userMessage]);
        setChatInput('');
        
        // Add temporary AI message with loading state
        const tempId = Date.now().toString(36) + Math.random().toString(36).substring(2);
        const tempMessage: ChatMessage = {
            id: tempId,
            text: '...',
            sender: 'ai',
            timestamp: Date.now(),
            isProcessing: true
        };
        setChatMessages(prev => [...prev, tempMessage]);
        
        // Generate AI response
        const response = await generateChatResponse(chatInput, chatMessages);
        
        // Replace temporary message with actual response
        setChatMessages(prev => 
            prev.map(msg => msg.id === tempId ? response : msg)
        );
    }, [chatInput, isThinking, generateChatResponse, chatMessages]);
    
    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
            {/* Top Navigation */}
            <header className="bg-gray-800/60 border-b border-gray-700/50 sticky top-0 z-10">
                <div className="flex items-center justify-between px-4 py-2">
                    <div className="flex items-center space-x-3">
                        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-1.5">
                            <IconComponents.SparklesIcon className="w-5 h-5 text-white" />
                        </div>
                        <h1 className="text-lg font-semibold">
                            <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                                Artemis AI Platform
                            </span>
                        </h1>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2 bg-gray-800/80 px-3 py-1.5 rounded-full border border-gray-700/50">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                            <span className="text-xs font-medium">AI Core Online</span>
                        </div>
                        
                        <div className="hidden sm:flex items-center space-x-3">
                            <div className="text-blue-400 bg-blue-500/10 px-2 py-1 rounded-md border border-blue-500/20 text-sm flex items-center space-x-1">
                                <IconComponents.BoltIcon className="w-4 h-4" />
                                <span>AI Powered</span>
                            </div>
                            <div className="text-purple-400 bg-purple-500/10 px-2 py-1 rounded-md border border-purple-500/20 text-sm">
                                {useArtemisAI().capabilities.length} Capabilities
                            </div>
                        </div>
                    </div>
                </div>
            </header>
            
            {/* Main Content */}
            <main className="flex-1 p-4">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {/* Left Column */}
                    <div className="lg:col-span-2 space-y-4">
                        {/* System Health */}
                        <Widget 
                            title={<span className="flex items-center space-x-2"><IconComponents.ChartBarIcon className="w-5 h-5 text-blue-400" /><span>System Health</span></span>}
                        >
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 mb-4">
                                {Object.entries(systemHealth || {}).map(([service, status]) => (
                                    <div key={service} className="bg-gray-800/30 p-2 rounded-lg border border-gray-700/50">
                                        <div className="text-xs text-gray-400 mb-1">{service}</div>
                                        <div className="flex items-center space-x-1.5">
                                            <div className={`w-2 h-2 rounded-full ${
                                                status === 'Operational' ? 'bg-green-400' :
                                                status === 'Degraded' ? 'bg-yellow-400' : 'bg-red-400'
                                            }`} />
                                            <Badge 
                                                type={
                                                    status === 'Operational' ? 'success' :
                                                    status === 'Degraded' ? 'warning' : 'error'
                                                }
                                            >
                                                {status}
                                            </Badge>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            
                            {systemMetricsChartData && (
                                <div className="mt-4 bg-gray-800/30 p-3 rounded-lg border border-gray-700/50">
                                    <h4 className="text-xs font-medium text-gray-300 mb-2">System Metrics (24h)</h4>
                                    <div className="h-40">
                                        <Line 
                                            data={systemMetricsChartData}
                                            options={{
                                                responsive: true,
                                                maintainAspectRatio: false,
                                                scales: {
                                                    y: {
                                                        ticks: { color: '#9ca3af' },
                                                        grid: { color: 'rgba(55, 65, 81, 0.3)' }
                                                    },
                                                    x: {
                                                        ticks: { color: '#9ca3af' },
                                                        grid: { color: 'rgba(55, 65, 81, 0.3)' }
                                                    }
                                                },
                                                plugins: {
                                                    legend: {
                                                        labels: { color: '#e5e7eb', boxWidth: 8, padding: 6 },
                                                    }
                                                }
                                            }}
                                        />
                                    </div>
                                </div>
                            )}
                        </Widget>
                        
                        {/* Active Strategies */}
                        <Widget 
                            title={<span className="flex items-center space-x-2"><IconComponents.SparklesIcon className="w-5 h-5 text-purple-400" /><span>Active Strategies</span></span>}
                        >
                            <div className="space-y-3">
                                {strategies?.map(strategy => (
                                    <div key={strategy.id} className="bg-gray-800/30 p-3 rounded-lg border border-gray-700/50 flex items-center justify-between">
                                        <div>
                                            <div className="flex items-center space-x-2">
                                                <h3 className="font-medium">{strategy.name}</h3>
                                                <Badge 
                                                    type={
                                                        strategy.risk_level === 'low' ? 'success' :
                                                        strategy.risk_level === 'medium' ? 'warning' : 'error'
                                                    }
                                                >
                                                    {strategy.risk_level.toUpperCase()} RISK
                                                </Badge>
                                                {strategy.active && <Badge type="info">ACTIVE</Badge>}
                                            </div>
                                            <div className="text-sm text-gray-400 mt-1">
                                                Success Rate: {strategy.success_rate}% • PnL: <span className={strategy.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                                                    {strategy.pnl >= 0 ? '+' : ''}{strategy.pnl.toFixed(2)} ETH
                                                </span>
                                            </div>
                                        </div>
                                        <div>
                                            <button 
                                                onClick={() => toggleActive(strategy.id)}
                                                className={`px-3 py-1 rounded text-sm font-medium ${
                                                    strategy.active 
                                                        ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' 
                                                        : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                                                }`}
                                            >
                                                {strategy.active ? 'Deactivate' : 'Activate'}
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Widget>
                        
                        {/* ZK Proof Verification */}
                        <Widget 
                            title={<span className="flex items-center space-x-2"><IconComponents.CheckCircleIcon className="w-5 h-5 text-green-400" /><span>ZK Proof Verification</span></span>}
                        >
                            <div className="space-y-2">
                                {zkProofs?.map(proof => (
                                    <div key={proof.id} className="bg-gray-800/30 p-2 rounded-lg border border-gray-700/50 flex items-center justify-between">
                                        <div>
                                            <div className="flex items-center space-x-2">
                                                <span className="text-sm font-medium">{proof.proofType}</span>
                                                <Badge 
                                                    type={
                                                        proof.status === 'Verified' ? 'success' :
                                                        proof.status === 'Verifying' ? 'info' : 'error'
                                                    }
                                                >
                                                    {proof.status.toUpperCase()}
                                                </Badge>
                                            </div>
                                            <div className="text-xs text-gray-400 mt-0.5">
                                                ID: {proof.id} • {proof.status === 'Verifying' ? 'In progress...' : `${proof.verificationTime}ms`}
                                            </div>
                                            {proof.error && (
                                                <div className="text-xs text-red-400 mt-0.5">
                                                    Error: {proof.error}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Widget>
                    </div>
                    
                    {/* Right Column */}
                    <div className="space-y-4">
                        {/* Alerts */}
                        <Widget 
                            title={<span className="flex items-center space-x-2"><IconComponents.ExclamationTriangleIcon className="w-5 h-5 text-yellow-400" /><span>Alerts</span></span>}
                        >
                            {alerts?.length === 0 ? (
                                <div className="text-center py-6 text-gray-400">
                                    <p>No active alerts</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {alerts?.map(alert => (
                                        <div 
                                            key={alert.id} 
                                            className="bg-gray-800/30 p-3 rounded-lg border border-gray-700/50 cursor-pointer hover:bg-gray-800/50 transition-colors"
                                            onClick={() => handleAlertAnalysis(alert)}
                                        >
                                            <div className="flex items-start space-x-2">
                                                <div className="mt-0.5">
                                                    {alert.level === 'critical' ? (
                                                        <IconComponents.XCircleIcon className="w-5 h-5 text-red-400" />
                                                    ) : alert.level === 'warning' ? (
                                                        <IconComponents.ExclamationTriangleIcon className="w-5 h-5 text-yellow-400" />
                                                    ) : (
                                                        <IconComponents.CheckCircleIcon className="w-5 h-5 text-blue-400" />
                                                    )}
                                                </div>
                                                <div>
                                                    <div className="flex items-center space-x-2">
                                                        <Badge 
                                                            type={
                                                                alert.level === 'critical' ? 'error' :
                                                                alert.level === 'warning' ? 'warning' : 'info'
                                                            }
                                                        >
                                                            {alert.level.toUpperCase()}
                                                        </Badge>
                                                        <span className="text-xs text-gray-400">
                                                            {new Date(alert.timestamp).toLocaleTimeString()}
                                                        </span>
                                                    </div>
                                                    <p className="mt-1 text-sm">{alert.message}</p>
                                                    <p className="text-xs text-gray-400 mt-1">{alert.source}</p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </Widget>
                        
                        {/* AI Strategy Insights */}
                        <Widget 
                            title={<span className="flex items-center space-x-2"><IconComponents.SparklesIcon className="w-5 h-5 text-blue-400" /><span>AI Strategy Insights</span></span>}
                        >
                            <div className="bg-gray-800/30 p-3 rounded-lg border border-gray-700/50">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-medium">Latest Opportunity</h3>
                                    <Badge type="info">Confidence: {(aiStrategyData?.confidence * 100).toFixed(0)}%</Badge>
                                </div>
                                <p className="text-sm mb-3">{aiStrategyData?.summary}</p>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div className="bg-gray-800/50 p-2 rounded">
                                        <span className="text-gray-400">Pair:</span>
                                        <div className="font-medium">{aiStrategyData?.details.pair}</div>
                                    </div>
                                    <div className="bg-gray-800/50 p-2 rounded">
                                        <span className="text-gray-400">Potential Profit:</span>
                                        <div className="font-medium text-green-400">+{aiStrategyData?.details.potentialProfit} ETH</div>
                                    </div>
                                    <div className="bg-gray-800/50 p-2 rounded">
                                        <span className="text-gray-400">Required Capital:</span>
                                        <div className="font-medium">${aiStrategyData?.details.requiredCapital.toLocaleString()}</div>
                                    </div>
                                    <div className="bg-gray-800/50 p-2 rounded">
                                        <span className="text-gray-400">Risk Assessment:</span>
                                        <div className="font-medium">{aiStrategyData?.details.risk_assessment}</div>
                                    </div>
                                </div>
                            </div>
                        </Widget>
                        
                        {/* Risk Metrics */}
                        <Widget 
                            title={<span className="flex items-center space-x-2"><IconComponents.ChartBarIcon className="w-5 h-5 text-red-400" /><span>Risk Metrics</span></span>}
                        >
                            <div className="grid grid-cols-2 gap-3">
                                <div className="bg-gray-800/30 p-2 rounded-lg border border-gray-700/50">
                                    <div className="text-xs text-gray-400 mb-1">Value at Risk (99%)</div>
                                    <div className="text-lg font-medium">{riskMetrics?.var}%</div>
                                </div>
                                <div className="bg-gray-800/30 p-2 rounded-lg border border-gray-700/50">
                                    <div className="text-xs text-gray-400 mb-1">Max Drawdown</div>
                                    <div className="text-lg font-medium">{(riskMetrics?.maxDrawdown * 100).toFixed(1)}%</div>
                                </div>
                                <div className="bg-gray-800/30 p-2 rounded-lg border border-gray-700/50">
                                    <div className="text-xs text-gray-400 mb-1">Current Exposure</div>
                                    <div className="text-lg font-medium">${riskMetrics?.exposure.toLocaleString()}</div>
                                </div>
                                <div className="bg-gray-800/30 p-2 rounded-lg border border-gray-700/50">
                                    <div className="text-xs text-gray-400 mb-1">Risk Score</div>
                                    <div className="text-lg font-medium">{riskMetrics?.riskScore}/100</div>
                                </div>
                                <div className="bg-gray-800/30 p-2 rounded-lg border border-gray-700/50">
                                    <div className="text-xs text-gray-400 mb-1">Portfolio Beta</div>
                                    <div className="text-lg font-medium">{riskMetrics?.portfolioBeta}</div>
                                </div>
                                <div className="bg-gray-800/30 p-2 rounded-lg border border-gray-700/50">
                                    <div className="text-xs text-gray-400 mb-1">Sharpe Ratio</div>
                                    <div className="text-lg font-medium">{riskMetrics?.sharpeRatio}</div>
                                </div>
                            </div>
                        </Widget>
                        
                        {/* AI Capabilities */}
                        <Widget 
                            title={<span className="flex items-center space-x-2"><IconComponents.SparklesIcon className="w-5 h-5 text-purple-400" /><span>AI Capabilities</span></span>}
                        >
                            <div className="grid grid-cols-2 gap-2 mb-3">
                                {useArtemisAI().capabilities.slice(0, 6).map(capability => (
                                    <div key={capability.id} className="bg-gray-800/30 p-2 rounded-lg border border-gray-700/50 hover:bg-gray-800/50 transition-colors cursor-pointer">
                                        <h3 className="text-sm font-medium mb-1">{capability.name}</h3>
                                        <p className="text-xs text-gray-400">{capability.description}</p>
                                    </div>
                                ))}
                            </div>
                        </Widget>

                        {/* AI Chat */}
                        <Widget 
                            title={<span className="flex items-center space-x-2"><IconComponents.BoltIcon className="w-5 h-5 text-purple-400" /><span>Artemis AI Assistant</span></span>}
                        >
                            <div className="h-64 overflow-y-auto mb-3 space-y-3 custom-scrollbar">
                                {chatMessages.map(message => (
                                    <div 
                                        key={message.id} 
                                        className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div 
                                            className={`max-w-[85%] rounded-lg p-3 ${
                                                message.sender === 'user' 
                                                    ? 'bg-blue-600/30 border border-blue-500/30' 
                                                    : 'bg-gray-800/50 border border-gray-700/50'
                                            }`}
                                        >
                                            {message.isProcessing ? (
                                                <div className="flex items-center space-x-1">
                                                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                                </div>
                                            ) : (
                                                message.sender === 'user' ? (
                                                    <p className="text-sm">{message.text}</p>
                                                ) : (
                                                    <div className="text-sm">
                                                        <MarkdownRenderer content={message.text} />
                                                    </div>
                                                )
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="flex space-x-2">
                                <input
                                    type="text"
                                    value={chatInput}
                                    onChange={(e) => setChatInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                                    placeholder="Ask Artemis AI anything..."
                                    className="flex-1 bg-gray-800/50 border border-gray-700/50 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                                />
                                <button
                                    onClick={handleSendMessage}
                                    disabled={isThinking || !chatInput.trim()}
                                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 disabled:cursor-not-allowed text-white rounded-lg p-2 transition-colors"
                                >
                                    <IconComponents.PaperAirplaneIcon className="w-5 h-5" />
                                </button>
                            </div>
                        </Widget>
                    </div>
                </div>
            </main>
            
            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-900 border border-gray-700 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="border-b border-gray-700 px-4 py-3 flex items-center justify-between">
                            <h2 className="font-medium">{modalContent.title}</h2>
                            <button 
                                onClick={() => setShowModal(false)}
                                className="text-gray-400 hover:text-white"
                            >
                                <IconComponents.XCircleIcon className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-4">
                            {modalContent.content}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ArtemisAIDashboard;