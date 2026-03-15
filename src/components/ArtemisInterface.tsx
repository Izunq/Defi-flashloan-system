import React, { useState, useEffect, useRef } from 'react';
import './ArtemisInterface.css';

interface ArtemisMessage {
  id: string;
  type: 'user' | 'artemis' | 'thinking' | 'error';
  content: string;
  timestamp: string;
  metadata?: {
    actions?: ActionButton[];
    confidence?: number;
    sources?: string[];
    charts?: any[];
  };
}

interface ActionButton {
  type: string;
  label: string;
  endpoint: string;
}

const ArtemisInterface: React.FC = () => {
  const [messages, setMessages] = useState<ArtemisMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const websocketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const conversationId = useRef(generateId());

  // Sample prompts to help users get started
  const samplePrompts = [
    "What's the performance of our arbitrage strategies today?",
    "Show me the latest MEV protection alerts",
    "Analyze gas costs across different chains",
    "What are the current risk levels in our portfolio?",
    "Generate a profit/loss report for the last 7 days"
  ];

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    try {
      websocketRef.current = new WebSocket('ws://localhost:8083/ws/artemis');
      
      websocketRef.current.onopen = () => {
        setIsConnected(true);
        addMessage({
          id: generateId(),
          type: 'artemis',
          content: "Hello! I'm Artemis, your AI assistant for the flash loan arbitrage system. I can help you analyze performance, monitor risks, and understand your trading data. What would you like to know?",
          timestamp: new Date().toISOString()
        });
      };

      websocketRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'thinking') {
          setIsTyping(true);
          addMessage({
            id: generateId(),
            type: 'thinking',
            content: message.content,
            timestamp: new Date().toISOString()
          });
        } else {
          setIsTyping(false);
          // Remove thinking message if it exists
          setMessages(prev => prev.filter(msg => msg.type !== 'thinking'));
          
          addMessage({
            id: generateId(),
            type: message.type,
            content: message.content,
            timestamp: message.timestamp,
            metadata: message.metadata
          });
        }
      };

      websocketRef.current.onclose = () => {
        setIsConnected(false);
        setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
      };

      websocketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setIsConnected(false);
    }
  };

  const addMessage = (message: ArtemisMessage) => {
    setMessages(prev => [...prev, message]);
  };

  const sendMessage = () => {
    if (!inputValue.trim() || !isConnected) return;

    const userMessage: ArtemisMessage = {
      id: generateId(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    addMessage(userMessage);

    // Send to WebSocket
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({
        content: inputValue,
        conversation_id: conversationId.current,
        timestamp: new Date().toISOString()
      }));
    }

    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const useSamplePrompt = (prompt: string) => {
    setInputValue(prompt);
  };

  const executeAction = async (action: ActionButton) => {
    try {
      // Here you would integrate with your existing API
      const response = await fetch(`http://localhost:8083${action.endpoint}`);
      const data = await response.json();
      
      addMessage({
        id: generateId(),
        type: 'artemis',
        content: `Action "${action.label}" executed successfully. ${JSON.stringify(data)}`,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      addMessage({
        id: generateId(),
        type: 'error',
        content: `Failed to execute action: ${error}`,
        timestamp: new Date().toISOString()
      });
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  function generateId() {
    return Math.random().toString(36).substr(2, 9);
  }

  return (
    <div className="artemis-interface">
      <div className="artemis-header">
        <div className="artemis-title">
          <span className="artemis-icon">🧠</span>
          <h2>Artemis AI</h2>
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </div>
        </div>
        <div className="artemis-subtitle">
          Your intelligent assistant for flash loan arbitrage
        </div>
      </div>

      <div className="messages-container">
        {messages.length === 1 && (
          <div className="sample-prompts">
            <h4>Try asking:</h4>
            {samplePrompts.map((prompt, index) => (
              <button
                key={index}
                className="sample-prompt"
                onClick={() => useSamplePrompt(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-header">
              <span className="message-sender">
                {message.type === 'user' ? '👤' : 
                 message.type === 'thinking' ? '⏳' : 
                 message.type === 'error' ? '❌' : '🧠'} 
                {message.type === 'user' ? 'You' : 
                 message.type === 'thinking' ? 'Artemis (thinking...)' : 
                 message.type === 'error' ? 'Error' : 'Artemis'}
              </span>
              <span className="message-time">{formatTimestamp(message.timestamp)}</span>
            </div>
            
            <div className="message-content">
              {message.content}
            </div>

            {message.metadata && (
              <div className="message-metadata">
                {message.metadata.confidence && (
                  <div className="confidence-indicator">
                    <span>Confidence: {(message.metadata.confidence * 100).toFixed(0)}%</span>
                    <div className="confidence-bar">
                      <div 
                        className="confidence-fill"
                        style={{ width: `${message.metadata.confidence * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {message.metadata.actions && message.metadata.actions.length > 0 && (
                  <div className="action-buttons">
                    {message.metadata.actions.map((action, index) => (
                      <button
                        key={index}
                        className="action-button"
                        onClick={() => executeAction(action)}
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                )}

                {message.metadata.sources && message.metadata.sources.length > 0 && (
                  <div className="sources">
                    <span>Sources: {message.metadata.sources.join(', ')}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isConnected ? "Ask Artemis anything about your trading system..." : "Connecting to Artemis..."}
            disabled={!isConnected}
            rows={1}
            className="message-input"
          />
          <button
            onClick={sendMessage}
            disabled={!inputValue.trim() || !isConnected}
            className="send-button"
          >
            ⚡
          </button>
        </div>
        
        <div className="input-hints">
          <span>Press Enter to send, Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );
};

export default ArtemisInterface;
