// API Configuration
// In development: uses localhost
// In production: uses environment variable VITE_API_URL

const isDev = import.meta.env.DEV

// API base URL (without /api suffix)
export const API_BASE = isDev 
  ? 'http://localhost:8000' 
  : (import.meta.env.VITE_API_URL || window.location.origin)

// WebSocket base URL
export const WS_BASE = isDev
  ? 'ws://localhost:8000'
  : API_BASE.replace('https://', 'wss://').replace('http://', 'ws://')

// API endpoints with /api prefix
export const API_URL = `${API_BASE}/api`
