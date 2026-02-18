'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { getUnreadCount } from '@/lib/api'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/leads': 'Leads',
  '/briefs': 'Daily Briefs',
  '/intelligence': 'Sales Intelligence',
  '/analytics': 'Analytics',
  '/alerts': 'Alerts',
  '/admin': 'Admin',
  '/settings': 'Settings',
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, session, loading, signOut } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [unreadAlerts, setUnreadAlerts] = useState(0)

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await getUnreadCount()
      setUnreadAlerts(res.data?.count ?? res.data?.unread_count ?? 0)
    } catch {
      // non-critical
    }
  }, [])

  useEffect(() => {
    if (!loading && !session) {
      router.replace('/login')
      return
    }
    fetchUnreadCount()
    const interval = setInterval(fetchUnreadCount, 60_000)
    return () => clearInterval(interval)
  }, [loading, session, router, fetchUnreadCount])

  useEffect(() => {
    setMobileSidebarOpen(false)
  }, [pathname])

  async function handleSignOut() {
    await signOut()
    router.replace('/login')
  }

  function handleSearch(query: string) {
    if (query.trim()) {
      router.push(`/leads?search=${encodeURIComponent(query.trim())}`)
    }
  }

  const basePath = '/' + (pathname?.split('/')[1] || '')
  const pageTitle =
    pageTitles[basePath] ||
    (pathname?.startsWith('/leads/') ? 'Lead Detail' : 'Dashboard')

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-amber-500 border-t-transparent" />
          <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Loading Onsite...</p>
        </div>
      </div>
    )
  }

  if (!session) {
    return null
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
          aria-hidden
        />
      )}

      <div className="hidden lg:block">
        <Sidebar
          user={user}
          unreadAlerts={unreadAlerts}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      <div
        className={`transition-all duration-300 ${sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-64'}`}
      >
        <div className={`lg:hidden ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed left-0 top-0 z-40 transition-transform duration-300`}>
          <Sidebar
            user={user}
            unreadAlerts={unreadAlerts}
            collapsed={false}
            onToggle={() => setMobileSidebarOpen(false)}
          />
        </div>

        <Header
          title={pageTitle}
          onSearch={handleSearch}
          unreadAlerts={unreadAlerts}
          user={user}
          onSignOut={handleSignOut}
        />

        <button
          type="button"
          className="fixed left-4 top-4 z-50 rounded-lg bg-white p-2 shadow-lg lg:hidden dark:bg-zinc-800"
          onClick={() => setMobileSidebarOpen(true)}
          aria-label="Open menu"
        >
          <svg className="h-5 w-5 text-zinc-600 dark:text-zinc-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
