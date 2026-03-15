import React, { useState, useEffect, useMemo, FC, ReactNode } from 'react';

// --- MOCK ICONS (same as before) ---
const CheckCircleIcon: FC<{ className: string }> = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className={className}><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>;
const XCircleIcon: FC<{ className: string }> = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className={className}><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>;
const ExclamationTriangleIcon: FC<{ className: string }> = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className={className}><path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" /></svg>;
const SparklesIcon: FC<{ className: string }> = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.898 20.572L16.5 21.75l-.398-1.178a3.375 3.375 0 00-2.455-2.456L12.75 18l1.178-.398a3.375 3.375 0 002.455-2.456L16.5 14.25l.398 1.178a3.375 3.375 0 002.456 2.456L20.25 18l-1.178.398a3.375 3.375 0 00-2.456 2.456z" /></svg>;
const PaperAirplaneIcon: FC<{ className: string }> = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}><path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" /></svg>;

// --- Helper Components ---
const Modal: FC<{ show: boolean; onClose: () => void; title: string; children: ReactNode }> = ({ show, onClose, title, children }) => {
    if (!show) return null;
    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center" onClick={onClose}>
            <div className="bg-gray-800 rounded-lg shadow-2xl w-1/2 max-w-2xl border border-gray-700" onClick={(e) => e.stopPropagation()}>
                <div className="flex justify-between items-center p-4 border-b border-gray-700">
                    <h2 className="text-lg font-bold text-white">{title}</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">&times;</button>
                </div>
                <div className="p-6 text-gray-300 max-h-96 overflow-y-auto">{children}</div>
            </div>
        </div>
    );
};

const Spinner: FC<{ size?: 'sm' | 'md' }> = ({ size = 'md' }) => {
    const sizeClass = size === 'sm' ? 'h-5 w-5 border-2' : 'h-8 w-8 border-4';
    return <div className={`animate-spin rounded-full ${sizeClass} border-blue-500 border-t-transparent`}></div>;
};

// --- Enhanced UI Widgets ---
const Widget: FC<{ title: ReactNode; children: ReactNode }> = ({ title, children }) => (
    <div className="bg-gray-800/50 rounded-lg h-full flex flex-col p-1">
        <h3 className="text-md font-bold text-gray-200 p-3 border-b border-gray-700 flex-shrink-0 flex justify-between items-center">{title}</h3>
        <div className="p-3 overflow-y-auto flex-grow">{children}</div>
    </div>
);

const SentinelAlertsWidget: FC<{ alerts: any[], onAnalyze: (alert: any) => void }> = ({ alerts, onAnalyze }) => {
    const levelMap: {[key: string]: string} = { 'critical': 'bg-red-500/20 text-red-400 border-red-500', 'warning': 'bg-yellow-500/20 text-yellow-400 border-yellow-500', 'info': 'bg-blue-500/20 text-blue-400 border-blue-500' };
    return (
        <Widget title="Sentinel Alerts">
            <div className="space-y-2">
                {alerts.map(alert => (
                    <div key={alert.id} className={`p-3 rounded-md border-l-4 ${levelMap[alert.level]}`}>
                        <div className="flex justify-between items-center">
                            <span className="font-semibold">{alert.source}</span>
                            <span className="text-xs text-gray-400">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-sm text-gray-300 mt-1">{alert.message}</p>
                        {alert.level === 'critical' && (
                            <button onClick={() => onAnalyze(alert)} className="mt-2 text-xs flex items-center gap-1 text-blue-400 hover:text-blue-300">
                                <SparklesIcon className="w-4 h-4" /> ✨ Analyze with AI
                            </button>
                        )}
                    </div>
                ))}
            </div>
        </Widget>
    );
};

