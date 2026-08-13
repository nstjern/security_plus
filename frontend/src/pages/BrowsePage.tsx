import { useState } from 'react'

import { useCatalog, useQuestions } from '../api/hooks'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { EmptyState, ErrorMessage, Loading } from '../components/Feedback'
import { SelectField } from '../components/Field'

const PAGE_SIZE = 10

export function BrowsePage() {
  const [domain, setDomain] = useState('')
  const [subject, setSubject] = useState('')
  const [offset, setOffset] = useState(0)

  const catalog = useCatalog()
  const questions = useQuestions({
    domain: domain || undefined,
    subject: subject || undefined,
    limit: PAGE_SIZE,
    offset,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Browse the question bank</h1>
        <p className="mt-1 text-sm text-slate-400">
          Answers and explanations are not shown here. Start a session to have one graded.
        </p>
      </div>

      <Card>
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField
            label="Domain"
            value={domain}
            onChange={(event) => {
              setDomain(event.target.value)
              setOffset(0)
            }}
          >
            <option value="">All domains</option>
            {catalog.data?.domains.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </SelectField>

          <SelectField
            label="Subject"
            value={subject}
            onChange={(event) => {
              setSubject(event.target.value)
              setOffset(0)
            }}
          >
            <option value="">All subjects</option>
            {catalog.data?.subjects.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </SelectField>
        </div>
      </Card>

      {questions.isPending ? <Loading label="Loading questions" /> : null}
      {questions.isError ? <ErrorMessage error={questions.error} /> : null}

      {questions.data ? (
        questions.data.total === 0 ? (
          <EmptyState title="No questions match those filters" />
        ) : (
          <>
            <p className="text-sm text-slate-400">
              Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, questions.data.total)} of{' '}
              {questions.data.total}
            </p>

            <ul className="space-y-3">
              {questions.data.items.map((item) => (
                <li key={item.id}>
                  <Card>
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      {item.domain} · {item.subject}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-slate-100">{item.question}</p>
                  </Card>
                </li>
              ))}
            </ul>

            <div className="flex items-center justify-between gap-3">
              <Button
                variant="secondary"
                disabled={offset === 0}
                onClick={() => setOffset((current) => Math.max(0, current - PAGE_SIZE))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                disabled={offset + PAGE_SIZE >= questions.data.total}
                onClick={() => setOffset((current) => current + PAGE_SIZE)}
              >
                Next
              </Button>
            </div>
          </>
        )
      ) : null}
    </div>
  )
}
