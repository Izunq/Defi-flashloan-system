import React, { useState } from 'react';
import { Web3Provider } from './components/Web3Provider';
import EnhancedDashboard from './components/EnhancedDashboard';
import VaultDashboard from './components/VaultDashboard';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './styles/main.css';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'vault'>('dashboard');

  return (
    <Web3Provider>
      <div className="app-container">
        <header className="app-header">
          <h1>Arbitrage System</h1>
          <nav className="main-nav">
            <button 
              className={`nav-button ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              AI Dashboard
            </button>
            <button 
              className={`nav-button ${activeTab === 'vault' ? 'active' : ''}`}
              onClick={() => setActiveTab('vault')}
            >
              ERC-4626 Vault
            </button>
          </nav>
        </header>

        <main className="app-content">
          {activeTab === 'dashboard' && <EnhancedDashboard />}
          {activeTab === 'vault' && <VaultDashboard />}
        </main>

        <footer className="app-footer">
          <p>© 2023 Arbitrage System. All rights reserved.</p>
        </footer>
      </div>
      <ToastContainer position="bottom-right" theme="dark" />
    </Web3Provider>
  );
};

export default App;