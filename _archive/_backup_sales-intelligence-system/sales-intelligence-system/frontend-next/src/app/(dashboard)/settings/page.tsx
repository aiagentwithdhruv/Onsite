'use client'

import { useAuth } from '@/contexts/AuthContext'
import { User, Mail, Shield } from 'lucide-react'

export default function SettingsPage() {
  const { user } = useAuth()
  const displayName = user?.full_name || user?.name || user?.email || 'User'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-zinc-900 dark:text-white">Settings</h2>
        <p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">
          Your account and preferences
        </p>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/50">
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
    </div>
  )
}
