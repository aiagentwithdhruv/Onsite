import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  FileText,
  BarChart3,
  Bell,
  Settings,
  Wrench,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import type { User } from '../../lib/types'

interface SidebarProps {
  user: User | null
  unreadAlerts: number
  collapsed: boolean
  onToggle: () => void
}

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/leads', icon: Users, label: 'Leads' },
  { to: '/briefs', icon: FileText, label: 'Briefs' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/alerts', icon: Bell, label: 'Alerts', showBadge: true },
]

const adminItem = { to: '/admin', icon: Settings, label: 'Admin' }
const settingsItem = { to: '/settings', icon: Wrench, label: 'Settings' }

const adminRoles = new Set(['manager', 'founder', 'admin'])

function getRoleBadgeColor(role: string): string {
  switch (role) {
    case 'founder':
      return 'bg-purple-100 text-purple-700'
    case 'admin':
      return 'bg-red-100 text-red-700'
    case 'manager':
      return 'bg-blue-100 text-blue-700'
    case 'team_lead':
      return 'bg-teal-100 text-teal-700'
    default:
      return 'bg-slate-100 text-slate-700'
  }
}

export default function Sidebar({ user, unreadAlerts, collapsed, onToggle }: SidebarProps) {
  const showAdmin = user && adminRoles.has(user.role)
  const displayName = user?.full_name || user?.name || user?.email || 'User'
  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  return (
    <aside
      className={`fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-slate-200 bg-white transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between border-b border-slate-200 px-4">
        {!collapsed && (
          <span className="text-xl font-bold tracking-wide text-blue-600">ONSITE</span>
        )}
        {collapsed && (
          <span className="mx-auto text-lg font-bold text-blue-600">O</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-l-4 border-blue-600 bg-blue-50 text-blue-700'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  } ${collapsed ? 'justify-center' : ''}`
                }
              >
                <div className="relative flex-shrink-0">
                  <item.icon className="h-5 w-5" />
                  {item.showBadge && unreadAlerts > 0 && (
                    <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                      {unreadAlerts > 99 ? '99+' : unreadAlerts}
                    </span>
                  )}
                </div>
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            </li>
          ))}

          {showAdmin && (
            <>
              <li>
                <NavLink
                  to={adminItem.to}
                  className={({ isActive }) =>
                    `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                      isActive
                        ? 'border-l-4 border-blue-600 bg-blue-50 text-blue-700'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    } ${collapsed ? 'justify-center' : ''}`
                  }
                >
                  <adminItem.icon className="h-5 w-5" />
                  {!collapsed && <span>{adminItem.label}</span>}
                </NavLink>
              </li>
              <li>
                <NavLink
                  to={settingsItem.to}
                  className={({ isActive }) =>
                    `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                      isActive
                        ? 'border-l-4 border-blue-600 bg-blue-50 text-blue-700'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    } ${collapsed ? 'justify-center' : ''}`
                  }
                >
                  <settingsItem.icon className="h-5 w-5" />
                  {!collapsed && <span>{settingsItem.label}</span>}
                </NavLink>
              </li>
            </>
          )}
        </ul>
      </nav>

      {/* User info */}
      {user && !collapsed && (
        <div className="border-t border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-900">{displayName}</p>
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${getRoleBadgeColor(
                  user.role
                )}`}
              >
                {user.role.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>
      )}

      {user && collapsed && (
        <div className="border-t border-slate-200 p-2">
          <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">
            {initials}
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <div className="border-t border-slate-200 p-2">
        <button
          onClick={onToggle}
          className="flex w-full items-center justify-center rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
      </div>
    </aside>
  )
}
