import React from 'react';
import { Web3Provider } from './components/Web3Provider';
import UnifiedDashboard from './components/UnifiedDashboard';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './styles/main.css';

const App: React.FC = () => {
  return (
    <Web3Provider>
      <UnifiedDashboard />
      <ToastContainer position="bottom-right" theme="dark" />
    </Web3Provider>
  );
};

export default App;