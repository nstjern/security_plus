import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import * as fixtures from '../test/fixtures'
import { renderApp } from '../test/render'
import { server, url } from '../test/server'

describe('starting a session', () => {
  it('sends the chosen mode and lands on the first question', async () => {
    let body: unknown = null
    server.use(
      http.post(url('/api/sessions'), async ({ request }) => {
        body = await request.json()
        return HttpResponse.json(fixtures.studySession, { status: 201 })
      }),
      http.get(url('/api/sessions/:id'), () => HttpResponse.json(fixtures.studySession)),
      http.get(url('/api/sessions/:id/current-question'), () =>
        HttpResponse.json(fixtures.sessionQuestion),
      ),
    )
    const { user } = renderApp('/study')

    await user.click(await screen.findByRole('radio', { name: /everything/i }))
    await user.click(screen.getByRole('button', { name: 'Begin' }))

    expect(await screen.findByText(/emergency database maintenance/i)).toBeInTheDocument()
    expect(body).toMatchObject({ mode: 'all', shuffle_answers: true })
  })

  it('asks for a filter value when the mode needs one', async () => {
    const { user } = renderApp('/study')

    await user.click(await screen.findByRole('radio', { name: /one domain/i }))

    const select = screen.getByLabelText('One domain')
    expect(select).toBeRequired()
    expect(screen.getByRole('option', { name: fixtures.catalog.domains[0] })).toBeInTheDocument()
  })

  it('asks how many questions only for a practice quiz', async () => {
    const { user } = renderApp('/study')

    expect(await screen.findByLabelText('How many questions')).toHaveValue(20)

    await user.click(screen.getByRole('radio', { name: /everything/i }))
    expect(screen.queryByLabelText('How many questions')).not.toBeInTheDocument()
  })

  it('sends the number of questions the learner typed', async () => {
    let body: { count?: number } | null = null
    server.use(
      http.post(url('/api/sessions'), async ({ request }) => {
        body = (await request.json()) as { count?: number }
        return HttpResponse.json(fixtures.studySession, { status: 201 })
      }),
      http.get(url('/api/sessions/:id'), () => HttpResponse.json(fixtures.studySession)),
      http.get(url('/api/sessions/:id/current-question'), () =>
        HttpResponse.json(fixtures.sessionQuestion),
      ),
    )
    const { user } = renderApp('/study')

    const count = await screen.findByLabelText('How many questions')
    await user.clear(count)
    await user.type(count, '3')
    expect(count).toHaveValue(3)

    await user.click(screen.getByRole('button', { name: 'Begin' }))

    expect(body).toMatchObject({ mode: 'practice', count: 3 })
  })

  it('lets the API pick the size when the field is left empty', async () => {
    let body: { count?: number | null } | null = null
    server.use(
      http.post(url('/api/sessions'), async ({ request }) => {
        body = (await request.json()) as { count?: number | null }
        return HttpResponse.json(fixtures.studySession, { status: 201 })
      }),
      http.get(url('/api/sessions/:id'), () => HttpResponse.json(fixtures.studySession)),
      http.get(url('/api/sessions/:id/current-question'), () =>
        HttpResponse.json(fixtures.sessionQuestion),
      ),
    )
    const { user } = renderApp('/study')

    const count = await screen.findByLabelText('How many questions')
    await user.clear(count)
    expect(count).toHaveValue(null)

    await user.click(screen.getByRole('button', { name: 'Begin' }))

    expect(body).toMatchObject({ count: null })
  })

  it('preselects the mode named in the address', async () => {
    server.use(
      http.get(url('/api/progress/missed'), () =>
        HttpResponse.json({
          all: { count: 4, question_ids: ['a', 'b', 'c', 'd'] },
          unresolved: { count: 2, question_ids: ['a', 'b'] },
        }),
      ),
    )
    renderApp('/study?mode=missed')

    expect(await screen.findByRole('radio', { name: /questions you missed/i })).toBeChecked()
  })

  it('lets the learner choose which missed questions to revisit', async () => {
    let body: { mode?: string; missed_scope?: string } | null = null
    server.use(
      http.get(url('/api/progress/missed'), () =>
        HttpResponse.json({
          all: { count: 4, question_ids: ['a', 'b', 'c', 'd'] },
          unresolved: { count: 2, question_ids: ['a', 'b'] },
        }),
      ),
      http.post(url('/api/sessions'), async ({ request }) => {
        body = (await request.json()) as { mode?: string; missed_scope?: string }
        return HttpResponse.json(fixtures.studySession, { status: 201 })
      }),
      http.get(url('/api/sessions/:id'), () => HttpResponse.json(fixtures.studySession)),
      http.get(url('/api/sessions/:id/current-question'), () =>
        HttpResponse.json(fixtures.sessionQuestion),
      ),
    )
    const { user } = renderApp('/study')

    await user.click(await screen.findByRole('radio', { name: /questions you missed/i }))
    await user.click(
      screen.getByRole('radio', {
        name: /only questions not yet answered correctly.*2 questions/i,
      }),
    )
    await user.click(screen.getByRole('button', { name: 'Begin' }))

    expect(body).toMatchObject({ mode: 'missed', missed_scope: 'unresolved' })
  })

  it('disables revisiting missed questions when there are none', async () => {
    renderApp('/study')

    expect(await screen.findByRole('radio', { name: /have not missed any/i })).toBeDisabled()
  })

  it('reports why a selection was refused', async () => {
    server.use(
      http.post(url('/api/sessions'), () =>
        HttpResponse.json({ detail: 'No questions match that selection.' }, { status: 422 }),
      ),
    )
    const { user } = renderApp('/study')

    await user.click(await screen.findByRole('radio', { name: /everything/i }))
    await user.click(screen.getByRole('button', { name: 'Begin' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No questions match that selection.')
  })
})
