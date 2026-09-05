import type { ReactNode } from 'react'

import { describeError } from '../api/errors'
import { Alert } from './Alert'

export function Loading({ label = 'Loading' }: { label?: string }) {
  return (
    // <output> is a live region by default, so the wait is announced without a role attribute.
    <output className="flex items-center gap-3 py-8 text-sm text-slate-400">
      <span
        aria-hidden="true"
        className="size-4 animate-spin rounded-full border-2 border-slate-700 border-t-brand-400"
      />
      {label}
    </output>
  )
}

export function ErrorMessage({ error }: { error: unknown }) {
  return <Alert tone="error">{describeError(error)}</Alert>
}

interface EmptyStateProps {
  title: string
  children?: ReactNode
}

export function EmptyState({ title, children }: EmptyStateProps) {
  return (
    <div className="rounded-xl border border-dashed border-slate-800 px-6 py-10 text-center">
      <p className="font-medium text-slate-200">{title}</p>
      {children ? <div className="mt-2 text-sm text-slate-400">{children}</div> : null}
    </div>
  )
}
