import { Link, useParams } from 'react-router-dom'

import { useSessionSummary } from '../api/hooks'
import { buttonClasses } from '../components/Button'
import { Card } from '../components/Card'
import { ErrorMessage, Loading } from '../components/Feedback'

function Tally({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 text-center">
      <div className={`text-2xl font-semibold ${tone}`}>{value}</div>
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  )
}

export function SessionSummaryPage() {
  const { sessionId = '' } = useParams()
  const summary = useSessionSummary(sessionId)

  if (summary.isPending) {
    return <Loading label="Tallying your answers" />
  }

  if (summary.isError) {
    return <ErrorMessage error={summary.error} />
  }

  const { answered, total_questions, correct, incorrect, skipped, accuracy } = summary.data
  const graded = correct + incorrect

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Session complete</h1>
        <p className="mt-1 text-sm text-slate-400">
          {answered} of {total_questions} questions answered
        </p>
      </div>

      <Card>
        <p className="text-center text-5xl font-semibold text-slate-100">
          {graded ? `${Math.round(accuracy * 100)}%` : '—'}
        </p>
        <p className="mt-2 text-center text-sm text-slate-400">
          {graded ? `${correct} of ${graded} graded answers correct` : 'Nothing graded yet'}
        </p>

        <div className="mt-6 grid grid-cols-3 gap-3">
          <Tally label="Correct" value={correct} tone="text-emerald-400" />
          <Tally label="Missed" value={incorrect} tone="text-rose-400" />
          <Tally label="Skipped" value={skipped} tone="text-slate-300" />
        </div>
      </Card>

      <div className="flex flex-wrap gap-3">
        <Link to="/review-guide" className={buttonClasses('primary')}>
          Review what you missed
        </Link>
        <Link to="/study" className={buttonClasses('secondary')}>
          Study again
        </Link>
        <Link to="/" className={buttonClasses('ghost')}>
          Back to dashboard
        </Link>
      </div>
    </div>
  )
}
