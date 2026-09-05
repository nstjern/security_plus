interface MissedBarProps {
  missed: number
  /** The largest miss count in the list, used to scale bar width. */
  maxMissed: number
}

/** The red fill that sits between a domain label and its missed count. */
export function MissedBar({ missed, maxMissed }: MissedBarProps) {
  const width = maxMissed > 0 ? Math.round((missed / maxMissed) * 100) : 0

  return (
    // Fills its grid cell so every row shares the same bar width.
    <div
      className="h-2 w-full self-center overflow-hidden rounded-full bg-slate-800"
      aria-hidden="true"
    >
      <div className="h-full rounded-full bg-rose-500" style={{ width: `${width}%` }} />
    </div>
  )
}
