import axios from 'axios'
import { supabase } from './supabase'

const apiBase = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api')
  : '/api'

const api = axios.create({
  baseURL: apiBase,
  headers: { 'Content-Type': 'application/json' },
  timeout: 20000,
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
    if (err.response?.status === 401 && !originalRequest._retryCount) {
      originalRequest._retryCount = 1
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
  api.get('/leads', { params })

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
  api.get('/alerts', { params })

export const markAlertRead = (alertId: string) =>
  api.patch(`/alerts/${alertId}/read`)

export const getNotificationPreferences = () =>
  api.get('/alerts/notification-preferences')

export const updateNotificationPreferences = (prefs: { notify_via_telegram?: boolean; notify_via_discord?: boolean; notify_via_whatsapp?: boolean; notify_via_email?: boolean; discord_webhook_url?: string; telegram_chat_id?: string | null }) =>
  api.patch('/alerts/notification-preferences', prefs)

export const getTelegramLinkToken = () =>
  api.get('/alerts/telegram-link-token')

export const getUnreadCount = () =>
  api.get('/alerts/unread-count')
export const sendTestAlert = () =>
  api.post('/alerts/send-test')

export const getRepPerformance = (params?: Record<string, string>) =>
  api.get('/analytics/rep-performance', { params })

export const getPipelineFunnel = (params?: Record<string, string>) =>
  api.get('/analytics/pipeline-funnel', { params })

export const getSourceAnalysis = (params?: Record<string, string>) =>
  api.get('/analytics/source-analysis', { params })

export const getConversionTrends = (params?: Record<string, string>) =>
  api.get('/analytics/conversion-trends', { params })

export const getUsers = () => api.get('/admin/users')
export const updateUser = (userId: string, payload: { role?: string; deal_owner_name?: string | null; name?: string; team?: string | null; is_active?: boolean }) =>
  api.patch(`/admin/users/${userId}`, payload)
export const getSyncStatus = () => api.get('/admin/sync-status')
export const triggerSync = () => api.post('/admin/sync/trigger')
export const getAIUsage = () => api.get('/admin/ai-usage')
export const getTelegramConfig = () => api.get<{ configured: boolean }>('/admin/telegram-config')
export const updateTelegramConfig = (body: { telegram_bot_token?: string | null }) =>
  api.patch('/admin/telegram-config', body)

export type LLMModelItem = { id: string; label: string; description: string; provider: string; router_id?: string | null }
export type LLMConfigStatus = {
  anthropic: boolean
  openai: boolean
  openrouter: boolean
  moonshot: boolean
  models: LLMModelItem[]
  model_primary: string
  model_fast: string
  model_fallback: string
}
export const getLLMConfig = () => api.get<LLMConfigStatus>('/admin/llm-config')
export const updateLLMConfig = (body: {
  anthropic_api_key?: string | null
  openai_api_key?: string | null
  openrouter_api_key?: string | null
  moonshot_api_key?: string | null
  model_primary?: string | null
  model_fast?: string | null
  model_fallback?: string | null
}) => api.patch<LLMConfigStatus & { message?: string }>('/admin/llm-config', body)

export const getDashboardSummary = () => api.get('/intelligence/summary')
export const getDealOwners = () => api.get<{ deal_owners: string[] }>('/intelligence/deal-owners')
export const getTeamAttention = () => api.get<{ items: TeamAttentionItem[] }>('/intelligence/team-attention')

export type TeamAttentionItem = {
  name: string
  deal_owner: string
  stale_count: number
  demos_pending: number
  sale_rate: number
  next_best_action: string
  suggested_action: string
}
export const uploadIntelligenceCSV = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/intelligence/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  })
}
export const clearDashboardSummary = () => api.delete('/intelligence/summary')

export const getAgentProfiles = () => api.get('/agents')
export const getAgentProfile = (id: string) => api.get(`/agents/${id}`)
export const addAgentNote = (id: string, text: string) => api.post(`/agents/${id}/notes`, { text })

export default api
