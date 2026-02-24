'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
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
  Zap,
  Brain,
  UserCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { User } from '@/lib/types'

const navItems = [
  { href: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { href: '/leads', icon: Users, label: 'Leads' },
  { href: '/briefs', icon: FileText, label: 'Briefs' },
  { href: '/intelligence', icon: Brain, label: 'Intelligence' },
  { href: '/agents', icon: UserCircle, label: 'Agents' },
  { href: '/analytics', icon: BarChart3, label: 'Analytics' },
  { href: '/alerts', icon: Bell, label: 'Alerts', showBadge: true },
]

const adminItem = { href: '/admin', icon: Settings, label: 'Admin' }
const settingsItem = { href: '/settings', icon: Wrench, label: 'Settings' }
const adminRoles = new Set(['manager', 'founder', 'admin'])

function getRoleBadgeColor(role: string): string {
  switch (role) {
    case 'founder':
      return 'bg-violet-500/20 text-violet-400'
    case 'admin':
      return 'bg-rose-500/20 text-rose-400'
    case 'manager':
      return 'bg-fuchsia-500/20 text-fuchsia-400'
    case 'team_lead':
      return 'bg-emerald-500/20 text-emerald-400'
    default:
      return 'bg-zinc-500/20 text-zinc-400'
  }
}

interface SidebarProps {
  user: User | null
  unreadAlerts: number
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ user, unreadAlerts, collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname()
  const showAdmin = user && adminRoles.has(user.role)
  const displayName = user?.full_name || user?.name || user?.email || 'User'
  const initials = displayName.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-violet-500/10 bg-[#0f0a1f] transition-all duration-300',
        collapsed ? 'w-[72px]' : 'w-64'
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-violet-500/10 px-4">
        {!collapsed && (
          <Link href="/" className="flex items-center gap-2">
            <div className="glow-logo flex h-9 w-9 items-center justify-center rounded-lg bg-violet-500/20 text-violet-400">
              <Zap className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold tracking-tight text-white">ONSITE</span>
          </Link>
        )}
        {collapsed && (
          <Link href="/" className="glow-logo mx-auto flex h-9 w-9 items-center justify-center rounded-lg bg-violet-500/20 text-violet-400">
            <Zap className="h-5 w-5" />
          </Link>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = item.end ? pathname === item.href : pathname.startsWith(item.href)
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                    isActive
                      ? 'glow-active bg-violet-500/10 text-violet-400'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-white',
                    collapsed && 'justify-center'
                  )}
                >
                  <div className="relative shrink-0">
                    <item.icon className="h-5 w-5" />
                    {item.showBadge && unreadAlerts > 0 && (
                      <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
                        {unreadAlerts > 99 ? '99+' : unreadAlerts}
                      </span>
                    )}
                  </div>
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              </li>
            )
          })}
          {showAdmin && (
            <>
              <li>
                <Link
                  href={adminItem.href}
                  className={cn(
                    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-400 transition-all hover:bg-white/5 hover:text-white',
                    pathname === adminItem.href && 'glow-active bg-violet-500/10 text-violet-400',
                    collapsed && 'justify-center'
                  )}
                >
                  <adminItem.icon className="h-5 w-5" />
                  {!collapsed && <span>{adminItem.label}</span>}
                </Link>
              </li>
              <li>
                <Link
                  href={settingsItem.href}
                  className={cn(
                    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-400 transition-all hover:bg-white/5 hover:text-white',
                    pathname === settingsItem.href && 'glow-active bg-violet-500/10 text-violet-400',
                    collapsed && 'justify-center'
                  )}
                >
                  <settingsItem.icon className="h-5 w-5" />
                  {!collapsed && <span>{settingsItem.label}</span>}
                </Link>
              </li>
            </>
          )}
        </ul>
      </nav>

      {user && (
        <div className={cn('border-t border-violet-500/10 p-4', collapsed ? 'p-2' : '')}>
          {!collapsed ? (
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-violet-500/20 text-sm font-semibold text-violet-400">
                {initials}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-white">{displayName}</p>
                <span className={cn('inline-block rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide', getRoleBadgeColor(user.role))}>
                  {user.role.replace('_', ' ')}
                </span>
              </div>
            </div>
          ) : (
            <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-violet-500/20 text-sm font-semibold text-violet-400">
              {initials}
            </div>
          )}
        </div>
      )}

      <div className="border-t border-violet-500/10 p-2">
        <button
          onClick={onToggle}
          className="flex w-full items-center justify-center rounded-lg py-2.5 text-zinc-500 transition-colors hover:bg-white/5 hover:text-zinc-300"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
      </div>
    </aside>
  )
}
