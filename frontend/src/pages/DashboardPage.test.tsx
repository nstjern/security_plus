import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import * as fixtures from '../test/fixtures'
import { renderApp } from '../test/render'
import { server, url } from '../test/server'

function withProgress() {
  server.use(
    http.get(url('/api/progress/summary'), () => HttpResponse.json(fixtures.progress)),
    http.get(url('/api/progress/subjects'), () => HttpResponse.json(fixtures.progress.domains)),
    http.get(url('/api/progress/missed'), () =>
      HttpResponse.json({ count: 3, question_ids: ['clean-d04-q004'] }),
    ),
  )
}

describe('the dashboard', () => {
  it('invites a new learner to start rather than showing empty charts', async () => {
    renderApp('/')

    expect(await screen.findByText('No answers recorded yet')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Start your first session' })).toBeInTheDocument()
  })

  it('reports the headline numbers once there is progress', async () => {
    withProgress()
    renderApp('/')

    expect(await screen.findByText('67%')).toBeInTheDocument()
    expect(screen.getByText('Answered').previousSibling).toHaveTextContent('10')
    expect(screen.getByText('Correct').previousSibling).toHaveTextContent('6')
    expect(screen.getByText('Missed').previousSibling).toHaveTextContent('3')
  })

  it('breaks accuracy down by domain', async () => {
    withProgress()
    renderApp('/')

    expect(await screen.findByText('Accuracy by domain')).toBeInTheDocument()
    expect(screen.getAllByText('Domain 4: Security Operations').length).toBeGreaterThan(0)
    expect(screen.getByText('9 graded, 1 skipped')).toBeInTheDocument()
  })

  it('offers a shortcut to practise missed questions', async () => {
    withProgress()
    renderApp('/')

    const link = await screen.findByRole('link', { name: 'Practice these' })
    expect(link).toHaveAttribute('href', '/study?mode=missed')
  })

  it('surfaces a failure to load rather than rendering zeroes', async () => {
    // A 500 carries no useful detail, so the interface has to supply the wording.
    server.use(
      http.get(url('/api/progress/summary'), () => new HttpResponse(null, { status: 500 })),
    )
    renderApp('/')

    expect(await screen.findByRole('alert')).toHaveTextContent(/went wrong on our side/i)
  })
})
