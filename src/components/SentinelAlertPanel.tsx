import React, { useState, useEffect } from 'react';
import { SentinelAlert, useSentinelAlerts } from '../hooks/useSentinelAlerts';
import './SentinelAlertPanel.css';

interface SentinelAlertPanelProps {
  className?: string;
  maxAlerts?: number;
  showFilters?: boolean;
  onAlertClick?: (alert: SentinelAlert) => void;
  minPriority?: string;
}

const SentinelAlertPanel: React.FC<SentinelAlertPanelProps> = ({
  className = '',
  maxAlerts = 10,
  showFilters = true,
  onAlertClick,
  minPriority = 'low'
}) => {
  const { 
    alerts, 
    loading, 
    error, 
    acknowledgeAlert, 
    dismissAlert,
    filterAlerts,
    hasActiveAlerts
  } = useSentinelAlerts();
  
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [selectedPriorities, setSelectedPriorities] = useState<string[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<SentinelAlert[]>([]);
  
  // Apply filters when alerts or filter selections change
  useEffect(() => {
    setFilteredAlerts(filterAlerts(selectedSources, selectedPriorities));
  }, [alerts, selectedSources, selectedPriorities, filterAlerts]);
  
  // Toggle source filter
  const toggleSourceFilter = (source: string) => {
    setSelectedSources(prev => 
      prev.includes(source) 
        ? prev.filter(s => s !== source) 
        : [...prev, source]
    );
  };
  
  // Toggle priority filter
  const togglePriorityFilter = (priority: string) => {
    setSelectedPriorities(prev => 
      prev.includes(priority) 
        ? prev.filter(p => p !== priority) 
        : [...prev, priority]
    );
  };
  
  // Get color for priority
  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'low': return '#3498db';      // Blue
      case 'medium': return '#f39c12';   // Orange
      case 'high': return '#e67e22';     // Dark Orange
      case 'critical': return '#e74c3c'; // Red
      case 'emergency': return '#c0392b';// Dark Red
      default: return '#95a5a6';         // Gray
    }
  };
  
  // Get icon for alert source
  const getSourceIcon = (source: string): string => {
    switch (source) {
      case 'oracle': return '🔮';
      case 'mev': return '🛡️';
      case 'strategy': return '📊';
      default: return '⚠️';
    }
  };
  
  // Format timestamp
  const formatTime = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };
  
  // Handle alert click
  const handleAlertClick = (alert: SentinelAlert) => {
    if (onAlertClick) {
      onAlertClick(alert);
    }
  };
  
  // Handle acknowledge button click
  const handleAcknowledge = (e: React.MouseEvent, alertId: string) => {
    e.stopPropagation();
    acknowledgeAlert(alertId);
  };
  
  // Handle dismiss button click
  const handleDismiss = (e: React.MouseEvent, alertId: string) => {
    e.stopPropagation();
    dismissAlert(alertId);
  };
  
  if (loading) {
    return (
      <div className={`sentinel-alert-panel ${className}`}>
        <div className="alert-panel-loading">
          <div className="loading-spinner"></div>
          <p>Loading alerts...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={`sentinel-alert-panel ${className}`}>
        <div className="alert-panel-error">
          <p>Error: {error}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`sentinel-alert-panel ${className}`}>
      <div className="alert-panel-header">
        <h2>
          Sentinel Alerts
          {hasActiveAlerts('high') && (
            <span className="alert-badge high">!</span>
          )}
        </h2>
        
        {showFilters && (
          <div className="alert-filters">
            <div className="filter-group">
              <span className="filter-label">Source:</span>
              <button 
                className={`filter-btn ${selectedSources.includes('oracle') ? 'active' : ''}`}
                onClick={() => toggleSourceFilter('oracle')}
              >
                🔮 Oracle
              </button>
              <button 
                className={`filter-btn ${selectedSources.includes('mev') ? 'active' : ''}`}
                onClick={() => toggleSourceFilter('mev')}
              >
                🛡️ MEV
              </button>
              <button 
                className={`filter-btn ${selectedSources.includes('strategy') ? 'active' : ''}`}
                onClick={() => toggleSourceFilter('strategy')}
              >
                📊 Strategy
              </button>
            </div>
            
            <div className="filter-group">
              <span className="filter-label">Priority:</span>
              <button 
                className={`filter-btn ${selectedPriorities.includes('low') ? 'active' : ''}`}
                onClick={() => togglePriorityFilter('low')}
                style={{ borderLeft: `4px solid ${getPriorityColor('low')}` }}
              >
                Low
              </button>
              <button 
                className={`filter-btn ${selectedPriorities.includes('medium') ? 'active' : ''}`}
                onClick={() => togglePriorityFilter('medium')}
                style={{ borderLeft: `4px solid ${getPriorityColor('medium')}` }}
              >
                Medium
              </button>
              <button 
                className={`filter-btn ${selectedPriorities.includes('high') ? 'active' : ''}`}
                onClick={() => togglePriorityFilter('high')}
                style={{ borderLeft: `4px solid ${getPriorityColor('high')}` }}
              >
                High
              </button>
              <button 
                className={`filter-btn ${selectedPriorities.includes('critical') ? 'active' : ''}`}
                onClick={() => togglePriorityFilter('critical')}
                style={{ borderLeft: `4px solid ${getPriorityColor('critical')}` }}
              >
                Critical
              </button>
              <button 
                className={`filter-btn ${selectedPriorities.includes('emergency') ? 'active' : ''}`}
                onClick={() => togglePriorityFilter('emergency')}
                style={{ borderLeft: `4px solid ${getPriorityColor('emergency')}` }}
              >
                Emergency
              </button>
            </div>
          </div>
        )}
      </div>
      
      <div className="alert-list">
        {filteredAlerts.length === 0 ? (
          <div className="no-alerts">
            <p>No alerts to display</p>
          </div>
        ) : (
          filteredAlerts
            .filter(alert => !alert.dismissed)
            .slice(0, maxAlerts)
            .map(alert => (
              <div 
                key={alert.alert_id}
                className={`alert-item ${alert.acknowledged ? 'acknowledged' : ''} ${alert.resolved ? 'resolved' : ''} priority-${alert.priority}`}
                onClick={() => handleAlertClick(alert)}
                style={{ borderLeft: `4px solid ${getPriorityColor(alert.priority)}` }}
              >
                <div className="alert-icon">
                  {getSourceIcon(alert.source)}
                </div>
                
                <div className="alert-content">
                  <div className="alert-title">
                    <span className="alert-priority" style={{ backgroundColor: getPriorityColor(alert.priority) }}>
                      {alert.priority.toUpperCase()}
                    </span>
                    {alert.title}
                  </div>
                  
                  <div className="alert-message">{alert.message}</div>
                  
                  <div className="alert-meta">
                    <span className="alert-time">{formatTime(alert.timestamp)}</span>
                    {alert.resolved && <span className="alert-resolved">✓ Resolved</span>}
                  </div>
                </div>
                
                <div className="alert-actions">
                  {!alert.acknowledged && (
                    <button 
                      className="alert-btn acknowledge"
                      onClick={(e) => handleAcknowledge(e, alert.alert_id)}
                    >
                      Acknowledge
                    </button>
                  )}
                  
                  <button 
                    className="alert-btn dismiss"
                    onClick={(e) => handleDismiss(e, alert.alert_id)}
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  );
};

export default SentinelAlertPanel;