'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { User, Mail, Shield, MessageCircle, Eye, EyeOff, Loader2 } from 'lucide-react'
import { getTelegramConfig, updateTelegramConfig } from '@/lib/api'

const ADMIN_ROLES = ['manager', 'founder', 'admin']

export default function SettingsPage() {
  const { user } = useAuth()
  const displayName = user?.full_name || user?.name || user?.email || 'User'
  const canEditTelegram = user && ADMIN_ROLES.includes(user.role)

  const [telegramConfigured, setTelegramConfigured] = useState(false)
  const [telegramToken, setTelegramToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [telegramSaving, setTelegramSaving] = useState(false)
  const [telegramSaveError, setTelegramSaveError] = useState<string | null>(null)
  const [showTelegramInput, setShowTelegramInput] = useState(false)
  const [telegramLoaded, setTelegramLoaded] = useState(false)

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
    </div>
  )
}
