import React from 'react';

const App: React.FC = () => {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>🚀 Artemis AI Core</h1>
      <p>Loading test - if you see this, React is working!</p>
      <div style={{ 
        backgroundColor: '#f0f0f0', 
        padding: '20px', 
        margin: '20px',
        borderRadius: '8px'
      }}>
        <h2>System Status</h2>
        <p>✅ Frontend: Running on port 5175</p>
        <p>✅ Backend: Running on port 8083</p>
        <p>✅ React: Successfully loaded</p>
      </div>
      <button 
        onClick={() => window.location.href = window.location.href + '?test=full'}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        Load Full Dashboard
      </button>
    </div>
  );
};

export default App;
