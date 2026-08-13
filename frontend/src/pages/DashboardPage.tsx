import { Link } from 'react-router-dom'

import { useMissedQuestions, useProgressSummary, useWeakestSubjects } from '../api/hooks'
import { AccuracyBar } from '../components/AccuracyBar'
import { buttonClasses } from '../components/Button'
import { Card, CardHeading } from '../components/Card'
import { EmptyState, ErrorMessage, Loading } from '../components/Feedback'

function percent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function Statistic({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3">
      <div className="text-2xl font-semibold text-slate-100">{value}</div>
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  )
}

export function DashboardPage() {
  const summary = useProgressSummary()
  const subjects = useWeakestSubjects(5)
  const missed = useMissedQuestions()

  if (summary.isPending) {
    return <Loading label="Loading your progress" />
  }

  if (summary.isError) {
    return <ErrorMessage error={summary.error} />
  }

  const { attempts, correct, incorrect, skipped, graded, accuracy, domains } = summary.data

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Your progress</h1>
          <p className="mt-1 text-sm text-slate-400">
            Accuracy counts graded answers only; skipped questions are tracked separately.
          </p>
        </div>
        <Link to="/study" className={buttonClasses('primary', 'shrink-0')}>
          Start studying
        </Link>
      </div>

      {attempts === 0 ? (
        <EmptyState title="No answers recorded yet">
          <p>
            Start a session and your accuracy, weakest subjects, and review guide will build
            themselves.
          </p>
          <Link
            to="/study"
            className="mt-4 inline-block font-medium text-brand-300 underline underline-offset-4"
          >
            Start your first session
          </Link>
        </EmptyState>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Statistic label="Answered" value={String(attempts)} />
            <Statistic label="Accuracy" value={graded ? percent(accuracy) : '—'} />
            <Statistic label="Correct" value={String(correct)} />
            <Statistic label="Missed" value={String(incorrect)} />
          </div>

          <Card>
            <CardHeading
              title="Accuracy by domain"
              description={`${graded} graded, ${skipped} skipped`}
            />
            <div className="space-y-4">
              {domains.map((domain) => (
                <AccuracyBar
                  key={domain.name}
                  label={domain.name}
                  accuracy={domain.accuracy}
                  detail={`${domain.correct}/${domain.graded}`}
                />
              ))}
            </div>
          </Card>

          <Card>
            <CardHeading
              title="Weakest subjects"
              description="Ranked by accuracy across everything you have answered"
            />
            {subjects.isPending ? <Loading /> : null}
            {subjects.isError ? <ErrorMessage error={subjects.error} /> : null}
            {subjects.data?.length === 0 ? (
              <p className="text-sm text-slate-400">Nothing stands out yet.</p>
            ) : null}
            <ul className="space-y-4">
              {subjects.data?.map((subject) => (
                <li key={subject.name}>
                  <AccuracyBar
                    label={subject.name}
                    accuracy={subject.accuracy}
                    detail={`${subject.correct}/${subject.graded}`}
                  />
                </li>
              ))}
            </ul>
          </Card>

          {missed.data && missed.data.count > 0 ? (
            <Card>
              <CardHeading
                title="Questions you have missed"
                description={`${missed.data.count} to revisit`}
                action={
                  <Link
                    to="/study?mode=missed"
                    className="text-sm font-medium text-brand-300 underline underline-offset-4"
                  >
                    Practice these
                  </Link>
                }
              />
            </Card>
          ) : null}
        </>
      )}
    </div>
  )
}
