interface AccuracyBarProps {
  label: string
  accuracy: number
  detail: string
}

/** Below 70% is roughly where a Security+ candidate should still be revising. */
const NEEDS_WORK = 0.7
const SOLID = 0.85

function toneFor(accuracy: number): string {
  if (accuracy >= SOLID) return 'bg-emerald-500'
  if (accuracy >= NEEDS_WORK) return 'bg-amber-500'
  return 'bg-rose-500'
}

export function AccuracyBar({ label, accuracy, detail }: AccuracyBarProps) {
  const percentage = Math.round(accuracy * 100)
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-4 text-sm">
        <span className="font-medium text-slate-200">{label}</span>
        <span className="shrink-0 text-slate-400">
          {percentage}% · {detail}
        </span>
      </div>
      {/* Decorative: the percentage and the tally above already state the same thing. */}
      <div className="h-2 overflow-hidden rounded-full bg-slate-800" aria-hidden="true">
        <div
          className={`h-full rounded-full ${toneFor(accuracy)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
