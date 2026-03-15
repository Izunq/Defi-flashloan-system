import { useState, useEffect, useMemo } from 'react';

interface LoadingHook {
  isLoading: boolean;
  error: Error | null;
  serviceName: string;
}

interface LoadingState {
  isLoading: boolean;
  errors: {
    name: string;
    message: string;
    serviceName: string;
  }[];
}

export const useCombinedLoadingState = (...hooks: LoadingHook[]): LoadingState => {
  const [isTimedOut, setIsTimedOut] = useState(false);
  const [timeoutServices, setTimeoutServices] = useState<string[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const stillLoading = hooks.filter(h => h.isLoading && !h.error);
      if (stillLoading.length > 0) {
        setIsTimedOut(true);
        setTimeoutServices(stillLoading.map(h => h.serviceName));
      }
    }, 15000); // 15 second timeout

    // Clear timeout if all hooks are done loading or have errors
    if (hooks.every(h => !h.isLoading || h.error)) {
      clearTimeout(timer);
      setIsTimedOut(false);
      setTimeoutServices([]);
    }

    return () => clearTimeout(timer);
  }, [hooks]);

  const isLoading = useMemo(() => {
    return hooks.some(h => h.isLoading) && !isTimedOut;
  }, [hooks, isTimedOut]);

  const errors = useMemo(() => {
    let errorList = hooks
      .filter(h => h.error)
      .map(h => ({
        name: h.error!.name,
        message: h.error!.message,
        serviceName: h.serviceName
      }));

    // Add timeout errors
    if (isTimedOut && timeoutServices.length > 0) {
      errorList.push({
        name: 'TimeoutError',
        message: `Services failed to respond within 15 seconds: ${timeoutServices.join(', ')}`,
        serviceName: 'Application Loader'
      });
    }

    return errorList;
  }, [hooks, isTimedOut, timeoutServices]);

  const overallIsLoading = isLoading && errors.length === 0;

  return {
    isLoading: overallIsLoading,
    errors
  };
};
