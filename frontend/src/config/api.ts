// API configuration based on environment
const getApiBaseUrl = (): string => {
  // In development mode (Vite dev server)
  if (import.meta.env.DEV) {
    return 'http://localhost:8080/api'
  }

  // In production build (served from same origin)
  return '/api'
}

export const API_BASE_URL = getApiBaseUrl()
