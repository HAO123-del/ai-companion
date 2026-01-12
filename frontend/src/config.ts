// API Configuration
// In development: uses localhost
// In production: uses the deployed backend URL

const isDev = import.meta.env.DEV

// Production backend URL - update this when backend URL changes
const PRODUCTION_API_URL = 'https://ai-companion-api-ncrj.onrender.com'

// API base URL (without /api suffix)
export const API_BASE = isDev 
  ? 'http://localhost:8000' 
  : PRODUCTION_API_URL

// WebSocket base URL
export const WS_BASE = isDev
  ? 'ws://localhost:8000'
  : API_BASE.replace('https://', 'wss://').replace('http://', 'ws://')

// API endpoints with /api prefix
export const API_URL = `${API_BASE}/api`