const StrategyControlWidget: FC<{ strategies: any[], onSuggest: () => void, isSuggesting: boolean }> = ({ strategies, onSuggest, isSuggesting }) => (
     <Widget title={<span>Strategy Control Panel <button onClick={onSuggest} disabled={isSuggesting} className="ml-4 text-xs flex items-center gap-1 text-purple-400 hover:text-purple-300 disabled:opacity-50"><SparklesIcon className="w-4 h-4" /> ✨ Suggest New Strategy</button></span>}>
        <div className="space-y-3">
            {isSuggesting && <div className="flex justify-center p-4"><Spinner /></div>}
            {strategies.map(s => (
                <div key={s.id} className="bg-gray-900/50 p-3 rounded-lg flex items-center justify-between">
                    <div>
                        <p className="font-bold">{s.name}</p>
                        <p className="text-xs text-gray-400">Profit: <span className="text-green-400">{s.pnl} ETH</span></p>
                    </div>
                    <button className={`px-4 py-1 text-sm rounded-md ${s.active ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}`}>{s.active ? 'Deactivate' : 'Activate'}</button>
                </div>
            ))}
        </div>
    </Widget>
);

const ArtemisAI: FC<{ onClose: () => void }> = ({ onClose }) => {
    const [messages, setMessages] = useState<{ text: string, sender: 'user' | 'ai' }[]>([{ text: "Hello! I'm Artemis, your advanced AI trading assistant. I can analyze market conditions, assess risks, suggest strategies, and help with system diagnostics. What would you like to explore?", sender: 'ai' }]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const useGeminiForChat = useGemini(); // Using the enhanced hook

    const handleSend = async () => {
        if (!input.trim()) return;
        const userMessage = { text: input, sender: 'user' as const };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        const aiResponse = await useGeminiForChat.generate('chat', { query: input });
        setMessages(prev => [...prev, { text: aiResponse, sender: 'ai' }]);
        setIsLoading(false);
    };

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center" onClick={onClose}>
            <div className="w-2/3 h-2/3 max-w-4xl bg-gray-800 rounded-lg shadow-2xl flex flex-col border border-gray-700" onClick={(e) => e.stopPropagation()}>
                <div className="flex-shrink-0 flex justify-between items-center p-4 border-b border-gray-700">
                    <h2 className="text-lg font-bold text-white">Artemis AI Core</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">&times;</button>
                </div>
                <div className="flex-grow p-4 overflow-y-auto space-y-4">
                    {messages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-prose p-3 rounded-lg ${msg.sender === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
                                <p className="text-white whitespace-pre-wrap">{msg.text}</p>
                            </div>
                        </div>
                    ))}
                    {isLoading && <div className="flex justify-start"><div className="p-3 rounded-lg bg-gray-700"><Spinner size="sm" /></div></div>}
                </div>
                <div className="flex-shrink-0 p-4 border-t border-gray-700">
                    <div className="flex items-center bg-gray-900 rounded-lg">
                        <input type="text" value={input} onChange={e => setInput(e.target.value)} onKeyPress={e => e.key === 'Enter' && handleSend()} placeholder="Ask Artemis anything..." className="flex-grow bg-transparent p-3 focus:outline-none text-white" />
                        <button onClick={handleSend} disabled={isLoading} className="p-3 text-blue-400 hover:text-blue-300 disabled:opacity-50"><PaperAirplaneIcon className="w-6 h-6"/></button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// --- Other Components (unchanged from previous version) ---
const SystemHealthWidget: FC<{ healthData: any; connectionStatus: string }> = ({ healthData, connectionStatus }) => {
    const statusMap: { [key: string]: { icon: ReactNode, color: string } } = { Operational: { icon: <CheckCircleIcon className="w-5 h-5" />, color: "text-green-400" }, Degraded: { icon: <ExclamationTriangleIcon className="w-5 h-5" />, color: "text-yellow-400" }, Outage: { icon: <XCircleIcon className="w-5 h-5" />, color: "text-red-500" }, };
    const services = healthData ? Object.entries(healthData) : [];
    return ( <Widget title="System Health"><ul className="space-y-3"><li className={`flex items-center justify-between text-sm ${connectionStatus === 'connected' ? 'text-green-400' : 'text-yellow-400'}`}><span>WebSocket</span><div className="flex items-center gap-2"><span>{connectionStatus}</span>{connectionStatus === 'connected' ? <CheckCircleIcon className="w-5 h-5"/> : <ExclamationTriangleIcon className="w-5 h-5"/>}</div></li>{services.map(([service, status]) => { const { icon, color } = statusMap[status as string] || statusMap.Degraded; return ( <li key={service} className={`flex items-center justify-between text-sm ${color}`}><span>{service}</span><div className="flex items-center gap-2"><span>{status as string}</span>{icon}</div></li> ); })}</ul></Widget> ); };
const AIInsightsWidget: FC<{ insights: any }> = ({ insights }) => ( <Widget title="AI Strategy Insights"><div className="bg-gray-900/50 p-4 rounded-lg"><h4 className="font-bold text-green-400">Opportunity Confidence: {(insights.confidence * 100).toFixed(1)}%</h4><p className="text-sm mt-2">{insights.summary}</p><div className="mt-4 text-xs space-y-1"><p><span className="font-semibold">Target Pair:</span> {insights.details.pair}</p><p><span className="font-semibold">Potential Profit:</span> {insights.details.potentialProfit} ETH</p><p><span className="font-semibold">Required Capital:</span> {insights.details.requiredCapital} USDC</p></div></div></Widget> );
const ZKProofsWidget: FC<{ proofs: any[] }> = ({ proofs }) => ( <Widget title="ZK Proof Verification"><table className="w-full text-sm text-left"><thead className="text-xs text-gray-400 uppercase"><tr><th className="py-2">Proof ID</th><th className="py-2">Status</th><th className="py-2 text-right">Time (ms)</th></tr></thead><tbody>{proofs.map(p => (<tr key={p.id} className="border-b border-gray-700"><td className="py-2 font-mono text-cyan-400">{p.id.slice(0,12)}...</td><td className={`py-2 ${p.status === 'Verified' ? 'text-green-400' : 'text-yellow-400'}`}>{p.status}</td><td className="py-2 text-right">{p.verificationTime}</td></tr>))}</tbody></table></Widget> );
const RiskConsoleWidget: FC<{ metrics: any }> = ({ metrics }) => ( <Widget title="Risk Console (from MATLAB RiskEngine.m)"><div className="grid grid-cols-2 gap-4 text-center"><div className="bg-gray-900/50 p-3 rounded-lg"><h4 className="text-sm text-gray-400">Value at Risk (VaR)</h4><p className="text-xl font-bold text-red-400">{metrics.var.toFixed(4)} ETH</p></div><div className="bg-gray-900/50 p-3 rounded-lg"><h4 className="text-sm text-gray-400">Max Drawdown</h4><p className="text-xl font-bold text-yellow-400">{(metrics.maxDrawdown * 100).toFixed(2)}%</p></div><div className="bg-gray-900/50 p-3 rounded-lg col-span-2"><h4 className="text-sm text-gray-400">Overall Exposure</h4><p className="text-xl font-bold text-blue-400">${metrics.exposure.toLocaleString()}</p></div></div></Widget> );
const Header: FC<{ onArtemisToggle: () => void }> = ({ onArtemisToggle }) => ( <header className="flex-shrink-0 h-16 bg-gray-900/80 border-b border-gray-700 flex items-center justify-between px-6"><h1 className="text-xl font-bold text-white">Project Artemis Dashboard</h1><button onClick={onArtemisToggle} className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"> Toggle Artemis AI </button></header> );
const ResizablePanelGroup: FC<{ direction: 'horizontal' | 'vertical'; children: ReactNode, className?: string }> = ({ direction, children, className }) => <div className={`flex ${direction === 'horizontal' ? 'flex-row' : 'flex-col'} ${className}`}>{children}</div>;
const ResizablePanel: FC<{ children: ReactNode, defaultSize: number, minSize: number }> = ({ children, defaultSize }) => <div style={{ flexBasis: `${defaultSize}%` }} className="min-w-[15%] min-h-[15%] p-2">{children}</div>;
const ResizableHandle: FC<{ withHandle?: boolean }> = () => <div className="w-2 bg-gray-800 hover:bg-blue-600 cursor-col-resize rounded-full mx-1" />;
const TabbedPanel: FC<{ tabs: { title: string, content: ReactNode }[] }> = ({ tabs }) => { const [activeTab, setActiveTab] = useState(0); return ( <div className="flex flex-col h-full"><div className="flex-shrink-0 border-b border-gray-700">{tabs.map((tab, index) => ( <button key={tab.title} onClick={() => setActiveTab(index)} className={`py-2 px-4 text-sm font-medium ${activeTab === index ? 'border-b-2 border-blue-500 text-white' : 'text-gray-400 hover:text-white'}`}>{tab.title}</button>))}</div><div className="flex-grow p-1">{tabs[activeTab].content}</div></div> )};
const LoadingScreen: FC<{ message?: string }> = ({ message = "Loading..." }) => ( <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white"><div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-blue-500"></div><p className="mt-8 text-xl text-gray-300">{message}</p></div> );
const ErrorDisplay: FC<{ errors: { name: string; message: string; serviceName?: string }[] }> = ({ errors }) => ( <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white p-8"><div className="bg-red-900/50 border border-red-700 rounded-lg p-6 max-w-2xl w-full shadow-lg"><h1 className="text-3xl font-bold text-red-400 mb-4">Application Error</h1><p className="text-lg text-gray-300 mb-6">One or more critical services failed to load.</p><div className="space-y-4">{errors.map((error, index) => (<div key={index} className="bg-gray-800 p-4 rounded-md border border-gray-700"><h2 className="font-semibold text-red-500">{error.serviceName || 'Unknown Service'}</h2><p className="text-sm text-gray-400 font-mono">{error.message}</p></div>))}</div><button onClick={() => window.location.reload()} className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors">Retry</button></div></div> );
const useCombinedLoadingState = (...hooks: { isLoading: boolean; error: Error | null; serviceName: string }[]) => { const [isTimedOut, setIsTimedOut] = useState(false); useEffect(() => { const timer = setTimeout(() => { if (hooks.some(h => h.isLoading)) setIsTimedOut(true); }, 15000); if (hooks.every(h => !h.isLoading || h.error)) clearTimeout(timer); return () => clearTimeout(timer); }, [hooks]); const isLoading = useMemo(() => hooks.some(h => h.isLoading), [hooks]); let errors = useMemo(() => hooks.filter(h => h.error).map(h => ({ name: h.error!.name, message: h.error!.message, serviceName: h.serviceName })), [hooks]); if (isTimedOut) { const hangingServices = hooks.filter(h => h.isLoading && !h.error).map(h => h.serviceName); if (hangingServices.length > 0) { errors.push({ name: 'TimeoutError', message: `Services did not respond: ${hangingServices.join(', ')}`, serviceName: 'Application Loader' }); } } const overallIsLoading = isLoading && errors.length === 0 && !isTimedOut; return { isLoading: overallIsLoading, errors }; };

// --- ENHANCED AI with Smart Responses (Fixed) ---
const useGemini = () => {
    const generate = async (type: 'analyze_alert' | 'suggest_strategy' | 'chat', context: any): Promise<string> => {
        // Simulate network delay
        await new Promise(res => setTimeout(res, 1800 + Math.random() * 700));

        if (type === 'analyze_alert') {
            const alert = context.alert;
            if (alert.source === 'OracleSentinel' && alert.message.includes('price deviation')) {
                return `**🚨 Critical Oracle Price Deviation Analysis**

**IMMEDIATE THREAT ASSESSMENT: HIGH RISK**

**1. Technical Analysis:**
The ETH/USD oracle has deviated 1.7% from consensus pricing. This exceeds our 1.5% threshold and indicates potential:
- Oracle manipulation attack (likelihood: 15%)
- Exchange-specific flash crash (likelihood: 40%)
- Network congestion causing feed delays (35%)
- Legitimate market volatility spike (10%)

**2. Risk Impact Assessment:**
- **Active Strategies at Risk:** All strategies using ETH/USD pricing
- **Potential Loss Exposure:** $250,000 - $1,200,000 (based on current positions)
- **Liquidation Risk:** MODERATE (if deviation persists >5 minutes)

**3. Immediate Actions Required:**
🔴 **CRITICAL (Execute within 60 seconds):**
- Pause all active arbitrage strategies using ETH/USD
- Halt new position entries on affected pairs
- Switch to backup oracle feeds if available

🟡 **URGENT (Execute within 5 minutes):**
- Cross-verify prices on Coinbase Pro, Binance, Kraken
- Check oracle provider status (Chainlink/Band Protocol)
- Monitor for MEV attacks targeting this deviation

**4. Market Context:**
Current market volatility suggests this could be legitimate price action. However, the speed and magnitude indicate potential manipulation. Our MATLAB risk models show 73% correlation with historical manipulation events.

**5. Recovery Strategy:**
If validation confirms legitimate price movement, gradually re-enable strategies with 2x normal slippage protection. If manipulation detected, maintain defensive posture for 30 minutes post-resolution.

**Confidence Level: 87% (High)**`;
            }
            return `**🔍 Alert Analysis: ${alert.source}**

**Risk Level:** ${alert.level.toUpperCase()}

Based on current market conditions and historical patterns, this ${alert.level} alert requires immediate attention. 

**Recommended Actions:**
1. Evaluate exposure to related trading pairs/protocols
2. Increase surveillance on correlated metrics
3. ${alert.level === 'critical' ? 'Execute emergency protocols immediately' : 'Monitor and prepare contingency plans'}

**Impact Assessment:** ${alert.level === 'critical' ? 'High - immediate intervention needed' : 'Medium - close monitoring advised'}`;
        }
        
        if (type === 'suggest_strategy') {
            const strategies = [
                `**⚡ Cross-DEX Arbitrage with ZK Privacy**

**Market Opportunity:**
Current analysis shows persistent price discrepancies between Uniswap V3, SushiSwap, and Balancer for WETH/USDC pairs. Average spread: 0.15-0.23%.

**Strategy Mechanics:**
1. **Detection Phase:** Monitor price feeds across 5 major DEXs every 100ms
2. **Execution Phase:** Deploy flash loans for capital-efficient arbitrage
3. **Privacy Phase:** Use ZK proofs to obscure transaction patterns from MEV bots

**Capital Requirements:** 50-500 ETH (auto-scaling based on opportunity size)

**Risk Metrics:**
- **Expected Annual Return:** 23-31%
- **Maximum Drawdown:** 3.2%
- **Sharpe Ratio:** 2.7
- **Win Rate:** 89%

**Current Signal:** Model predicting 4-hour window of optimal conditions with 91% confidence.`,

                `**🧠 Volatility Arbitrage with ML Prediction**

**Core Concept:**
Exploit volatility mispricings between implied (options) and realized volatility using machine learning predictions.

**Algorithm Overview:**
- LSTM model predicts 1-hour realized volatility
- Trade when model confidence >85% and expected edge >0.3%
- Auto-hedging for delta-neutral positions

**Performance Metrics (Backtested):**
- **6-month Return:** +47.3%
- **Volatility:** 8.9% (low risk)
- **Profit Factor:** 2.4

**Current Signal:** Model predicting volatility increase with 91% confidence.`
            ];
            return strategies[Math.floor(Math.random() * strategies.length)];
        }
        
        if (type === 'chat') {
            const input = context.query.toLowerCase();
            
            if (input.includes('oracle') || input.includes('price')) {
                return `**Oracle & Price Analysis:**

I'm monitoring multiple oracle feeds and detect concerning patterns:

🔴 **Current Issues:**
- ETH/USD oracle showing 1.7% deviation from spot markets
- MATLAB bridge degraded (affecting risk calculations)
- Higher than normal MEV activity

**Recommendations:**
1. **Immediate:** Reduce position sizes by 30% until oracle stability improves
2. **Medium-term:** Implement multi-oracle validation
3. **Monitor:** Watch for correlation between oracle deviations and network congestion

The degraded MATLAB bridge is particularly concerning as it affects our risk calculations. I suggest switching to backup risk models until restored.

Would you like me to run a deeper analysis on any specific trading pair?`;
            }
            
            if (input.includes('risk') || input.includes('matlab')) {
                return `**System Health & MATLAB Integration Status:**

🟡 **System Status Update:**
The MATLAB bridge degradation is affecting our advanced risk calculations.

**Affected Components:**
- Risk Engine calculations (using backup models)
- Predictive analytics (reduced accuracy)  
- Portfolio optimization (simplified algorithms)

**Current Workarounds:**
- Switched to Python-based risk models (90% accuracy vs 97% for MATLAB)
- Reduced position sizes by 15% to compensate
- Increased monitoring frequency

**Estimated Impact:**
- Strategy performance reduction: 5-8%
- Risk calculation error margin: +0.3%
- Daily profit impact: ~0.2-0.4 ETH

DevOps team estimates 2-4 hours for full restoration. Until then, I recommend conservative position sizing and avoiding complex multi-leg strategies.`;
            }
            
            return `I understand you're asking about "${context.query}". 

**Current System Context:**
- System operating at 87% capacity (MATLAB bridge issue)
- Market volatility: MEDIUM (good for arbitrage)
- Gas costs: NORMAL (strategies profitable)
- Active alerts: 1 critical, 1 warning

**My Analysis:**
Based on current conditions, I can provide insights on risk analysis, portfolio optimization, market opportunities, and system diagnostics.

I can help with:
🔍 Risk analysis and portfolio optimization
📊 Strategy performance evaluation  
⚡ Real-time market opportunity identification
🛡️ System health monitoring and diagnostics

What specific aspect would you like me to focus on?`;
        }
        return "I'm here to help with trading analysis and system monitoring.";
    };
    return { generate };
};

// --- Mock Data Hooks (with enhanced data) ---
const useMockHook = (dataFactory: () => any, delay: number, shouldError: boolean, serviceName: string) => { 
    const [state, setState] = useState({ data: null, isLoading: true, error: null as Error | null }); 
    useEffect(() => { 
        const timer = setTimeout(() => { 
            if (shouldError) setState({ data: null, isLoading: false, error: new Error(`Failed to fetch from ${serviceName}.`) }); 
            else setState({ data: dataFactory(), isLoading: false, error: null }); 
        }, delay); 
        return () => clearTimeout(timer); 
    }, []); 
    return state; 
};

const useSystemHealth = () => useMockHook(() => ({ 'Node.js Backend': 'Operational', 'Postgres DB': 'Operational', 'Python AI Agent': 'Operational', 'MATLAB Bridge': 'Degraded', 'Blockchain Node': 'Operational' }), 800, false, 'System Health');
const useSentinelAlerts = () => useMockHook(() => ([ { id: 1, source: 'OracleSentinel', message: 'ETH/USD price deviation detected: 1.7% above consensus', level: 'critical', timestamp: Date.now() - 45000 }, { id: 2, source: 'MEVSentinel', message: 'Large sandwich opportunity: $547K USDC swap detected', level: 'warning', timestamp: Date.now() - 180000 }, { id: 3, source: 'GasSentinel', message: 'Gas price spike detected: 89 gwei (normal: 27 gwei)', level: 'info', timestamp: Date.now() - 420000 } ]), 1200, false, 'Sentinel Alerts');
const useAIStrategyData = () => useMockHook(() => ({ confidence: 0.87, summary: 'High-confidence triangular arbitrage opportunity detected across Uniswap V3, SushiSwap, and Balancer. Current market conditions favor execution.', details: { pair: 'USDC/WETH/WBTC', potentialProfit: 1.23, requiredCapital: 180000 } }), 1500, false, 'AI Strategy Data');
const useZKProofData = () => useMockHook(() => ([{id: 'zk-a4b8c1', status: 'Verified', verificationTime: 187}, {id: 'zk-d9e2f7', status: 'Verifying', verificationTime: -1}, {id: 'zk-g5h1i3', status: 'Verified', verificationTime: 143}]), 1800, false, 'ZK Proofs Service');
const useRiskMetrics = () => useMockHook(() => ({ var: 12.54, maxDrawdown: 0.152, exposure: 1247800 }), 1400, false, 'Risk Metrics');
const useStrategies = () => useMockHook(() => ([{id: 1, name: 'Tri-Arbitrage V2', pnl: 14.23, active: true}, {id: 2, name: 'Flash-Mint Hedge', pnl: 5.12, active: false}, {id: 3, name: 'MEV Backrun', pnl: 8.87, active: true}]), 1600, false, 'Strategies');
const useAppConfig = () => ({ apiBaseUrl: '/api', webSocketUrl: 'ws://localhost:8080' });
const useWebSocket = (url: string) => { const [connectionStatus, setConnectionStatus] = useState('connecting'); useEffect(() => { const timer = setTimeout(() => setConnectionStatus('connected'), 1200); return () => clearTimeout(timer); }, [url]); return { connectionStatus }; };

// --- Main Dashboard Component ---
const SmartUnifiedDashboard: React.FC = () => {
    const [isArtemisOpen, setIsArtemisOpen] = useState(false);
    const [modalState, setModalState] = useState<{ show: boolean; title: string; content: string | ReactNode }>({ show: false, title: '', content: '' });
    const [isSuggesting, setIsSuggesting] = useState(false);
    const gemini = useGemini();

    const handleAnalyzeAlert = async (alert: any) => {
        setModalState({ show: true, title: `🤖 AI Analysis: ${alert.source}`, content: <div className="flex justify-center p-8"><Spinner /></div> });
        const analysis = await gemini.generate('analyze_alert', { alert });
        setModalState({ show: true, title: `🤖 AI Analysis: ${alert.source}`, content: <div className="whitespace-pre-wrap">{analysis}</div> });
    };

    const handleSuggestStrategy = async () => {
        setIsSuggesting(true);
        const suggestion = await gemini.generate('suggest_strategy', {});
        setModalState({ show: true, title: "✨ AI Strategy Suggestion", content: <div className="whitespace-pre-wrap">{suggestion}</div> });
        setIsSuggesting(false);
    };

    // Data fetching hooks
    const config = useAppConfig();
    const systemHealth = useSystemHealth();
    const alerts = useSentinelAlerts();
    const aiData = useAIStrategyData();
    const zkData = useZKProofData();
    const riskMetrics = useRiskMetrics();
    const strategies = useStrategies();
    const { connectionStatus } = useWebSocket(config.webSocketUrl);

    const { isLoading, errors } = useCombinedLoadingState(
        { ...systemHealth, serviceName: 'System Health' },
        { isLoading: connectionStatus !== 'connected', error: null, serviceName: 'WebSocket' },
        { ...alerts, serviceName: 'Sentinel Alerts' },
        { ...aiData, serviceName: 'AI Strategies' },
        { ...zkData, serviceName: 'ZK Proofs' },
        { ...riskMetrics, serviceName: 'Risk Metrics' },
        { ...strategies, serviceName: 'Strategies' }
    );

    if (isLoading) return <LoadingScreen message="Calibrating Artemis AI Core... Loading all system modules..." />;
    if (errors.length > 0) return <ErrorDisplay errors={errors} />;

    return (
        <div className="flex h-screen w-screen flex-col bg-gray-900 text-gray-100 font-sans overflow-hidden">
            <Header onArtemisToggle={() => setIsArtemisOpen(!isArtemisOpen)} />
            
            <main className="flex-grow p-2">
                <ResizablePanelGroup direction="horizontal" className="h-full w-full">
                    <ResizablePanel defaultSize={20} minSize={15}>
                        <SystemHealthWidget healthData={systemHealth.data} connectionStatus={connectionStatus}/>
                    </ResizablePanel>
                    <ResizableHandle />
                    <ResizablePanel defaultSize={55} minSize={30}>
                        <TabbedPanel tabs={[
                            { title: 'Sentinel Alerts', content: <SentinelAlertsWidget alerts={alerts.data!} onAnalyze={handleAnalyzeAlert} /> },
                            { title: 'AI Insights', content: <AIInsightsWidget insights={aiData.data!} /> },
                            { title: 'Risk Console', content: <RiskConsoleWidget metrics={riskMetrics.data!} /> },
                        ]}/>
                    </ResizablePanel>
                    <ResizableHandle />
                    <ResizablePanel defaultSize={25} minSize={15}>
                        <div className="flex flex-col h-full gap-4">
                            <div className="flex-1"><StrategyControlWidget strategies={strategies.data!} onSuggest={handleSuggestStrategy} isSuggesting={isSuggesting} /></div>
                            <div className="flex-1"><ZKProofsWidget proofs={zkData.data!} /></div>
                        </div>
                    </ResizablePanel>
                </ResizablePanelGroup>
            </main>

            {isArtemisOpen && <ArtemisAI onClose={() => setIsArtemisOpen(false)} />}
            <Modal show={modalState.show} onClose={() => setModalState({ ...modalState, show: false })} title={modalState.title}>
                {modalState.content}
            </Modal>
        </div>
    );
};

export default SmartUnifiedDashboard;
