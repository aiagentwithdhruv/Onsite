'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Search, Bell, ChevronDown, User as UserIcon, LogOut, Menu, Sun, Moon } from 'lucide-react'
import { useTheme } from '@/lib/useTheme'
import type { User } from '@/lib/types'

interface HeaderProps {
  title: string
  onSearch: (query: string) => void
  unreadAlerts: number
  user: User | null
  onSignOut: () => void
  onMobileMenuOpen?: () => void
}

export default function Header({ title, onSearch, unreadAlerts, user, onSignOut, onMobileMenuOpen }: HeaderProps) {
  const router = useRouter()
  const { theme, toggle: toggleTheme } = useTheme()
  const [searchValue, setSearchValue] = useState('')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const displayName = user?.full_name || user?.name || user?.email || 'User'

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSearch(searchValue)
  }

  const initials = user
    ? displayName.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : '?'

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-zinc-200/80 bg-white/80 px-4 backdrop-blur-sm sm:px-6 dark:border-violet-500/10 dark:bg-zinc-900/80">
      <div className="flex items-center gap-3">
        {onMobileMenuOpen && (
          <button
            type="button"
            className="rounded-lg p-2 text-zinc-500 transition-colors hover:bg-zinc-100 lg:hidden dark:text-zinc-400 dark:hover:bg-white/5"
            onClick={onMobileMenuOpen}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-white">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        <form onSubmit={handleSearchSubmit} className="relative hidden sm:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <input
            type="text"
            placeholder="Search leads, companies..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            className="h-9 w-64 rounded-lg border border-zinc-200 bg-zinc-50 pl-9 pr-3 text-sm text-zinc-800 placeholder:text-zinc-400 transition-colors focus:border-violet-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-violet-500/20 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
          />
        </form>

        <button
          type="button"
          onClick={toggleTheme}
          className="rounded-lg p-2 text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-white/5 dark:hover:text-zinc-300"
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>

        <Link
          href="/alerts"
          className="relative rounded-lg p-2 text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-white/5 dark:hover:text-zinc-300"
          aria-label="Alerts"
        >
          <Bell className="h-5 w-5" />
          {unreadAlerts > 0 && (
            <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
              {unreadAlerts > 99 ? '99+' : unreadAlerts}
            </span>
          )}
        </Link>

        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-lg p-1.5 transition-colors hover:bg-zinc-100 dark:hover:bg-white/5"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-500/20 text-xs font-semibold text-violet-600 dark:text-violet-400">
              {initials}
            </div>
            {user && (
              <div className="hidden items-center gap-1 md:flex">
                <span className="text-sm font-medium text-zinc-700 dark:text-zinc-200">{displayName}</span>
                <ChevronDown className="h-4 w-4 text-zinc-400" />
              </div>
            )}
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 top-full z-50 mt-1 w-48 rounded-xl border border-zinc-200 bg-white py-1 shadow-xl dark:border-zinc-700 dark:bg-zinc-800">
              {user && (
                <div className="border-b border-zinc-100 px-4 py-2 dark:border-zinc-700">
                  <p className="text-sm font-medium text-zinc-900 dark:text-white">{displayName}</p>
                  <p className="text-xs capitalize text-zinc-500 dark:text-zinc-400">{user.role.replace('_', ' ')}</p>
                </div>
              )}
              <button
                onClick={() => setDropdownOpen(false)}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-zinc-600 transition-colors hover:bg-zinc-50 dark:text-zinc-300 dark:hover:bg-zinc-700/50"
              >
                <UserIcon className="h-4 w-4" />
                Profile
              </button>
              <button
                onClick={() => {
                  setDropdownOpen(false)
                  onSignOut()
                }}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-rose-600 transition-colors hover:bg-rose-50 dark:hover:bg-rose-500/10"
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
