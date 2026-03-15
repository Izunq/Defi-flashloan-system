import React, { useState, useEffect, useMemo, FC, ReactNode, memo, useCallback } from 'react';
import { IconComponents } from './icons/IconComponents';
import { useGeminiAI } from '../hooks/useGeminiAI';
import { useCombinedLoadingState } from '../hooks/useCombinedLoadingState';
import { useSystemHealth, useSentinelAlerts, useAIStrategyData, useZKProofData, useRiskMetrics, useStrategies, useAppConfig, useWebSocket } from '../hooks/dataHooks';

// Type definitions
interface Alert {
  id: number;
  source: string;
  message: string;
  level: 'critical' | 'warning' | 'info';
  timestamp: number;
  metadata?: {
    pair?: string;
    deviation?: number;
    threshold?: number;
    exchanges?: string[];
  };
}

interface Strategy {
  id: number;
  name: string;
  pnl: number;
  active: boolean;
  risk_level: 'low' | 'medium' | 'high';
  last_executed?: number;
  success_rate?: number;
}

interface SystemHealth {
  [service: string]: 'Operational' | 'Degraded' | 'Outage';
}

interface AIInsight {
  confidence: number;
  summary: string;
  details: {
    pair: string;
    potentialProfit: number;
    requiredCapital: number;
    risk_assessment: string;
    market_conditions: string;
  };
}

