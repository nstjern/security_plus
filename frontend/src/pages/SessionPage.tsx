import { useCallback, useEffect, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'

import { useCurrentQuestion, useEndSession, useSession, useSubmitAnswer } from '../api/hooks'
import type { AnswerResponse, ChoiceLetter } from '../api/types'
import { CHOICE_LETTERS } from '../api/types'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { ErrorMessage, Loading } from '../components/Feedback'

function isChoiceLetter(value: string): value is ChoiceLetter {
  return (CHOICE_LETTERS as readonly string[]).includes(value)
}

interface AnswerFeedbackProps {
  answer: AnswerResponse
  chosen: ChoiceLetter | null
  onNext: () => void
}

function AnswerFeedback({ answer, chosen, onNext }: AnswerFeedbackProps) {
  const heading =
    answer.result === 'correct' ? 'Correct' : answer.result === 'skipped' ? 'Skipped' : 'Not quite'

  return (
    // Announced politely so the outcome reaches a screen reader without stealing focus.
    <div className="space-y-4" aria-live="polite">
      <Alert tone={answer.result === 'correct' ? 'success' : 'error'}>
        <p className="font-semibold">{heading}</p>
        {answer.result === 'incorrect' && chosen ? (
          <p className="mt-1">
            You chose {chosen.toUpperCase()}. The answer is {answer.correct_choice.toUpperCase()}:{' '}
            {answer.correct_choice_text}
          </p>
        ) : (
          <p className="mt-1">
            {answer.correct_choice.toUpperCase()}: {answer.correct_choice_text}
          </p>
        )}
      </Alert>

      <Card>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Why that is the answer
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-slate-200">{answer.explanation}</p>
        {answer.correction_note ? (
          <p className="mt-3 border-t border-slate-800 pt-3 text-xs text-slate-400">
            {answer.correction_note}
          </p>
        ) : null}
      </Card>

      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={onNext}>
          {answer.next_available ? 'Next question' : 'See your results'}
        </Button>
        <span className="text-xs text-slate-500">or press Enter</span>
      </div>
    </div>
  )
}

export function SessionPage() {
  const { sessionId = '' } = useParams()
  const navigate = useNavigate()

  const [chosen, setChosen] = useState<ChoiceLetter | null>(null)
  const [answer, setAnswer] = useState<AnswerResponse | null>(null)

  const session = useSession(sessionId)
  const question = useCurrentQuestion(sessionId)
  const submitAnswer = useSubmitAnswer(sessionId)
  const endSession = useEndSession(sessionId)

  // Pulled out because these two keep the same identity across renders while the objects
  // holding them do not, which is what lets the handlers below stay memoized.
  const { mutate: submit } = submitAnswer
  const { refetch: refetchQuestion } = question

  // Both are memoized because the keyboard listener below depends on them, and a fresh
  // function on every render would tear the listener down and rebuild it just as often.
  const handleSubmit = useCallback(() => {
    submit(chosen, { onSuccess: setAnswer })
  }, [chosen, submit])

  const handleNext = useCallback(() => {
    const wasLast = answer?.next_available === false
    setAnswer(null)
    setChosen(null)
    if (wasLast) {
      void navigate(`/sessions/${sessionId}/summary`)
    } else {
      void refetchQuestion()
    }
  }, [answer, navigate, sessionId, refetchQuestion])

  // Lowercase a–d pick a choice, Enter submits, Enter again moves on. Bound to the window so
  // the shortcuts work without tabbing into the question first.
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      // A held key would race through several questions, and a browser or system shortcut is
      // never ours to intercept.
      if (event.repeat || event.ctrlKey || event.metaKey || event.altKey) {
        return
      }

      const insideButtonOrLink =
        event.target instanceof HTMLElement && event.target.closest('a, button') !== null

      if (answer !== null) {
        if (event.key === 'Enter') {
          // A focused button already acts on Enter; handling it here as well would advance
          // twice.
          if (insideButtonOrLink) {
            return
          }
          event.preventDefault()
          handleNext()
        }
        return
      }

      if (event.key === 'Enter') {
        if (insideButtonOrLink) {
          return
        }
        // Mirrors the submit button, which stays disabled until a choice exists.
        if (chosen !== null && !submitAnswer.isPending) {
          event.preventDefault()
          handleSubmit()
        }
        return
      }

      // Only bare lowercase letters; Shift+A and Caps Lock are ignored on purpose.
      if (event.shiftKey) {
        return
      }

      const choices = question.data?.question.choices
      if (isChoiceLetter(event.key) && choices && event.key in choices) {
        event.preventDefault()
        setChosen(event.key)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [answer, chosen, question.data, submitAnswer.isPending, handleNext, handleSubmit])

  if (session.isPending || question.isPending) {
    return <Loading label="Loading your session" />
  }

  if (session.isError) {
    return <ErrorMessage error={session.error} />
  }

  if (question.isError) {
    return <ErrorMessage error={question.error} />
  }

  // The API reports a finished session by refusing to serve another question.
  if (question.data === null && answer === null) {
    return <Navigate to={`/sessions/${sessionId}/summary`} replace />
  }

  const current = question.data

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-slate-400">
            Question {current?.position ?? session.data.answered} of {session.data.total_questions}
          </p>
          <h1 className="text-lg font-semibold tracking-tight">
            {current?.question.subject ?? 'Session complete'}
          </h1>
        </div>
        <Button
          variant="ghost"
          disabled={endSession.isPending}
          onClick={() => {
            endSession.mutate(undefined, {
              onSuccess: () => void navigate(`/sessions/${sessionId}/summary`),
            })
          }}
        >
          End session
        </Button>
      </div>

      {current ? (
        <Card>
          <p className="text-xs uppercase tracking-wide text-slate-400">
            {current.question.domain} · {current.question.objective}
          </p>
          <h2 className="mt-3 text-base leading-relaxed text-slate-100">
            {current.question.question}
          </h2>

          <fieldset className="mt-5 space-y-2" disabled={answer !== null}>
            <legend className="sr-only">Answer choices</legend>
            {Object.entries(current.question.choices).map(([letter, text]) => {
              const isCorrect = answer !== null && answer.correct_choice === letter
              const isWrongPick = answer !== null && chosen === letter && !isCorrect
              return (
                <label
                  key={letter}
                  className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm transition-colors ${
                    isCorrect
                      ? 'border-emerald-600 bg-emerald-950/40'
                      : isWrongPick
                        ? 'border-rose-700 bg-rose-950/40'
                        : chosen === letter
                          ? 'border-brand-500 bg-slate-900'
                          : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="choice"
                    value={letter}
                    checked={chosen === letter}
                    onChange={(event) => {
                      if (isChoiceLetter(event.target.value)) {
                        setChosen(event.target.value)
                      }
                    }}
                    className="mt-1"
                  />
                  <span>
                    <span className="font-semibold text-slate-300">{letter.toUpperCase()}.</span>{' '}
                    <span className="text-slate-100">{text}</span>
                  </span>
                </label>
              )
            })}
          </fieldset>
        </Card>
      ) : null}

      {submitAnswer.isError ? <ErrorMessage error={submitAnswer.error} /> : null}

      {answer ? (
        <AnswerFeedback answer={answer} chosen={chosen} onNext={handleNext} />
      ) : (
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={handleSubmit} disabled={chosen === null || submitAnswer.isPending}>
            Submit answer
          </Button>
          <Button
            variant="secondary"
            disabled={submitAnswer.isPending}
            onClick={() => {
              setChosen(null)
              submitAnswer.mutate(null, { onSuccess: setAnswer })
            }}
          >
            Skip
          </Button>
          <span className="text-xs text-slate-500">or press a–d, then Enter</span>
        </div>
      )}
    </div>
  )
}
