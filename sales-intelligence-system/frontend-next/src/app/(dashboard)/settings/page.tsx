'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { User, Mail, Shield, MessageCircle, Eye, EyeOff, Loader2, Cpu } from 'lucide-react'
import { getTelegramConfig, updateTelegramConfig, getLLMConfig, updateLLMConfig, type LLMConfigStatus } from '@/lib/api'

const ADMIN_ROLES = ['manager', 'founder', 'admin']
const ADMIN_ONLY_ROLES = ['founder', 'admin']

const LLM_PROVIDERS = [
  { id: 'anthropic' as const, label: 'Anthropic (Claude)', key: 'anthropic_api_key' },
  { id: 'openai' as const, label: 'OpenAI (GPT)', key: 'openai_api_key' },
  { id: 'openrouter' as const, label: 'OpenRouter', key: 'openrouter_api_key' },
  { id: 'moonshot' as const, label: 'Moonshot', key: 'moonshot_api_key' },
]

export default function SettingsPage() {
  const { user } = useAuth()
  const displayName = user?.full_name || user?.name || user?.email || 'User'
  const canEditTelegram = user && ADMIN_ROLES.includes(user.role)
  const canEditLLM = user && ADMIN_ONLY_ROLES.includes(user.role)

  const [telegramConfigured, setTelegramConfigured] = useState(false)
  const [telegramToken, setTelegramToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [telegramSaving, setTelegramSaving] = useState(false)
  const [telegramSaveError, setTelegramSaveError] = useState<string | null>(null)
  const [showTelegramInput, setShowTelegramInput] = useState(false)
  const [telegramLoaded, setTelegramLoaded] = useState(false)

  // LLM Providers (admin only)
  const [llmStatus, setLLMStatus] = useState<LLMConfigStatus | null>(null)
  const [llmLoaded, setLLMLoaded] = useState(false)
  const [editingProvider, setEditingProvider] = useState<keyof Pick<LLMConfigStatus, 'anthropic' | 'openai' | 'openrouter' | 'moonshot'> | null>(null)
  const [llmTokenValue, setLLMTokenValue] = useState('')
  const [llmShowToken, setLLMShowToken] = useState(false)
  const [llmSaving, setLLMSaving] = useState(false)
  const [llmError, setLLMError] = useState<string | null>(null)
  // Model selection (primary / fast / fallback)
  const [modelPrimary, setModelPrimary] = useState('')
  const [modelFast, setModelFast] = useState('')
  const [modelFallback, setModelFallback] = useState('')
  const [modelSaving, setModelSaving] = useState(false)
  const [modelError, setModelError] = useState<string | null>(null)

  useEffect(() => {
    if (!canEditTelegram) return
    const timeoutMs = 5000
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error('timeout')), timeoutMs)
    )
    Promise.race([getTelegramConfig(), timeoutPromise])
      .then((r) => {
        setTelegramConfigured(r.data?.configured ?? false)
        setShowTelegramInput(!(r.data?.configured ?? false))
      })
      .catch(() => {
        setTelegramLoaded(true)
        setShowTelegramInput(true)
      })
      .finally(() => setTelegramLoaded(true))
  }, [canEditTelegram])

  useEffect(() => {
    if (!canEditLLM) return
    getLLMConfig()
      .then((r) => {
        const data = r.data || null
        setLLMStatus(data)
        if (data?.model_primary) setModelPrimary(data.model_primary)
        if (data?.model_fast) setModelFast(data.model_fast)
        if (data?.model_fallback) setModelFallback(data.model_fallback)
      })
      .catch(() => setLLMStatus(null))
      .finally(() => setLLMLoaded(true))
  }, [canEditLLM])

  async function saveTelegramToken() {
    if (!canEditTelegram) return
    setTelegramSaving(true)
    setTelegramSaveError(null)
    const saveTimeoutMs = 15000
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error('Save timed out. Check your connection and that the backend is running.')), saveTimeoutMs)
    )
    try {
      await Promise.race([
        updateTelegramConfig({ telegram_bot_token: telegramToken.trim() || null }),
        timeoutPromise,
      ])
      setTelegramConfigured(!!telegramToken.trim())
      setShowTelegramInput(false)
      setTelegramToken('')
    } catch (e: unknown) {
      const msg = e && typeof e === 'object' && 'response' in e && (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        ? String((e as { response: { data: { detail: string } } }).response.data.detail)
        : e instanceof Error ? e.message : 'Save failed. Try again.'
      setTelegramSaveError(msg)
    } finally {
      setTelegramSaving(false)
    }
  }

  function clearTelegramAndShowInput() {
    setShowTelegramInput(true)
    setTelegramToken('')
    setTelegramSaveError(null)
  }

  function startEditLLM(provider: keyof Pick<LLMConfigStatus, 'anthropic' | 'openai' | 'openrouter' | 'moonshot'>) {
    setEditingProvider(provider)
    setLLMTokenValue('')
    setLLMError(null)
  }

  async function saveModelSelection() {
    if (!canEditLLM) return
    setModelSaving(true)
    setModelError(null)
    try {
      const res = await updateLLMConfig({
        model_primary: modelPrimary || null,
        model_fast: modelFast || null,
        model_fallback: modelFallback || null,
      })
      if (res.data) {
        setLLMStatus(res.data)
        if (res.data.model_primary) setModelPrimary(res.data.model_primary)
        if (res.data.model_fast) setModelFast(res.data.model_fast)
        if (res.data.model_fallback) setModelFallback(res.data.model_fallback)
      }
    } catch (e: unknown) {
      const msg = e && typeof e === 'object' && 'response' in e && (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        ? String((e as { response: { data: { detail: string } } }).response.data.detail)
        : e instanceof Error ? e.message : 'Save failed.'
      setModelError(msg)
    } finally {
      setModelSaving(false)
    }
  }

  async function saveLLMProvider() {
    if (!editingProvider || !canEditLLM) return
    const key = LLM_PROVIDERS.find((p) => p.id === editingProvider)?.key
    if (!key) return
    setLLMSaving(true)
    setLLMError(null)
    try {
      const body = { [key]: llmTokenValue.trim() || null }
      const res = await updateLLMConfig(body)
      setLLMStatus(res.data || null)
      setEditingProvider(null)
      setLLMTokenValue('')
    } catch (e: unknown) {
      const msg = e && typeof e === 'object' && 'response' in e && (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        ? String((e as { response: { data: { detail: string } } }).response.data.detail)
        : e instanceof Error ? e.message : 'Save failed.'
      setLLMError(msg)
    } finally {
      setLLMSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">Settings</h2>
        <p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">
          Your account and preferences
        </p>
      </div>

      <div className="rounded-2xl border border-zinc-200/80 bg-white p-6 shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
        <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
          <User className="h-5 w-5 text-amber-500" />
          Profile
        </h3>
        <dl className="space-y-3">
          <div className="flex items-center gap-3">
            <Mail className="h-4 w-4 text-zinc-400" />
            <div>
              <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Email</dt>
              <dd className="text-sm font-medium text-zinc-900 dark:text-white">{user?.email}</dd>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <User className="h-4 w-4 text-zinc-400" />
            <div>
              <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Name</dt>
              <dd className="text-sm font-medium text-zinc-900 dark:text-white">{displayName}</dd>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Shield className="h-4 w-4 text-zinc-400" />
            <div>
              <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Role</dt>
              <dd className="text-sm font-medium text-zinc-900 dark:text-white capitalize">
                {user?.role?.replace('_', ' ')}
              </dd>
            </div>
          </div>
        </dl>
      </div>

      {canEditTelegram && (
        <div className="rounded-2xl border border-zinc-200/80 bg-white p-6 shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
          <h3 className="mb-2 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
            <MessageCircle className="h-5 w-5 text-sky-500" />
            Telegram Bot (for alerts)
          </h3>
          <p className="mb-4 text-xs text-zinc-500 dark:text-zinc-400">
            Create a bot with @BotFather, then paste the token here. Alerts will be sent to users who added their Chat ID on the Alerts page.
          </p>
          {!telegramLoaded ? (
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <Loader2 className="h-4 w-4 animate-spin" /> Checking…
            </div>
          ) : showTelegramInput ? (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <input
                  type={showToken ? 'text' : 'password'}
                  placeholder="Paste bot token from @BotFather"
                  value={telegramToken}
                  onChange={(e) => { setTelegramToken(e.target.value); setTelegramSaveError(null) }}
                  className="min-w-[240px] rounded-xl border border-zinc-200 bg-zinc-50/80 px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-500/20 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
                />
                <button
                  type="button"
                  onClick={() => setShowToken((s) => !s)}
                  className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white px-2.5 py-2 text-xs font-medium text-zinc-600 hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
                  aria-label={showToken ? 'Hide token' : 'Show token'}
                >
                  {showToken ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                  {showToken ? 'Hide' : 'Show'}
                </button>
                <button
                  type="button"
                  onClick={saveTelegramToken}
                  disabled={telegramSaving || !telegramToken.trim()}
                  className="flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-2 text-xs font-medium text-white hover:bg-amber-600 disabled:opacity-50"
                >
                  {telegramSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                  Save
                </button>
              </div>
              {telegramSaveError && (
              <p className="text-xs text-red-600 dark:text-red-400" role="alert">
                {telegramSaveError}
              </p>
            )}
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                Token is stored securely and never shown again. Use Show/Hide only while editing.
              </p>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              <span className="rounded-lg bg-green-500/10 px-3 py-1.5 text-sm font-medium text-green-700 dark:text-green-400">
                Token saved
              </span>
              <span className="text-sm text-zinc-500 dark:text-zinc-400">••••••••••••</span>
              <button
                type="button"
                onClick={clearTelegramAndShowInput}
                className="text-xs font-medium text-amber-600 hover:underline dark:text-amber-400"
              >
                Change
              </button>
            </div>
          )}
        </div>
      )}

      {canEditLLM && (
        <div className="rounded-2xl border border-zinc-200/80 bg-white p-6 shadow-sm dark:border-zinc-700/50 dark:bg-zinc-900/40">
          <h3 className="mb-2 flex items-center gap-2 text-lg font-semibold text-zinc-900 dark:text-white">
            <Cpu className="h-5 w-5 text-violet-500" />
            LLM Providers
          </h3>
          <p className="mb-4 text-xs text-zinc-500 dark:text-zinc-400">
            Connect AI providers for daily pipeline, research, and reports. Only admins can set these. Keys are stored securely and never shown again.
          </p>
          {!llmLoaded ? (
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : (
            <div className="space-y-4">
              {LLM_PROVIDERS.map((provider) => (
                <div key={provider.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-zinc-200/60 bg-zinc-50/50 p-3 dark:border-zinc-700/50 dark:bg-zinc-800/30">
                  <span className="w-36 text-sm font-medium text-zinc-700 dark:text-zinc-300">{provider.label}</span>
                  {editingProvider === provider.id ? (
                    <>
                      <input
                        type={llmShowToken ? 'text' : 'password'}
                        placeholder={`Paste ${provider.label} API key`}
                        value={llmTokenValue}
                        onChange={(e) => { setLLMTokenValue(e.target.value); setLLMError(null) }}
                        className="min-w-[220px] rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
                      />
                      <button
                        type="button"
                        onClick={() => setLLMShowToken((s) => !s)}
                        className="flex items-center gap-1 rounded border border-zinc-200 bg-white px-2 py-1.5 text-xs dark:border-zinc-600 dark:bg-zinc-800"
                      >
                        {llmShowToken ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                        {llmShowToken ? 'Hide' : 'Show'}
                      </button>
                      <button
                        type="button"
                        onClick={saveLLMProvider}
                        disabled={llmSaving}
                        className="rounded bg-violet-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-violet-700 disabled:opacity-50"
                      >
                        {llmSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Save'}
                      </button>
                      <button
                        type="button"
                        onClick={() => { setEditingProvider(null); setLLMError(null) }}
                        className="text-xs text-zinc-500 hover:underline dark:text-zinc-400"
                      >
                        Cancel
                      </button>
                    </>
                  ) : llmStatus?.[provider.id] ? (
                    <>
                      <span className="rounded bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-700 dark:text-green-400">Configured</span>
                      <span className="text-xs text-zinc-500">••••••••••••</span>
                      <button
                        type="button"
                        onClick={() => startEditLLM(provider.id)}
                        className="text-xs font-medium text-violet-600 hover:underline dark:text-violet-400"
                      >
                        Change
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      onClick={() => startEditLLM(provider.id)}
                      className="rounded border border-violet-500/50 bg-violet-500/10 px-3 py-1.5 text-xs font-medium text-violet-700 hover:bg-violet-500/20 dark:text-violet-400"
                    >
                      Add API key
                    </button>
                  )}
                </div>
              ))}
              {llmError && (
                <p className="text-xs text-red-600 dark:text-red-400" role="alert">{llmError}</p>
              )}
              <div className="mt-4 border-t border-zinc-200/60 pt-4 dark:border-zinc-700/50">
                <h4 className="mb-3 text-sm font-semibold text-zinc-800 dark:text-zinc-200">Model selection</h4>
                <p className="mb-3 text-xs text-zinc-500 dark:text-zinc-400">
                  Primary for complex tasks; fast for scoring/ranking; fallback used if primary fails.
                </p>
                <div className="grid gap-3 sm:grid-cols-1 md:grid-cols-3">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">Primary</label>
                    <select
                      value={modelPrimary}
                      onChange={(e) => { setModelPrimary(e.target.value); setModelError(null) }}
                      className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
                    >
                      {(llmStatus?.models ?? []).map((m) => (
                        <option key={m.id} value={m.id}>{m.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">Fast</label>
                    <select
                      value={modelFast}
                      onChange={(e) => { setModelFast(e.target.value); setModelError(null) }}
                      className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
                    >
                      {(llmStatus?.models ?? []).map((m) => (
                        <option key={m.id} value={m.id}>{m.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-zinc-600 dark:text-zinc-400">Fallback</label>
                    <select
                      value={modelFallback}
                      onChange={(e) => { setModelFallback(e.target.value); setModelError(null) }}
                      className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
                    >
                      {(llmStatus?.models ?? []).map((m) => (
                        <option key={m.id} value={m.id}>{m.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={saveModelSelection}
                    disabled={modelSaving}
                    className="rounded-lg bg-violet-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-violet-700 disabled:opacity-50"
                  >
                    {modelSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save model selection'}
                  </button>
                </div>
                {modelError && (
                  <p className="mt-2 text-xs text-red-600 dark:text-red-400" role="alert">{modelError}</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
