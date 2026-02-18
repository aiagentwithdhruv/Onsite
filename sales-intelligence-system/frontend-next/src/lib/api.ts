import axios from 'axios'
import { supabase } from './supabase'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config
    if (err.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const { data } = await supabase.auth.refreshSession()
      if (data.session?.access_token) {
        originalRequest.headers.Authorization = `Bearer ${data.session.access_token}`
        return api(originalRequest)
      }
      if (typeof window !== 'undefined') window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const login = (email: string, password: string) =>
  supabase.auth.signInWithPassword({ email, password })

export const logout = () => supabase.auth.signOut()

export const getLeads = (params?: Record<string, string>) =>
  api.get('/leads/', { params })

export const getLeadDetail = (id: string) =>
  api.get(`/leads/${id}`)

export const performLeadAction = (id: string, action: string, notes?: string) =>
  api.post(`/leads/${id}/action`, { action, notes })

export const getLeadTimeline = (id: string) =>
  api.get(`/leads/${id}/timeline`)

export const triggerResearch = (leadId: string) =>
  api.post(`/research/${leadId}`)

export const getResearch = (leadId: string) =>
  api.get(`/research/${leadId}`)

export const getTodayBrief = () =>
  api.get('/briefs/today')

export const getBriefHistory = () =>
  api.get('/briefs/history')

export const getAlerts = (params?: Record<string, string>) =>
  api.get('/alerts/', { params })

export const markAlertRead = (alertId: string) =>
  api.patch(`/alerts/${alertId}/read`)

export const getUnreadCount = () =>
  api.get('/alerts/unread-count')

export const getRepPerformance = (params?: Record<string, string>) =>
  api.get('/analytics/rep-performance', { params })

export const getPipelineFunnel = (params?: Record<string, string>) =>
  api.get('/analytics/pipeline-funnel', { params })

export const getSourceAnalysis = (params?: Record<string, string>) =>
  api.get('/analytics/source-analysis', { params })

export const getConversionTrends = (params?: Record<string, string>) =>
  api.get('/analytics/conversion-trends', { params })

export const getUsers = () => api.get('/admin/users')
export const getSyncStatus = () => api.get('/admin/sync-status')
export const triggerSync = () => api.post('/admin/sync/trigger')
export const getAIUsage = () => api.get('/admin/ai-usage')

export const getDashboardSummary = () => api.get('/intelligence/summary')
export const uploadIntelligenceCSV = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/intelligence/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  })
}
export const clearDashboardSummary = () => api.delete('/intelligence/summary')

export default api
