import React from 'react';
import { Web3Provider } from './components/Web3Provider.simple';
import ArtemisAIDashboard from './components/ArtemisAIDashboard';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './styles/main.css';

const App: React.FC = () => {
  return (
    <Web3Provider>
      <ArtemisAIDashboard />
      <ToastContainer position="bottom-right" theme="dark" />
    </Web3Provider>
  );
};

export default App;