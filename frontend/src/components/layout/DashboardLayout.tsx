import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { getUnreadCount } from '../../lib/api'
import Sidebar from './Sidebar'
import Header from './Header'

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/leads': 'Leads',
  '/briefs': 'Daily Briefs',
  '/analytics': 'Analytics',
  '/alerts': 'Alerts',
  '/admin': 'Admin',
}

export default function DashboardLayout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [unreadAlerts, setUnreadAlerts] = useState(0)

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await getUnreadCount()
      setUnreadAlerts(res.data?.count ?? res.data?.unread_count ?? 0)
    } catch {
      // Silently fail - alerts count is non-critical
    }
  }, [])

  useEffect(() => {
    fetchUnreadCount()
    // Poll every 60 seconds for new alerts
    const interval = setInterval(fetchUnreadCount, 60_000)
    return () => clearInterval(interval)
  }, [fetchUnreadCount])

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileSidebarOpen(false)
  }, [location.pathname])

  async function handleSignOut() {
    await signOut()
    navigate('/login')
  }

  function handleSearch(query: string) {
    if (query.trim()) {
      navigate(`/leads?search=${encodeURIComponent(query.trim())}`)
    }
  }

  // Determine page title from current path
  const basePath = '/' + (location.pathname.split('/')[1] || '')
  const pageTitle =
    pageTitles[basePath] ||
    (location.pathname.startsWith('/leads/') ? 'Lead Detail' : 'Dashboard')

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile overlay */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar - desktop */}
      <div className="hidden lg:block">
        <Sidebar
          user={user}
          unreadAlerts={unreadAlerts}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* Sidebar - mobile (overlay) */}
      <div
        className={`lg:hidden ${
          mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } fixed left-0 top-0 z-40 transition-transform duration-300`}
      >
        <Sidebar
          user={user}
          unreadAlerts={unreadAlerts}
          collapsed={false}
          onToggle={() => setMobileSidebarOpen(false)}
        />
      </div>

      {/* Main content area */}
      <div
        className={`transition-all duration-300 ${
          sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'
        }`}
      >
        {/* Header */}
        <Header
          title={pageTitle}
          onSearch={handleSearch}
          unreadAlerts={unreadAlerts}
          user={user}
          onSignOut={handleSignOut}
        />

        {/* Mobile menu button */}
        <button
          className="fixed left-4 top-4 z-50 rounded-lg bg-white p-2 shadow-md lg:hidden"
          onClick={() => setMobileSidebarOpen(true)}
          aria-label="Open menu"
        >
          <svg className="h-5 w-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
