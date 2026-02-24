'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { LogIn, Zap } from 'lucide-react'

export default function LoginPage() {
  const { signIn, session, loading } = useAuth()
  const router = useRouter()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!loading && session) {
      router.replace('/')
    }
  }, [loading, session, router])

  if (loading || session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-amber-500 border-t-transparent" />
      </div>
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password.')
      return
    }
    setSubmitting(true)
    try {
      const { error: signInError } = await signIn(email.trim(), password)
      if (signInError) {
        setError(signInError)
      } else {
        router.replace('/')
      }
    } catch {
      setError('An unexpected error occurred. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-zinc-900 via-zinc-950 to-zinc-900 px-4">
      <div className="absolute inset-0 bg-grid-pattern opacity-50" />

      <div className="relative w-full max-w-md">
        <div className="rounded-2xl border border-white/10 bg-zinc-900/90 px-8 py-10 shadow-2xl backdrop-blur">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400">
              <Zap className="h-8 w-8" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">ONSITE</h1>
            <p className="mt-2 text-sm text-zinc-400">Sales Intelligence</p>
          </div>

          {error && (
            <div className="mb-6 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-zinc-300">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@onsite.com"
                autoComplete="email"
                autoFocus
                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-zinc-300">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-amber-500/50 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-amber-500 px-4 py-2.5 text-sm font-semibold text-zinc-900 transition-colors hover:bg-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 focus:ring-offset-zinc-900 disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-900 border-t-transparent" />
                  Signing in...
                </>
              ) : (
                <>
                  <LogIn className="h-4 w-4" />
                  Sign In
                </>
              )}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-zinc-500">
          Onsite Sales Intelligence — Construction SaaS
        </p>
      </div>
    </div>
  )
}
