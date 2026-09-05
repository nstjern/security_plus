import type { ReactNode } from 'react'

type Tone = 'error' | 'info' | 'success'

const TONES: Record<Tone, string> = {
  error: 'border-rose-800 bg-rose-950/60 text-rose-100',
  info: 'border-slate-700 bg-slate-900 text-slate-200',
  success: 'border-emerald-800 bg-emerald-950/60 text-emerald-100',
}

interface AlertProps {
  tone?: Tone
  children: ReactNode
}

export function Alert({ tone = 'info', children }: AlertProps) {
  return (
    <div
      // Assistive technology should announce failures without the user hunting for them.
      role={tone === 'error' ? 'alert' : 'status'}
      className={`rounded-lg border px-4 py-3 text-sm ${TONES[tone]}`}
    >
      {children}
    </div>
  )
}
