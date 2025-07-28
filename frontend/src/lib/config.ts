// API Configuration for different environments
export const getApiBaseUrl = (): string => {
  // Check if we're in development (localhost)
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  
  // Production environment via ngrok - use Next.js API proxy to bypass browser restrictions
  if (typeof window !== 'undefined' && window.location.hostname.includes('ngrok-free.app')) {
    return window.location.origin + '/api/proxy';
  }
  
  // Fallback to localhost for any other case
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();