import { Link } from 'react-router-dom'

import { useReviewGuide } from '../api/hooks'
import { buttonClasses } from '../components/Button'
import { Card, CardHeading } from '../components/Card'
import { EmptyState, ErrorMessage, Loading } from '../components/Feedback'

export function ReviewGuidePage() {
  const guide = useReviewGuide()

  if (guide.isPending) {
    return <Loading label="Building your review guide" />
  }

  if (guide.isError) {
    return <ErrorMessage error={guide.error} />
  }

  // Collections default to empty server-side, so the contract marks them optional.
  const focusAreas = guide.data.focus_areas ?? []
  const priorityDomains = guide.data.priority_domains ?? []
  const totalIncorrect = guide.data.total_incorrect

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Your review guide</h1>
        <p className="mt-1 text-sm text-slate-400">
          Built from the questions you have missed, ranked by how often and how consistently you
          missed them.
        </p>
      </div>

      {totalIncorrect === 0 ? (
        <EmptyState title="Nothing to review yet">
          <p>Once you miss a question, the concept behind it shows up here.</p>
          <Link to="/study" className={`${buttonClasses('primary')} mt-4`}>
            Start a session
          </Link>
        </EmptyState>
      ) : (
        <>
          {priorityDomains.length > 0 ? (
            <Card>
              <CardHeading
                title="Where to spend your time"
                description={`${totalIncorrect} missed answers across ${priorityDomains.length} domains`}
              />
              <ol className="space-y-2">
                {priorityDomains.map((domain, index) => (
                  <li key={domain.domain} className="flex items-baseline gap-3 text-sm">
                    <span className="font-semibold text-brand-300">{index + 1}</span>
                    <span className="text-slate-100">{domain.domain}</span>
                    <span className="ml-auto shrink-0 text-slate-400">
                      {domain.incorrect} missed
                    </span>
                  </li>
                ))}
              </ol>
            </Card>
          ) : null}

          <div className="space-y-6">
            {focusAreas.map((area) => (
              <Card key={`${area.domain}-${area.subject}`}>
                <CardHeading
                  title={area.subject}
                  description={`${area.domain} · missed ${area.incorrect} of ${area.correct + area.incorrect}`}
                />
                <ul className="space-y-5">
                  {(area.concepts ?? []).map((concept) => (
                    <li key={concept.question_id} className="border-t border-slate-800 pt-4">
                      <p className="text-sm font-medium text-slate-100">{concept.correct_choice}</p>
                      <p className="mt-2 text-sm leading-relaxed text-slate-300">
                        {concept.explanation}
                      </p>
                      <p className="mt-2 text-xs text-slate-500">
                        {concept.chapter} · {concept.objective}
                      </p>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>

          <div className="flex flex-wrap gap-3">
            <Link to="/study?mode=missed" className={buttonClasses('primary')}>
              Practice these questions
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
