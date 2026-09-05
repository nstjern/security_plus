import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { useReviewGuide } from '../api/hooks'
import type { FocusArea } from '../api/types'
import { buttonClasses } from '../components/Button'
import { Card, CardHeading } from '../components/Card'
import { EmptyState, ErrorMessage, Loading } from '../components/Feedback'
import { MissedBar } from '../components/MissedBar'

function filterFocusAreas(
  areas: FocusArea[],
  selectedDomain: string | null,
  selectedSubject: string | null,
): FocusArea[] {
  if (selectedSubject !== null) {
    return areas.filter((area) => area.subject === selectedSubject)
  }
  if (selectedDomain !== null) {
    return areas.filter((area) => area.domain === selectedDomain)
  }
  return areas
}

function resolveSelectedSubject(
  requestedSubject: string | null,
  focusAreas: FocusArea[],
): string | null {
  if (!requestedSubject) {
    return null
  }

  const knownSubjects = new Set(focusAreas.map((area) => area.subject))
  return knownSubjects.has(requestedSubject) ? requestedSubject : null
}

function resolveSelectedDomain(
  requestedDomain: string | null,
  priorityDomains: { domain: string }[],
  focusAreas: FocusArea[],
): string | null {
  if (!requestedDomain) {
    return null
  }

  const knownDomains = new Set([
    ...priorityDomains.map((domain) => domain.domain),
    ...focusAreas.map((area) => area.domain),
  ])
  return knownDomains.has(requestedDomain) ? requestedDomain : null
}

export function ReviewGuidePage() {
  const guide = useReviewGuide()
  const [searchParams, setSearchParams] = useSearchParams()

  const focusAreas = guide.data?.focus_areas
  const priorityDomains = guide.data?.priority_domains
  const selectedDomain = useMemo(
    () =>
      resolveSelectedDomain(searchParams.get('domain'), priorityDomains ?? [], focusAreas ?? []),
    [searchParams, focusAreas, priorityDomains],
  )
  const selectedSubject = useMemo(
    () => resolveSelectedSubject(searchParams.get('subject'), focusAreas ?? []),
    [searchParams, focusAreas],
  )

  if (guide.isPending) {
    return <Loading label="Building your review guide" />
  }

  if (guide.isError) {
    return <ErrorMessage error={guide.error} />
  }

  const visibleFocusAreas = filterFocusAreas(focusAreas ?? [], selectedDomain, selectedSubject)
  const totalIncorrect = guide.data.total_incorrect
  const maxMissed = Math.max(...(priorityDomains ?? []).map((domain) => domain.incorrect), 0)

  function toggleDomainFilter(domain: string) {
    const next = selectedDomain === domain && selectedSubject === null ? null : domain
    setSearchParams(next ? { domain: next } : {}, { replace: true })
  }

  const filterDescription = selectedSubject
    ? `Showing ${selectedSubject}. Click a domain below to filter by domain instead.`
    : selectedDomain
      ? `Showing subjects in ${selectedDomain}. Click the domain again to show all.`
      : `${totalIncorrect} missed answers across ${(priorityDomains ?? []).length} domains`

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Your review guide</h1>
        <p className="mt-1 text-sm text-slate-400">
          Grouped by exam domain. Each subject includes a weakness score that reflects how often and
          how consistently you missed it.
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
          {priorityDomains && priorityDomains.length > 0 ? (
            <Card>
              <CardHeading title="Where to spend your time" description={filterDescription} />
              <ul className="grid grid-cols-[auto_1fr_auto] gap-x-3 gap-y-1 text-sm">
                {priorityDomains.map((domain) => {
                  const isSelected = selectedDomain === domain.domain && selectedSubject === null

                  return (
                    <li key={domain.domain} className="col-span-3 grid grid-cols-subgrid">
                      <button
                        type="button"
                        aria-pressed={isSelected}
                        onClick={() => toggleDomainFilter(domain.domain)}
                        className={`col-span-3 grid grid-cols-subgrid items-baseline rounded-lg px-2 py-1.5 text-left transition-colors ${
                          isSelected
                            ? 'bg-slate-800 ring-1 ring-brand-500'
                            : 'hover:bg-slate-800/50'
                        }`}
                      >
                        <span className="text-slate-100">{domain.domain}</span>
                        <MissedBar missed={domain.incorrect} maxMissed={maxMissed} />
                        <span className="shrink-0 text-slate-400">{domain.incorrect} missed</span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </Card>
          ) : null}

          <div className="space-y-6">
            {visibleFocusAreas.map((area) => {
              const chapterSections = [
                ...new Set(
                  (area.concepts ?? []).map(
                    (concept) => `${concept.chapter} - ${concept.objective}`,
                  ),
                ),
              ]

              return (
                <Card key={`${area.domain}-${area.subject}`}>
                  <div className="mb-4">
                    <h2 className="text-lg font-semibold text-slate-100">{area.subject}</h2>
                    <p className="mt-1 text-sm text-slate-400">{area.domain}</p>
                    {chapterSections.map((section) => (
                      <p key={section} className="mt-1 text-sm text-slate-400">
                        {section}
                      </p>
                    ))}
                    <p className="mt-1 text-sm text-slate-500">
                      missed {area.incorrect} of {area.correct + area.incorrect} · weakness score{' '}
                      {area.weakness_score.toFixed(1)}
                    </p>
                  </div>
                  <ul className="space-y-5">
                    {(area.concepts ?? []).map((concept) => (
                      <li key={concept.question_id} className="border-t border-slate-800 pt-4">
                        <p className="text-sm font-medium text-slate-100">
                          {concept.correct_choice}
                        </p>
                        <p className="mt-2 text-sm leading-relaxed text-slate-300">
                          {concept.explanation}
                        </p>
                      </li>
                    ))}
                  </ul>
                </Card>
              )
            })}
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
