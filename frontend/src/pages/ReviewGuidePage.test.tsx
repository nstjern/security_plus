import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import * as fixtures from '../test/fixtures'
import { renderApp } from '../test/render'
import { server, url } from '../test/server'

describe('the review guide', () => {
  it('explains why it is empty for a new learner', async () => {
    renderApp('/review-guide')

    expect(await screen.findByText('Nothing to review yet')).toBeInTheDocument()
  })

  it('ranks the domains worth working on', async () => {
    server.use(http.get(url('/api/review-guide'), () => HttpResponse.json(fixtures.reviewGuide)))
    renderApp('/review-guide')

    expect(await screen.findByText('Where to spend your time')).toBeInTheDocument()
    expect(screen.getByText('3 missed answers across 1 domains')).toBeInTheDocument()
    expect(screen.getByText('2 missed')).toBeInTheDocument()
  })

  it('gives the concept and explanation behind each missed question', async () => {
    server.use(http.get(url('/api/review-guide'), () => HttpResponse.json(fixtures.reviewGuide)))
    renderApp('/review-guide')

    expect(await screen.findByText(/A PAM system that brokers/)).toBeInTheDocument()
    expect(screen.getByText(/injects vaulted credentials/)).toBeInTheDocument()
    expect(
      screen.getByText(/Chapter 10: Identity and Access Operations · Privileged session control/),
    ).toBeInTheDocument()
  })

  it('links to a session built from those questions', async () => {
    server.use(http.get(url('/api/review-guide'), () => HttpResponse.json(fixtures.reviewGuide)))
    renderApp('/review-guide')

    const link = await screen.findByRole('link', { name: 'Practice these questions' })
    expect(link).toHaveAttribute('href', '/study?mode=missed')
  })
})
