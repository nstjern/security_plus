import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { describeError } from '../api/errors'
import { useCatalog, useCreateSession, useMissedQuestions } from '../api/hooks'
import type { MissedScope, StudyMode } from '../api/types'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card, CardHeading } from '../components/Card'
import { ErrorMessage, Loading } from '../components/Feedback'
import { SelectField, TextField } from '../components/Field'

interface ModeOption {
  value: StudyMode
  label: string
  description: string
  /** Which catalog list supplies the filter value, when the mode needs one. */
  source?: 'domains' | 'chapters' | 'subjects' | 'objectives'
}

const MODES: ModeOption[] = [
  { value: 'all', label: 'Everything', description: 'All 136 questions in a random order' },
  {
    value: 'practice',
    label: 'Practice quiz',
    description: 'A random sample of the size you choose',
  },
  {
    value: 'domain',
    label: 'One domain',
    description: 'Focus on a single exam domain',
    source: 'domains',
  },
  {
    value: 'chapter',
    label: 'One chapter',
    description: 'Focus on a single chapter',
    source: 'chapters',
  },
  {
    value: 'subject',
    label: 'One subject',
    description: 'Narrow to a single subject',
    source: 'subjects',
  },
  {
    value: 'objective',
    label: 'One objective',
    description: 'Narrow to a single exam objective',
    source: 'objectives',
  },
  {
    value: 'missed',
    label: 'Questions you missed',
    description: 'Revisit questions you have answered incorrectly',
  },
]

function isValidMode(value: string | null): value is StudyMode {
  return MODES.some((mode) => mode.value === value)
}

export function StartSessionPage() {
  const [searchParams] = useSearchParams()
  const requestedMode = searchParams.get('mode')

  const [mode, setMode] = useState<StudyMode>(
    isValidMode(requestedMode) ? requestedMode : 'practice',
  )
  const [filterValue, setFilterValue] = useState('')
  // Held as text so clearing the field leaves it empty instead of snapping to zero.
  const [count, setCount] = useState('20')
  const [shuffleAnswers, setShuffleAnswers] = useState(true)
  const [missedScope, setMissedScope] = useState<MissedScope>('all')

  const catalog = useCatalog()
  const missed = useMissedQuestions()
  const createSession = useCreateSession()
  const navigate = useNavigate()

  const selected = MODES.find((option) => option.value === mode)
  const options = selected?.source ? (catalog.data?.[selected.source] ?? []) : []

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    // An empty or nonsensical count is sent as null, which the API answers with its own
    // default rather than a validation error.
    const requestedCount = Number.parseInt(count, 10)
    createSession.mutate(
      {
        mode,
        filter_value: selected?.source ? filterValue : null,
        missed_scope: mode === 'missed' ? missedScope : 'all',
        count: mode === 'practice' && requestedCount > 0 ? requestedCount : null,
        shuffle_answers: shuffleAnswers,
        shuffle_questions: true,
      },
      { onSuccess: (session) => void navigate(`/sessions/${session.id}`) },
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Start a session</h1>
        <p className="mt-1 text-sm text-slate-400">
          Answers are graded as you go, and every result feeds your review guide.
        </p>
      </div>

      {catalog.isPending ? <Loading label="Loading study options" /> : null}
      {catalog.isError ? <ErrorMessage error={catalog.error} /> : null}

      {catalog.data ? (
        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeading title="What do you want to work on?" />
            <fieldset className="space-y-2">
              <legend className="sr-only">Study mode</legend>
              {MODES.map((option) => {
                const unavailable = option.value === 'missed' && missed.data?.all.count === 0
                return (
                  // The rule only recognises literal label text; this one comes from MODES.
                  // oxlint-disable-next-line jsx-a11y/label-has-associated-control
                  <label
                    key={option.value}
                    htmlFor={`mode-${option.value}`}
                    className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                      mode === option.value
                        ? 'border-brand-500 bg-slate-900'
                        : 'border-slate-800 hover:border-slate-700'
                    } ${unavailable ? 'opacity-50' : ''}`}
                  >
                    <input
                      id={`mode-${option.value}`}
                      type="radio"
                      name="mode"
                      value={option.value}
                      checked={mode === option.value}
                      disabled={unavailable}
                      onChange={() => {
                        setMode(option.value)
                        setFilterValue('')
                        if (option.value === 'missed') {
                          setMissedScope('all')
                        }
                      }}
                      className="mt-1"
                    />
                    <span>
                      <span className="block text-sm font-medium text-slate-100">
                        {option.label}
                      </span>
                      <span className="block text-xs text-slate-400">
                        {unavailable ? 'You have not missed any questions yet' : option.description}
                      </span>
                    </span>
                  </label>
                )
              })}
            </fieldset>
          </Card>

          <Card>
            <CardHeading title="Options" />
            <div className="space-y-4">
              {selected?.source ? (
                <SelectField
                  label={selected.label}
                  required
                  value={filterValue}
                  onChange={(event) => setFilterValue(event.target.value)}
                >
                  <option value="">Choose one…</option>
                  {options.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </SelectField>
              ) : null}

              {mode === 'missed' && missed.data ? (
                <fieldset className="space-y-2">
                  <legend className="text-sm font-medium text-slate-200">
                    Which missed questions?
                  </legend>
                  {(
                    [
                      {
                        value: 'all' as const,
                        label: 'All questions you have ever missed',
                        count: missed.data.all.count,
                      },
                      {
                        value: 'unresolved' as const,
                        label: 'Only questions not yet answered correctly',
                        count: missed.data.unresolved.count,
                      },
                    ] as const
                  ).map((option) => {
                    const unavailable = option.count === 0
                    return (
                      // oxlint-disable-next-line jsx-a11y/label-has-associated-control
                      <label
                        key={option.value}
                        htmlFor={`missed-scope-${option.value}`}
                        className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                          missedScope === option.value
                            ? 'border-brand-500 bg-slate-900'
                            : 'border-slate-800 hover:border-slate-700'
                        } ${unavailable ? 'opacity-50' : ''}`}
                      >
                        <input
                          id={`missed-scope-${option.value}`}
                          type="radio"
                          name="missed-scope"
                          value={option.value}
                          checked={missedScope === option.value}
                          disabled={unavailable}
                          onChange={() => setMissedScope(option.value)}
                          className="mt-1"
                        />
                        <span>
                          <span className="block text-sm font-medium text-slate-100">
                            {option.label}
                          </span>
                          <span className="block text-xs text-slate-400">
                            {unavailable
                              ? 'Nothing in this group right now'
                              : `${option.count} question${option.count === 1 ? '' : 's'}`}
                          </span>
                        </span>
                      </label>
                    )
                  })}
                </fieldset>
              ) : null}

              {mode === 'practice' ? (
                <TextField
                  label="How many questions"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={136}
                  value={count}
                  onChange={(event) => setCount(event.target.value)}
                />
              ) : null}

              <label className="flex items-center gap-3 text-sm text-slate-200">
                <input
                  type="checkbox"
                  checked={shuffleAnswers}
                  onChange={(event) => setShuffleAnswers(event.target.checked)}
                />
                Shuffle the answer choices
              </label>
            </div>
          </Card>

          {createSession.isError ? (
            <Alert tone="error">{describeError(createSession.error)}</Alert>
          ) : null}

          <Button type="submit" disabled={createSession.isPending} className="w-full">
            {createSession.isPending ? 'Preparing…' : 'Begin'}
          </Button>
        </form>
      ) : null}
    </div>
  )
}
