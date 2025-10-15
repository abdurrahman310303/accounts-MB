import axios from 'axios'

// Use environment variable for API URL, fallback to your Railway backend for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://accounts-mb-production.up.railway.app/api/v1'

console.log('API Base URL:', API_BASE_URL) // For debugging

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for error handling
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error.response?.data || error.message)
  }
)

// Account API
export const accountAPI = {
  getAll: () => api.get('/accounts/'),
  getById: (id) => api.get(`/accounts/${id}/`),
  create: (data) => api.post('/accounts/', data),
  update: (id, data) => api.put(`/accounts/${id}/`, data),
  delete: (id) => api.delete(`/accounts/${id}/`),
  getSummary: () => api.get('/accounts/summary/overview/'),
}

// Transaction API
export const transactionAPI = {
  getAll: (params = {}) => api.get('/transactions/', { params }),
  getById: (id) => api.get(`/transactions/${id}/`),
  create: (data) => api.post('/transactions/', data),
  update: (id, data) => api.put(`/transactions/${id}/`, data),
  delete: (id) => api.delete(`/transactions/${id}/`),
}



// Category API
export const categoryAPI = {
  getAll: () => api.get('/categories/'),
  getById: (id) => api.get(`/categories/${id}/`),
  create: (data) => api.post('/categories/', data),
  update: (id, data) => api.put(`/categories/${id}/`, data),
  delete: (id) => api.delete(`/categories/${id}/`),
}

// Team API
export const teamAPI = {
  getAll: () => api.get('/teams/'),
  getById: (id) => api.get(`/teams/${id}/`),
  create: (data) => api.post('/teams/', data),
  update: (id, data) => api.put(`/teams/${id}/`, data),
  delete: (id) => api.delete(`/teams/${id}/`),
}

// Report API
export const reportAPI = {
  getProfitLoss: (params = {}) => api.get('/reports/profit-loss', { params }),
  getBalanceSheet: (params = {}) => api.get('/reports/balance-sheet', { params }),
  getCashFlow: (params = {}) => api.get('/reports/cash-flow', { params }),
}

// Utility functions
export const formatCurrency = (amount, currency = 'PKR') => {
  // Handle NaN or invalid values
  if (isNaN(amount) || amount === null || amount === undefined) {
    const symbol = currency === 'USD' ? '$' : 'Rs.'
    return `${symbol}0.00`
  }

  // Use appropriate locale and currency formatting
  const locale = currency === 'USD' ? 'en-US' : 'en-PK'
  const currencyCode = currency === 'USD' ? 'USD' : 'PKR'
  
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  } catch (error) {
    // Fallback formatting if Intl fails
    const symbol = currency === 'USD' ? '$' : 'Rs.'
    return `${symbol}${Math.abs(amount).toFixed(2)}`
  }
}

// Compact currency formatting for dashboard stats
export const formatCurrencyCompact = (amount, currency = 'PKR') => {
  // Handle NaN or invalid values
  if (isNaN(amount) || amount === null || amount === undefined) {
    const symbol = currency === 'USD' ? '$' : 'Rs.'
    return `${symbol}0`
  }

  const absAmount = Math.abs(amount)
  const symbol = currency === 'USD' ? '$' : 'Rs.'
  const sign = amount < 0 ? '-' : ''

  // Format based on amount size
  if (absAmount >= 10000000) { // 10 million and above
    return `${sign}${symbol}${(absAmount / 10000000).toFixed(1)}Cr`
  } else if (absAmount >= 100000) { // 1 lakh and above
    return `${sign}${symbol}${(absAmount / 100000).toFixed(1)}L`
  } else if (absAmount >= 1000) { // 1 thousand and above
    return `${sign}${symbol}${(absAmount / 1000).toFixed(1)}K`
  } else {
    return `${sign}${symbol}${absAmount.toFixed(0)}`
  }
}

export const formatDate = (date) => {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

export default api
