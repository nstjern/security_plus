import { screen } from '@testing-library/react'
import { http, HttpResponse, type RequestHandler } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import * as fixtures from '../test/fixtures'
import { renderApp } from '../test/render'
import { server, url } from '../test/server'

const SESSION_PATH = `/sessions/${fixtures.SESSION_ID}`

/** Overrides come first: the earliest matching handler is the one MSW uses. */
function sessionHandlers(...overrides: RequestHandler[]) {
  server.use(
    ...overrides,
    http.get(url('/api/sessions/:id'), () => HttpResponse.json(fixtures.studySession)),
    http.get(url('/api/sessions/:id/current-question'), () =>
      HttpResponse.json(fixtures.sessionQuestion),
    ),
    http.get(url('/api/sessions/:id/summary'), () => HttpResponse.json(fixtures.sessionSummary)),
  )
}

describe('answering a question', () => {
  beforeEach(() => sessionHandlers())

  it('shows the question and its choices without revealing the answer', async () => {
    renderApp(SESSION_PATH)

    expect(await screen.findByText(/emergency database maintenance/i)).toBeInTheDocument()
    expect(screen.getByText('Question 1 of 2')).toBeInTheDocument()
    expect(screen.getAllByRole('radio')).toHaveLength(4)
    expect(screen.queryByText(/why that is the answer/i)).not.toBeInTheDocument()
  })

  it('will not submit until a choice is made', async () => {
    renderApp(SESSION_PATH)

    expect(await screen.findByRole('button', { name: 'Submit answer' })).toBeDisabled()
  })

  it('reveals the explanation once an answer is submitted', async () => {
    server.use(
      http.post(url('/api/sessions/:id/answer'), () => HttpResponse.json(fixtures.correctAnswer)),
    )
    const { user } = renderApp(SESSION_PATH)

    await user.click(await screen.findByRole('radio', { name: /PAM system/i }))
    await user.click(screen.getByRole('button', { name: 'Submit answer' }))

    expect(await screen.findByText('Correct')).toBeInTheDocument()
    expect(screen.getByText(/injects vaulted credentials/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Next question' })).toBeInTheDocument()
  })

  it('names the choice that was picked when it was wrong', async () => {
    server.use(
      http.post(url('/api/sessions/:id/answer'), () =>
        HttpResponse.json({ ...fixtures.correctAnswer, result: 'incorrect' }),
      ),
    )
    const { user } = renderApp(SESSION_PATH)

    await user.click(await screen.findByRole('radio', { name: /shared spreadsheet/i }))
    await user.click(screen.getByRole('button', { name: 'Submit answer' }))

    expect(await screen.findByText('Not quite')).toBeInTheDocument()
    expect(screen.getByText(/you chose C\. the answer is B/i)).toBeInTheDocument()
  })

  it('records a skip without choosing anything', async () => {
    server.use(
      http.post(url('/api/sessions/:id/answer'), () =>
        HttpResponse.json({ ...fixtures.correctAnswer, result: 'skipped' }),
      ),
    )
    const { user } = renderApp(SESSION_PATH)

    await user.click(await screen.findByRole('button', { name: 'Skip' }))

    expect(await screen.findByText('Skipped')).toBeInTheDocument()
  })

  it('offers the results instead of another question at the end', async () => {
    server.use(
      http.post(url('/api/sessions/:id/answer'), () =>
        HttpResponse.json(fixtures.incorrectFinalAnswer),
      ),
    )
    const { user } = renderApp(SESSION_PATH)

    await user.click(await screen.findByRole('radio', { name: /PAM system/i }))
    await user.click(screen.getByRole('button', { name: 'Submit answer' }))

    const finish = await screen.findByRole('button', { name: 'See your results' })
    await user.click(finish)

    expect(await screen.findByRole('heading', { name: 'Session complete' })).toBeInTheDocument()
  })

  it('reports a failure to submit rather than pretending it worked', async () => {
    server.use(
      http.post(url('/api/sessions/:id/answer'), () =>
        HttpResponse.json({ detail: 'This session has no questions left.' }, { status: 409 }),
      ),
    )
    const { user } = renderApp(SESSION_PATH)

    await user.click(await screen.findByRole('radio', { name: /PAM system/i }))
    await user.click(screen.getByRole('button', { name: 'Submit answer' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'This session has no questions left.',
    )
  })
})

describe('answering from the keyboard', () => {
  beforeEach(() => sessionHandlers())

  it('picks a choice by its letter and submits on Enter', async () => {
    server.use(
      http.post(url('/api/sessions/:id/answer'), () => HttpResponse.json(fixtures.correctAnswer)),
    )
    const { user } = renderApp(SESSION_PATH)

    await screen.findByText(/emergency database maintenance/i)
    await user.keyboard('b')
    expect(screen.getByRole('radio', { name: /PAM system/i })).toBeChecked()

    await user.keyboard('{Enter}')

    expect(await screen.findByText('Correct')).toBeInTheDocument()
  })

  it('moves to the next question on a second Enter', async () => {
    server.use(
      http.post(url('/api/sessions/:id/answer'), () => HttpResponse.json(fixtures.correctAnswer)),
    )
    const { user } = renderApp(SESSION_PATH)

    await screen.findByText(/emergency database maintenance/i)
    await user.keyboard('b{Enter}')
    await screen.findByText('Correct')

    await user.keyboard('{Enter}')

    expect(await screen.findByRole('radio', { name: /PAM system/i })).not.toBeChecked()
    expect(screen.queryByText(/why that is the answer/i)).not.toBeInTheDocument()
  })

  it('reaches the summary when Enter follows the last question', async () => {
    server.use(
      http.post(url('/api/sessions/:id/answer'), () =>
        HttpResponse.json(fixtures.incorrectFinalAnswer),
      ),
    )
    const { user } = renderApp(SESSION_PATH)

    await screen.findByText(/emergency database maintenance/i)
    await user.keyboard('b{Enter}')
    await screen.findByText('Not quite')

    await user.keyboard('{Enter}')

    expect(await screen.findByRole('heading', { name: 'Session complete' })).toBeInTheDocument()
  })

  it('ignores Enter until a choice is made', async () => {
    const { user } = renderApp(SESSION_PATH)

    await screen.findByText(/emergency database maintenance/i)
    await user.keyboard('{Enter}')

    expect(screen.getByRole('button', { name: 'Submit answer' })).toBeDisabled()
    expect(screen.queryByText(/why that is the answer/i)).not.toBeInTheDocument()
  })

  it('ignores letters that this question does not offer', async () => {
    const { user } = renderApp(SESSION_PATH)

    await screen.findByText(/emergency database maintenance/i)
    await user.keyboard('z')

    expect(
      screen.getAllByRole('radio').every((radio) => !(radio as HTMLInputElement).checked),
    ).toBe(true)
  })

  it('ignores uppercase letters', async () => {
    const { user } = renderApp(SESSION_PATH)

    await screen.findByText(/emergency database maintenance/i)
    await user.keyboard('B')

    expect(
      screen.getAllByRole('radio').every((radio) => !(radio as HTMLInputElement).checked),
    ).toBe(true)
  })

  it('selects a choice even when a button has focus', async () => {
    const { user } = renderApp(SESSION_PATH)

    await screen.findByText(/emergency database maintenance/i)
    screen.getByRole('button', { name: 'End session' }).focus()
    await user.keyboard('b')

    expect(screen.getByRole('radio', { name: /PAM system/i })).toBeChecked()
  })

  it('submits once when Enter is pressed on the focused button', async () => {
    let submissions = 0
    server.use(
      http.post(url('/api/sessions/:id/answer'), () => {
        submissions += 1
        return HttpResponse.json(fixtures.correctAnswer)
      }),
    )
    const { user } = renderApp(SESSION_PATH)

    await user.click(await screen.findByRole('radio', { name: /PAM system/i }))
    // The button handles Enter natively, so the window listener has to stand down or the
    // answer would be posted twice.
    screen.getByRole('button', { name: 'Submit answer' }).focus()
    await user.keyboard('{Enter}')

    expect(await screen.findByText('Correct')).toBeInTheDocument()
    expect(submissions).toBe(1)
  })
})

describe('a session that is already over', () => {
  it('goes straight to the summary', async () => {
    sessionHandlers(
      http.get(url('/api/sessions/:id/current-question'), () =>
        HttpResponse.json({ detail: 'This session has no questions left.' }, { status: 409 }),
      ),
    )
    renderApp(SESSION_PATH)

    expect(await screen.findByRole('heading', { name: 'Session complete' })).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
  })

  it('can be ended early', async () => {
    sessionHandlers(
      http.post(url('/api/sessions/:id/end'), () =>
        HttpResponse.json({ ...fixtures.studySession, status: 'ended' }),
      ),
    )
    const { user } = renderApp(SESSION_PATH)

    await user.click(await screen.findByRole('button', { name: 'End session' }))

    expect(await screen.findByRole('heading', { name: 'Session complete' })).toBeInTheDocument()
  })
})
