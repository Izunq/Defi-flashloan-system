import { useState, useEffect } from 'react';

export const useLoadingState = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentModule, setCurrentModule] = useState('Initializing...');

  const modules = [
    'Initializing Artemis AI Core...',
    'Loading system modules...',
    'Connecting to oracle networks...',
    'Calibrating risk engine...',
    'Establishing MEV protection...',
    'Activating trading algorithms...',
    'System ready for deployment!'
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + 2;
        if (newProgress <= 100) {
          const moduleIndex = Math.floor((newProgress / 100) * modules.length);
          setCurrentModule(modules[Math.min(moduleIndex, modules.length - 1)]);
        }
        return Math.min(newProgress, 100);
      });
    }, 60);

    const timer = setTimeout(() => {
      setIsLoading(false);
      setIsInitialized(true);
    }, 3000);

    return () => {
      clearInterval(interval);
      clearTimeout(timer);
    };
  }, []);

  return { 
    isLoading, 
    isInitialized, 
    progress, 
    currentModule 
  };
};
