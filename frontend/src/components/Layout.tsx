import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'

import { useSignOut } from '../api/hooks'
import { useAuth } from '../auth/context'
import { Button } from './Button'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/study', label: 'Study' },
  { to: '/review-guide', label: 'Review guide' },
  { to: '/questions', label: 'Browse' },
]

function navLinkClasses({ isActive }: { isActive: boolean }): string {
  return `rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
    isActive ? 'bg-slate-800 text-slate-100' : 'text-slate-400 hover:text-slate-100'
  }`
}

export function Layout({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const signOut = useSignOut()
  const navigate = useNavigate()

  return (
    <div className="min-h-full">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:rounded-lg focus:bg-slate-800 focus:px-3 focus:py-2"
      >
        Skip to content
      </a>

      <header className="border-b border-slate-800 bg-slate-900/50">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-4 px-4 py-3">
          <span className="font-semibold tracking-tight text-slate-100">Security+ Study</span>

          {user ? (
            <nav aria-label="Main" className="flex flex-wrap items-center gap-1">
              {NAV_ITEMS.map((item) => (
                <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClasses}>
                  {item.label}
                </NavLink>
              ))}
            </nav>
          ) : null}

          {user ? (
            <div className="ml-auto flex items-center gap-3">
              <span className="text-sm text-slate-400">{user.username}</span>
              <Button
                variant="ghost"
                disabled={signOut.isPending}
                onClick={() => {
                  signOut.mutate(undefined, { onSettled: () => void navigate('/sign-in') })
                }}
              >
                Sign out
              </Button>
            </div>
          ) : null}
        </div>
      </header>

      <main id="main" className="mx-auto max-w-5xl px-4 py-8">
        {children}
      </main>
    </div>
  )
}