// --- Helper Components ---
const Modal: FC<{ 
  show: boolean; 
  onClose: () => void; 
  title: string; 
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}> = memo(({ show, onClose, title, children, size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-1/3 max-w-md',
    md: 'w-1/2 max-w-2xl',
    lg: 'w-2/3 max-w-4xl',
    xl: 'w-5/6 max-w-6xl'
  };

  if (!show) return null;
  
  return (
    <div 
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center" 
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div 
        className={`bg-gray-800 rounded-lg shadow-2xl ${sizeClasses[size]} border border-gray-700`} 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center p-4 border-b border-gray-700">
          <h2 id="modal-title" className="text-lg font-bold text-white">{title}</h2>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-white text-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            aria-label="Close modal"
          >
            &times;
          </button>
        </div>
        <div className="p-6 text-gray-300 max-h-96 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
});

const Spinner: FC<{ size?: 'sm' | 'md' | 'lg' }> = memo(({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'h-5 w-5 border-2',
    md: 'h-8 w-8 border-4',
    lg: 'h-12 w-12 border-4'
  };
  return (
    <div 
      className={`animate-spin rounded-full ${sizeClasses[size]} border-blue-500 border-t-transparent`}
      role="status"
      aria-label="Loading"
    />
  );
});

// --- Enhanced Widget Components ---
const Widget: FC<{ title: ReactNode; children: ReactNode; className?: string }> = memo(({ title, children, className = '' }) => (
  <div className={`bg-gray-800/50 rounded-lg h-full flex flex-col p-1 ${className}`}>
    <h3 className="text-md font-bold text-gray-200 p-3 border-b border-gray-700 flex-shrink-0 flex justify-between items-center">
      {title}
    </h3>
    <div className="p-3 overflow-y-auto flex-grow">{children}</div>
  </div>
));

const SentinelAlertsWidget: FC<{ 
  alerts: Alert[]; 
  onAnalyze: (alert: Alert) => void;
  onDismiss?: (alertId: number) => void;
}> = memo(({ alerts, onAnalyze, onDismiss }) => {
  const levelMap: {[key: string]: string} = { 
    'critical': 'bg-red-500/20 text-red-400 border-red-500', 
    'warning': 'bg-yellow-500/20 text-yellow-400 border-yellow-500', 
    'info': 'bg-blue-500/20 text-blue-400 border-blue-500' 
  };

  const sortedAlerts = useMemo(() => 
    [...alerts].sort((a, b) => {
      const priorityMap = { critical: 3, warning: 2, info: 1 };
      return priorityMap[b.level] - priorityMap[a.level] || b.timestamp - a.timestamp;
    }), [alerts]
  );

  return (
    <Widget title={
      <span className="flex items-center gap-2">
        Sentinel Alerts
        <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
          {alerts.filter(a => a.level === 'critical').length}
        </span>
      </span>
    }>
      <div className="space-y-2">
        {sortedAlerts.map(alert => (
          <div key={alert.id} className={`p-3 rounded-md border-l-4 ${levelMap[alert.level]} transition-all hover:bg-gray-700/30`}>
            <div className="flex justify-between items-start">
              <div className="flex-grow">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-semibold text-sm">{alert.source}</span>
                  <span className="text-xs text-gray-400">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-sm text-gray-300">{alert.message}</p>
                {alert.metadata && (
                  <div className="mt-2 text-xs text-gray-400 space-y-1">
                    {alert.metadata.pair && <div>Pair: {alert.metadata.pair}</div>}
                    {alert.metadata.deviation && <div>Deviation: {alert.metadata.deviation}%</div>}
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-1 ml-2">
                <button 
                  onClick={() => onAnalyze(alert)} 
                  className="text-xs flex items-center gap-1 text-blue-400 hover:text-blue-300 px-2 py-1 rounded hover:bg-blue-500/10"
                  aria-label={`Analyze alert ${alert.id}`}
                >
                  <IconComponents.SparklesIcon className="w-3 h-3" /> AI Analyze
                </button>
                {onDismiss && (
                  <button 
                    onClick={() => onDismiss(alert.id)} 
                    className="text-xs text-gray-500 hover:text-gray-400 px-2 py-1 rounded hover:bg-gray-600/20"
                    aria-label={`Dismiss alert ${alert.id}`}
                  >
                    Dismiss
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Widget>
  );
});

const StrategyControlWidget: FC<{ 
  strategies: Strategy[]; 
  onSuggest: () => void; 
  isSuggesting: boolean;
  onToggleStrategy?: (id: number) => void;
}> = memo(({ strategies, onSuggest, isSuggesting, onToggleStrategy }) => {
  const activeStrategies = strategies.filter(s => s.active);
  const totalPnL = strategies.reduce((sum, s) => sum + s.pnl, 0);

  return (
    <Widget title={
      <div className="flex justify-between items-center w-full">
        <span>Strategy Control Panel</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">
            {activeStrategies.length}/{strategies.length} Active
          </span>
          <button 
            onClick={onSuggest} 
            disabled={isSuggesting} 
            className="text-xs flex items-center gap-1 text-purple-400 hover:text-purple-300 disabled:opacity-50 px-2 py-1 rounded hover:bg-purple-500/10"
          >
            <IconComponents.SparklesIcon className="w-4 h-4" /> 
            {isSuggesting ? 'Generating...' : 'AI Suggest'}
          </button>
        </div>
      </div>
    }>
      <div className="space-y-3">
        <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700">
          <div className="text-center">
            <p className="text-xs text-gray-400">Total P&L</p>
            <p className={`text-lg font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)} ETH
            </p>
          </div>
        </div>
        
        {isSuggesting && (
          <div className="flex justify-center p-4">
            <Spinner />
          </div>
        )}
        
        {strategies.map(strategy => (
          <div key={strategy.id} className="bg-gray-900/50 p-3 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex-grow">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-bold text-sm">{strategy.name}</p>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    strategy.risk_level === 'high' ? 'bg-red-500/20 text-red-400' :
                    strategy.risk_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-green-500/20 text-green-400'
                  }`}>
                    {strategy.risk_level}
                  </span>
                </div>
                <div className="flex justify-between text-xs text-gray-400">
                  <span>P&L: <span className={strategy.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                    {strategy.pnl >= 0 ? '+' : ''}{strategy.pnl} ETH
                  </span></span>
                  {strategy.success_rate && (
                    <span>Success: {(strategy.success_rate * 100).toFixed(1)}%</span>
                  )}
                </div>
              </div>
              <button 
                onClick={() => onToggleStrategy?.(strategy.id)}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  strategy.active 
                    ? 'bg-red-600 hover:bg-red-700 text-white' 
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {strategy.active ? 'Stop' : 'Start'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </Widget>
  );
});

const ArtemisAI: FC<{ onClose: () => void }> = memo(({ onClose }) => {
  const [messages, setMessages] = useState<{ text: string, sender: 'user' | 'ai', timestamp: number }[]>([
    { 
      text: "Hello! I'm Artemis, your advanced AI trading assistant. I can analyze market conditions, assess risks, suggest strategies, and help with system diagnostics. What would you like to explore?", 
      sender: 'ai',
      timestamp: Date.now()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const gemini = useGeminiAI();

  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage = { text: input, sender: 'user' as const, timestamp: Date.now() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      const aiResponse = await gemini.generateChatResponse(input, messages);
      setMessages(prev => [...prev, { text: aiResponse, sender: 'ai', timestamp: Date.now() }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        text: "I apologize, but I encountered an error processing your request. Please try again.", 
        sender: 'ai', 
        timestamp: Date.now() 
      }]);
    }
    
    setIsLoading(false);
  }, [input, isLoading, gemini, messages]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center" onClick={onClose}>
      <div className="w-4/5 h-4/5 max-w-6xl bg-gray-800 rounded-lg shadow-2xl flex flex-col border border-gray-700" onClick={(e) => e.stopPropagation()}>
        <div className="flex-shrink-0 flex justify-between items-center p-4 border-b border-gray-700">
          <div>
            <h2 className="text-lg font-bold text-white">Artemis AI Core</h2>
            <p className="text-xs text-gray-400">Advanced Trading & Risk Analysis Assistant</p>
          </div>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-white text-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            aria-label="Close Artemis AI"
          >
            &times;
          </button>
        </div>
        
        <div className="flex-grow p-4 overflow-y-auto space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-prose p-3 rounded-lg ${
                msg.sender === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-100'
              }`}>
                <p className="whitespace-pre-wrap">{msg.text}</p>
                <p className="text-xs opacity-70 mt-1">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="p-3 rounded-lg bg-gray-700 flex items-center gap-2">
                <Spinner size="sm" />
                <span className="text-gray-300 text-sm">Artemis is thinking...</span>
              </div>
            </div>
          )}
        </div>
        
        <div className="flex-shrink-0 p-4 border-t border-gray-700">
          <div className="flex items-center bg-gray-900 rounded-lg">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask about market conditions, risk analysis, strategy optimization..."
              className="flex-grow bg-transparent p-3 focus:outline-none text-white resize-none"
              rows={1}
              disabled={isLoading}
            />
            <button 
              onClick={handleSend} 
              disabled={isLoading || !input.trim()}
              className="p-3 text-blue-400 hover:text-blue-300 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              aria-label="Send message"
            >
              <IconComponents.PaperAirplaneIcon className="w-6 h-6"/>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

// Additional widgets remain the same but with memo wrapper...
const SystemHealthWidget: FC<{ healthData: SystemHealth; connectionStatus: string }> = memo(({ healthData, connectionStatus }) => {
  const statusMap: { [key: string]: { icon: ReactNode, color: string } } = { 
    Operational: { icon: <IconComponents.CheckCircleIcon className="w-5 h-5" />, color: "text-green-400" }, 
    Degraded: { icon: <IconComponents.ExclamationTriangleIcon className="w-5 h-5" />, color: "text-yellow-400" }, 
    Outage: { icon: <IconComponents.XCircleIcon className="w-5 h-5" />, color: "text-red-500" }
  };
  
  const services = healthData ? Object.entries(healthData) : [];
  const degradedServices = services.filter(([_, status]) => status === 'Degraded').length;
  const outageServices = services.filter(([_, status]) => status === 'Outage').length;
  
  return (
    <Widget title={
      <div className="flex items-center gap-2">
        System Health
        {(degradedServices > 0 || outageServices > 0) && (
          <span className="bg-yellow-500 text-black text-xs px-2 py-1 rounded-full">
            {degradedServices + outageServices} Issues
          </span>
        )}
      </div>
    }>
      <ul className="space-y-3">
        <li className={`flex items-center justify-between text-sm ${
          connectionStatus === 'connected' ? 'text-green-400' : 'text-yellow-400'
        }`}>
          <span>WebSocket Connection</span>
          <div className="flex items-center gap-2">
            <span className="capitalize">{connectionStatus}</span>
            {connectionStatus === 'connected' ? 
              <IconComponents.CheckCircleIcon className="w-5 h-5"/> : 
              <IconComponents.ExclamationTriangleIcon className="w-5 h-5"/>
            }
          </div>
        </li>
        {services.map(([service, status]) => {
          const { icon, color } = statusMap[status as string] || statusMap.Degraded;
          return (
            <li key={service} className={`flex items-center justify-between text-sm ${color}`}>
              <span>{service}</span>
              <div className="flex items-center gap-2">
                <span>{status as string}</span>
                {icon}
              </div>
            </li>
          );
        })}
      </ul>
    </Widget>
  );
});

// Continue with other widgets...
const AIInsightsWidget: FC<{ insights: AIInsight }> = memo(({ insights }) => (
  <Widget title="AI Strategy Insights">
    <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-bold text-green-400">
          Opportunity Confidence: {(insights.confidence * 100).toFixed(1)}%
        </h4>
        <div className={`w-3 h-3 rounded-full ${
          insights.confidence > 0.8 ? 'bg-green-500' :
          insights.confidence > 0.6 ? 'bg-yellow-500' : 'bg-red-500'
        }`} />
      </div>
      <p className="text-sm mb-4">{insights.summary}</p>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="space-y-1">
          <p><span className="font-semibold text-gray-400">Target Pair:</span> {insights.details.pair}</p>
          <p><span className="font-semibold text-gray-400">Potential Profit:</span> <span className="text-green-400">{insights.details.potentialProfit} ETH</span></p>
        </div>
        <div className="space-y-1">
          <p><span className="font-semibold text-gray-400">Required Capital:</span> {insights.details.requiredCapital.toLocaleString()} USDC</p>
          <p><span className="font-semibold text-gray-400">Risk Level:</span> <span className={
            insights.details.risk_assessment === 'Low' ? 'text-green-400' :
            insights.details.risk_assessment === 'Medium' ? 'text-yellow-400' : 'text-red-400'
          }>{insights.details.risk_assessment}</span></p>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-gray-700">
        <p className="text-xs text-gray-400">
          <span className="font-semibold">Market Conditions:</span> {insights.details.market_conditions}
        </p>
      </div>
    </div>
  </Widget>
));

// Export the enhanced dashboard
const EnhancedUnifiedDashboard: React.FC = () => {
  const [isArtemisOpen, setIsArtemisOpen] = useState(false);
  const [modalState, setModalState] = useState<{ show: boolean; title: string; content: string | ReactNode }>({ 
    show: false, 
    title: '', 
    content: '' 
  });
  const [isSuggesting, setIsSuggesting] = useState(false);
  const gemini = useGeminiAI();

  const handleAnalyzeAlert = useCallback(async (alert: Alert) => {
    setModalState({ 
      show: true, 
      title: `🤖 AI Analysis: ${alert.source}`, 
      content: <div className="flex justify-center p-8"><Spinner /></div> 
    });
    
    try {
      const analysis = await gemini.analyzeAlert(alert);
      setModalState({ 
        show: true, 
        title: `🤖 AI Analysis: ${alert.source}`, 
        content: <div className="whitespace-pre-wrap">{analysis}</div> 
      });
    } catch (error) {
      setModalState({ 
        show: true, 
        title: `❌ Analysis Error`, 
        content: <div>Sorry, I couldn't analyze this alert. Please try again later.</div> 
      });
    }
  }, [gemini]);

  const handleSuggestStrategy = useCallback(async () => {
    setIsSuggesting(true);
    try {
      const suggestion = await gemini.suggestStrategy();
      setModalState({ 
        show: true, 
        title: "✨ AI Strategy Suggestion", 
        content: <div className="whitespace-pre-wrap">{suggestion}</div> 
      });
    } catch (error) {
      setModalState({ 
        show: true, 
        title: "❌ Strategy Error", 
        content: <div>Sorry, I couldn't generate a strategy suggestion. Please try again later.</div> 
      });
    }
    setIsSuggesting(false);
  }, [gemini]);

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
            <SystemHealthWidget healthData={systemHealth.data!} connectionStatus={connectionStatus}/>
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
              <div className="flex-1">
                <StrategyControlWidget 
                  strategies={strategies.data!} 
                  onSuggest={handleSuggestStrategy} 
                  isSuggesting={isSuggesting} 
                />
              </div>
              <div className="flex-1">
                <ZKProofsWidget proofs={zkData.data!} />
              </div>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </main>

      {isArtemisOpen && <ArtemisAI onClose={() => setIsArtemisOpen(false)} />}
      <Modal 
        show={modalState.show} 
        onClose={() => setModalState({ ...modalState, show: false })} 
        title={modalState.title}
        size="lg"
      >
        {modalState.content}
      </Modal>
    </div>
  );
};

// Additional required components
const ZKProofsWidget: FC<{ proofs: any[] }> = memo(({ proofs }) => (
  <Widget title={
    <div className="flex items-center gap-2">
      ZK Proof Verification
      <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
        {proofs.filter(p => p.status === 'Verified').length}/{proofs.length}
      </span>
    </div>
  }>
    <div className="space-y-2">
      {proofs.map(proof => (
        <div key={proof.id} className={`p-3 rounded-lg border ${
          proof.status === 'Verified' ? 'border-green-500/30 bg-green-500/10' :
          proof.status === 'Verifying' ? 'border-yellow-500/30 bg-yellow-500/10' :
          'border-red-500/30 bg-red-500/10'
        }`}>
          <div className="flex justify-between items-center mb-1">
            <span className="font-mono text-sm text-cyan-400">{proof.id.slice(0, 16)}...</span>
            <span className={`text-xs px-2 py-1 rounded-full ${
              proof.status === 'Verified' ? 'bg-green-500 text-white' :
              proof.status === 'Verifying' ? 'bg-yellow-500 text-black' :
              'bg-red-500 text-white'
            }`}>
              {proof.status}
            </span>
          </div>
          <div className="flex justify-between items-center text-xs text-gray-400">
            <span>{proof.proofType}</span>
            {proof.verificationTime > 0 && (
              <span>{proof.verificationTime}ms</span>
            )}
          </div>
          {proof.error && (
            <p className="text-xs text-red-400 mt-1">Error: {proof.error}</p>
          )}
        </div>
      ))}
    </div>
  </Widget>
));

const RiskConsoleWidget: FC<{ metrics: any }> = memo(({ metrics }) => (
  <Widget title="Risk Console">
    <div className="grid grid-cols-2 gap-3 mb-4">
      <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700">
        <h4 className="text-xs text-gray-400 mb-1">Value at Risk (24h)</h4>
        <p className="text-lg font-bold text-red-400">{metrics.var.toFixed(2)} ETH</p>
        <p className="text-xs text-gray-500">~${(metrics.var * 2000).toLocaleString()}</p>
      </div>
      <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700">
        <h4 className="text-xs text-gray-400 mb-1">Max Drawdown</h4>
        <p className="text-lg font-bold text-yellow-400">{(metrics.maxDrawdown * 100).toFixed(1)}%</p>
        <p className="text-xs text-gray-500">Risk Score: {metrics.riskScore}/100</p>
      </div>
    </div>
    <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700">
      <h4 className="text-xs text-gray-400 mb-2">Portfolio Exposure</h4>
      <p className="text-xl font-bold text-blue-400">${metrics.exposure.toLocaleString()}</p>
      <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
        <div>
          <span className="text-gray-400">Leverage:</span>
          <span className="text-white ml-1">{metrics.leverage}x</span>
        </div>
        <div>
          <span className="text-gray-400">Sharpe:</span>
          <span className="text-green-400 ml-1">{metrics.sharpeRatio}</span>
        </div>
        <div>
          <span className="text-gray-400">Beta:</span>
          <span className="text-blue-400 ml-1">{metrics.portfolioBeta}</span>
        </div>
      </div>
    </div>
  </Widget>
));

// Enhanced Header component
const Header: FC<{ onArtemisToggle: () => void }> = memo(({ onArtemisToggle }) => (
  <header className="flex-shrink-0 h-16 bg-gray-900/80 border-b border-gray-700 flex items-center justify-between px-6">
    <div className="flex items-center gap-4">
      <h1 className="text-xl font-bold text-white">Artemis Trading Platform</h1>
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
        <span>Live Trading Active</span>
      </div>
    </div>
    <div className="flex items-center gap-4">
      <div className="text-right text-sm">
        <p className="text-white font-semibold">Portfolio: +28.2 ETH</p>
        <p className="text-green-400 text-xs">+$56,400 (24h)</p>
      </div>
      <button 
        onClick={onArtemisToggle} 
        className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-all duration-200 flex items-center gap-2"
      >
        <IconComponents.SparklesIcon className="w-5 h-5" />
        Artemis AI
      </button>
    </div>
  </header>
));

// Resizable components (simplified for demo)
const ResizablePanelGroup: FC<{ direction: 'horizontal' | 'vertical'; children: ReactNode; className?: string }> = 
  memo(({ direction, children, className }) => (
    <div className={`flex ${direction === 'horizontal' ? 'flex-row' : 'flex-col'} ${className}`}>
      {children}
    </div>
  ));

const ResizablePanel: FC<{ children: ReactNode; defaultSize: number; minSize: number }> = 
  memo(({ children, defaultSize }) => (
    <div style={{ flexBasis: `${defaultSize}%` }} className="min-w-[15%] min-h-[15%] p-2">
      {children}
    </div>
  ));

const ResizableHandle: FC<{ withHandle?: boolean }> = memo(() => (
  <div className="w-2 bg-gray-800 hover:bg-blue-600 cursor-col-resize rounded-full mx-1 transition-colors" />
));

const TabbedPanel: FC<{ tabs: { title: string; content: ReactNode }[] }> = memo(({ tabs }) => {
  const [activeTab, setActiveTab] = useState(0);
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex-shrink-0 border-b border-gray-700">
        {tabs.map((tab, index) => (
          <button
            key={tab.title}
            onClick={() => setActiveTab(index)}
            className={`py-2 px-4 text-sm font-medium transition-colors ${
              activeTab === index 
                ? 'border-b-2 border-blue-500 text-white bg-gray-800/50' 
                : 'text-gray-400 hover:text-white hover:bg-gray-800/30'
            }`}
          >
            {tab.title}
          </button>
        ))}
      </div>
      <div className="flex-grow p-1">
        {tabs[activeTab].content}
      </div>
    </div>
  );
});

const LoadingScreen: FC<{ message?: string }> = memo(({ message = "Loading..." }) => (
  <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
    <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-blue-500"></div>
    <p className="mt-8 text-xl text-gray-300">{message}</p>
    <p className="mt-2 text-sm text-gray-500">Initializing Artemis AI Core systems...</p>
  </div>
));

const ErrorDisplay: FC<{ errors: { name: string; message: string; serviceName?: string }[] }> = memo(({ errors }) => (
  <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white p-8">
    <div className="bg-red-900/50 border border-red-700 rounded-lg p-6 max-w-2xl w-full shadow-lg">
      <h1 className="text-3xl font-bold text-red-400 mb-4">System Error</h1>
      <p className="text-lg text-gray-300 mb-6">Critical services failed to initialize:</p>
      <div className="space-y-4">
        {errors.map((error, index) => (
          <div key={index} className="bg-gray-800 p-4 rounded-md border border-gray-700">
            <h2 className="font-semibold text-red-500">{error.serviceName || 'Unknown Service'}</h2>
            <p className="text-sm text-gray-400 font-mono">{error.message}</p>
          </div>
        ))}
      </div>
      <button 
        onClick={() => window.location.reload()} 
        className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors"
      >
        Retry System Initialization
      </button>
    </div>
  </div>
));

export default EnhancedUnifiedDashboard;
