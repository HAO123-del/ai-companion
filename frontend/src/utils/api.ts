/**
 * API 配置
 * 开发环境使用代理，生产环境使用环境变量配置的后端地址
 */

const API_URL = import.meta.env.VITE_API_URL || ''

export function getApiUrl(path: string): string {
  if (API_URL) {
    return `${API_URL}${path}`
  }
  return path
}

export async function apiFetch(path: string, options?: RequestInit) {
  const url = getApiUrl(path)
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers
    }
  })
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }
  
  return response.json()
}

export default {
  getApiUrl,
  apiFetch
}
