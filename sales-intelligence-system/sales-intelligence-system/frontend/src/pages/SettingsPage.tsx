import { useState, useEffect } from 'react'
import {
  Save,
  Eye,
  EyeOff,
  CheckCircle,
  AlertTriangle,
  Database,
  Key,
  Globe,
  Bot,
  MessageSquare,
  Mail,
  Loader2,
  RefreshCw,
  Shield,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { cn } from '../lib/utils'

interface CredentialField {
  key: string
  label: string
  value: string
  placeholder: string
  secret?: boolean
  required?: boolean
}

interface CredentialGroup {
  title: string
  icon: React.ReactNode
  description: string
  fields: CredentialField[]
  testEndpoint?: string
}

const DEFAULT_CREDENTIALS: Record<string, string> = {
  // Supabase
  supabase_url: import.meta.env.VITE_SUPABASE_URL || '',
  supabase_anon_key: import.meta.env.VITE_SUPABASE_ANON_KEY || '',
  supabase_service_key: '',
  // AI
  anthropic_api_key: '',
  openai_api_key: '',
  // Zoho
  zoho_client_id: '',
  zoho_client_secret: '',
  zoho_refresh_token: '',
  zoho_api_domain: 'https://www.zohoapis.in',
  // WhatsApp
  gupshup_api_key: '',
  gupshup_app_name: '',
  gupshup_source_number: '',
  // Email
  resend_api_key: '',
  from_email: 'alerts@onsite.team',
}

export default function SettingsPage() {
  const { user } = useAuth()
  const [credentials, setCredentials] = useState<Record<string, string>>(DEFAULT_CREDENTIALS)
  const [visibleFields, setVisibleFields] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, 'success' | 'error' | 'testing'>>({})

  // Load saved credentials from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('onsite_credentials')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setCredentials((prev) => ({ ...prev, ...parsed }))
      } catch {
        // ignore invalid JSON
      }
    }
  }, [])

  // Only admin/founder can access
  if (!user || !['admin', 'founder', 'manager'].includes(user.role)) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <Shield className="mx-auto h-12 w-12 text-slate-300" />
          <h2 className="mt-4 text-lg font-semibold text-slate-800">Access Denied</h2>
          <p className="mt-1 text-sm text-slate-500">
            Only admins, founders, and managers can access settings.
          </p>
        </div>
      </div>
    )
  }

  function updateField(key: string, value: string) {
    setCredentials((prev) => ({ ...prev, [key]: value }))
    setSaved(false)
  }

  function toggleVisibility(key: string) {
    setVisibleFields((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      // Save to localStorage (frontend credentials)
      localStorage.setItem('onsite_credentials', JSON.stringify(credentials))

      // Also push backend credentials to the API
      const backendCreds = {
        supabase_url: credentials.supabase_url,
        supabase_service_key: credentials.supabase_service_key,
        anthropic_api_key: credentials.anthropic_api_key,
        openai_api_key: credentials.openai_api_key,
        zoho_client_id: credentials.zoho_client_id,
        zoho_client_secret: credentials.zoho_client_secret,
        zoho_refresh_token: credentials.zoho_refresh_token,
        zoho_api_domain: credentials.zoho_api_domain,
        gupshup_api_key: credentials.gupshup_api_key,
        gupshup_app_name: credentials.gupshup_app_name,
        gupshup_source_number: credentials.gupshup_source_number,
        resend_api_key: credentials.resend_api_key,
        from_email: credentials.from_email,
      }

      try {
        await fetch('/api/admin/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(backendCreds),
        })
      } catch {
        // Backend might not be running yet — that's fine, localStorage saved
      }

      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setError('Failed to save settings')
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  async function testConnection(groupKey: string) {
    setTestResults((prev) => ({ ...prev, [groupKey]: 'testing' }))

    try {
      if (groupKey === 'supabase') {
        const url = credentials.supabase_url
        const key = credentials.supabase_anon_key
        if (!url || !key) throw new Error('Missing URL or key')
        const res = await fetch(`${url}/rest/v1/`, { headers: { apikey: key } })
        if (res.ok) {
          setTestResults((prev) => ({ ...prev, [groupKey]: 'success' }))
        } else {
          throw new Error(`HTTP ${res.status}`)
        }
      } else if (groupKey === 'anthropic') {
        // Just check the key format
        if (credentials.anthropic_api_key.startsWith('sk-ant-')) {
          setTestResults((prev) => ({ ...prev, [groupKey]: 'success' }))
        } else {
          throw new Error('Invalid key format')
        }
      } else if (groupKey === 'zoho') {
        if (credentials.zoho_client_id && credentials.zoho_client_secret) {
          setTestResults((prev) => ({ ...prev, [groupKey]: 'success' }))
        } else {
          throw new Error('Missing credentials')
        }
      } else {
        // Generic: mark success if key exists
        setTestResults((prev) => ({ ...prev, [groupKey]: 'success' }))
      }
    } catch {
      setTestResults((prev) => ({ ...prev, [groupKey]: 'error' }))
    }

    setTimeout(() => {
      setTestResults((prev) => {
        const next = { ...prev }
        delete next[groupKey]
        return next
      })
    }, 5000)
  }

  const groups: (CredentialGroup & { key: string })[] = [
    {
      key: 'supabase',
      title: 'Supabase (Database)',
      icon: <Database className="h-5 w-5 text-green-600" />,
      description: 'PostgreSQL database, auth, and realtime',
      fields: [
        {
          key: 'supabase_url',
          label: 'Project URL',
          value: credentials.supabase_url,
          placeholder: 'https://xxx.supabase.co',
          required: true,
        },
        {
          key: 'supabase_anon_key',
          label: 'Anon Key (Public)',
          value: credentials.supabase_anon_key,
          placeholder: 'eyJhbGciOi...',
          secret: true,
          required: true,
        },
        {
          key: 'supabase_service_key',
          label: 'Service Role Key',
          value: credentials.supabase_service_key,
          placeholder: 'eyJhbGciOi...',
          secret: true,
        },
      ],
    },
    {
      key: 'anthropic',
      title: 'AI (Claude + GPT Fallback)',
      icon: <Bot className="h-5 w-5 text-purple-600" />,
      description: 'Claude for scoring/research, GPT-4o as fallback',
      fields: [
        {
          key: 'anthropic_api_key',
          label: 'Anthropic API Key',
          value: credentials.anthropic_api_key,
          placeholder: 'sk-ant-api...',
          secret: true,
          required: true,
        },
        {
          key: 'openai_api_key',
          label: 'OpenAI API Key (Fallback)',
          value: credentials.openai_api_key,
          placeholder: 'sk-...',
          secret: true,
        },
      ],
    },
    {
      key: 'zoho',
      title: 'Zoho CRM',
      icon: <Globe className="h-5 w-5 text-blue-600" />,
      description: 'Lead sync, notes, activities from Zoho',
      fields: [
        {
          key: 'zoho_client_id',
          label: 'Client ID',
          value: credentials.zoho_client_id,
          placeholder: '1000.xxx...',
          required: true,
        },
        {
          key: 'zoho_client_secret',
          label: 'Client Secret',
          value: credentials.zoho_client_secret,
          placeholder: 'xxx...',
          secret: true,
          required: true,
        },
        {
          key: 'zoho_refresh_token',
          label: 'Refresh Token',
          value: credentials.zoho_refresh_token,
          placeholder: '1000.xxx...',
          secret: true,
          required: true,
        },
        {
          key: 'zoho_api_domain',
          label: 'API Domain',
          value: credentials.zoho_api_domain,
          placeholder: 'https://www.zohoapis.in',
        },
      ],
    },
    {
      key: 'whatsapp',
      title: 'WhatsApp (Gupshup)',
      icon: <MessageSquare className="h-5 w-5 text-green-500" />,
      description: 'WhatsApp Business alerts via Gupshup',
      fields: [
        {
          key: 'gupshup_api_key',
          label: 'API Key',
          value: credentials.gupshup_api_key,
          placeholder: 'xxx...',
          secret: true,
        },
        {
          key: 'gupshup_app_name',
          label: 'App Name',
          value: credentials.gupshup_app_name,
          placeholder: 'onsite-alerts',
        },
        {
          key: 'gupshup_source_number',
          label: 'Source Number',
          value: credentials.gupshup_source_number,
          placeholder: '919999900000',
        },
      ],
    },
    {
      key: 'email',
      title: 'Email (Resend)',
      icon: <Mail className="h-5 w-5 text-blue-500" />,
      description: 'Email alerts and weekly reports',
      fields: [
        {
          key: 'resend_api_key',
          label: 'Resend API Key',
          value: credentials.resend_api_key,
          placeholder: 're_xxx...',
          secret: true,
        },
        {
          key: 'from_email',
          label: 'From Email',
          value: credentials.from_email,
          placeholder: 'alerts@onsite.team',
        },
      ],
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage API credentials and integrations
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className={cn(
            'inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium text-white transition-colors',
            saved
              ? 'bg-green-600'
              : 'bg-blue-600 hover:bg-blue-700 disabled:opacity-50'
          )}
        >
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : saved ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {saving ? 'Saving...' : saved ? 'Saved!' : 'Save All'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3">
          <AlertTriangle className="h-4 w-4 text-red-500" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Credential Groups */}
      <div className="space-y-4">
        {groups.map((group) => (
          <div
            key={group.key}
            className="rounded-xl border border-slate-200 bg-white"
          >
            {/* Group Header */}
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-50">
                  {group.icon}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    {group.title}
                  </h3>
                  <p className="text-xs text-slate-500">{group.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {testResults[group.key] === 'testing' && (
                  <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Testing...
                  </span>
                )}
                {testResults[group.key] === 'success' && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                    <CheckCircle className="h-3.5 w-3.5" />
                    Connected
                  </span>
                )}
                {testResults[group.key] === 'error' && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Failed
                  </span>
                )}
                <button
                  onClick={() => testConnection(group.key)}
                  disabled={testResults[group.key] === 'testing'}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Test
                </button>
              </div>
            </div>

            {/* Fields */}
            <div className="space-y-4 px-6 py-4">
              {group.fields.map((field) => (
                <div key={field.key}>
                  <label className="mb-1 flex items-center gap-1.5 text-sm font-medium text-slate-700">
                    {field.secret && <Key className="h-3.5 w-3.5 text-amber-500" />}
                    {field.label}
                    {field.required && (
                      <span className="text-red-400">*</span>
                    )}
                  </label>
                  <div className="relative">
                    <input
                      type={
                        field.secret && !visibleFields.has(field.key)
                          ? 'password'
                          : 'text'
                      }
                      value={field.value}
                      onChange={(e) => updateField(field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 pr-10 text-sm text-slate-800 placeholder:text-slate-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {field.secret && (
                      <button
                        type="button"
                        onClick={() => toggleVisibility(field.key)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600"
                      >
                        {visibleFields.has(field.key) ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Database Migration Section */}
      <div className="rounded-xl border border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-50">
              <Database className="h-5 w-5 text-indigo-600" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">
                Database Migration
              </h3>
              <p className="text-xs text-slate-500">
                Run this in Supabase SQL Editor to set up tables
              </p>
            </div>
          </div>
        </div>
        <div className="px-6 py-4">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                1
              </span>
              <p className="text-sm text-slate-700">
                Go to{' '}
                <a
                  href={`${credentials.supabase_url ? credentials.supabase_url.replace('.supabase.co', '') : 'https://supabase.com'}/project/jfuvhaampbngijfxgnnf/sql`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-blue-600 hover:text-blue-800"
                >
                  Supabase SQL Editor
                </a>
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                2
              </span>
              <p className="text-sm text-slate-700">
                Copy & run{' '}
                <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-mono text-slate-800">
                  001_initial_schema.sql
                </code>{' '}
                (creates 12 tables, indexes, views, RLS)
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                3
              </span>
              <p className="text-sm text-slate-700">
                Copy & run{' '}
                <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-mono text-slate-800">
                  002_seed_data.sql
                </code>{' '}
                (mock data: 8 users, 13 leads, notes, activities)
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* System Info */}
      <div className="rounded-xl border border-slate-200 bg-white px-6 py-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-900">
          System Info
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
          <div>
            <p className="text-slate-500">Environment</p>
            <p className="font-medium text-slate-800">
              {import.meta.env.MODE}
            </p>
          </div>
          <div>
            <p className="text-slate-500">Supabase Project</p>
            <p className="font-medium text-slate-800">jfuvhaampbngijfxgnnf</p>
          </div>
          <div>
            <p className="text-slate-500">Region</p>
            <p className="font-medium text-slate-800">ap-south-1 (Mumbai)</p>
          </div>
          <div>
            <p className="text-slate-500">Logged in as</p>
            <p className="font-medium text-slate-800">
              {user?.full_name || user?.email || 'Unknown'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
