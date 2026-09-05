import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import type { ReviewGuide } from '../api/types'
import * as fixtures from '../test/fixtures'
import { reviewGuidePath } from '../reviewGuidePaths'
import { renderApp } from '../test/render'
import { server, url } from '../test/server'

const multiDomainReviewGuide: ReviewGuide = {
  ...fixtures.reviewGuide,
  priority_domains: [
    {
      rank: 1,
      domain: 'Domain 1: General Security Concepts',
      incorrect: 1,
      accuracy: 0.0,
      weakness_score: 1.0,
    },
    fixtures.reviewGuide.priority_domains![0]!,
  ],
  focus_areas: [
    {
      rank: 1,
      domain: 'Domain 1: General Security Concepts',
      subject: 'Control categories',
      correct: 0,
      incorrect: 1,
      accuracy: 0.0,
      weakness_score: 1.0,
      concepts: [
        {
          question_id: 'clean-d01-q003',
          prompt: 'Which control type is a firewall?',
          correct_choice: 'Technical',
          explanation: 'Firewalls enforce rules in hardware or software.',
          objective: 'Control types',
          chapter: 'Chapter 1: Security Fundamentals',
          correction_note: null,
        },
      ],
    },
    fixtures.reviewGuide.focus_areas![0]!,
  ],
}

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
      screen.getByText('Chapter 10: Identity and Access Operations - Privileged session control'),
    ).toBeInTheDocument()
  })

  it('shows the weakness score for each focus area', async () => {
    server.use(http.get(url('/api/review-guide'), () => HttpResponse.json(fixtures.reviewGuide)))
    renderApp('/review-guide')

    expect(await screen.findByText(/weakness score 1\.4/i)).toBeInTheDocument()
  })

  it('links to a session built from those questions', async () => {
    server.use(http.get(url('/api/review-guide'), () => HttpResponse.json(fixtures.reviewGuide)))
    renderApp('/review-guide')

    const link = await screen.findByRole('link', { name: 'Practice these questions' })
    expect(link).toHaveAttribute('href', '/study?mode=missed')
  })

  it('opens with the requested domain already filtered', async () => {
    server.use(http.get(url('/api/review-guide'), () => HttpResponse.json(multiDomainReviewGuide)))
    renderApp(reviewGuidePath('Domain 4: Security Operations'))

    expect(await screen.findByText('Privileged access management')).toBeInTheDocument()
    expect(screen.queryByText('Control categories')).not.toBeInTheDocument()
    expect(
      screen.getByText(/Showing subjects in Domain 4: Security Operations/i),
    ).toBeInTheDocument()
  })

  it('opens with the requested subject already filtered', async () => {
    server.use(http.get(url('/api/review-guide'), () => HttpResponse.json(multiDomainReviewGuide)))
    renderApp(reviewGuidePath({ subject: 'Privileged access management' }))

    expect(await screen.findByText('Privileged access management')).toBeInTheDocument()
    expect(screen.queryByText('Control categories')).not.toBeInTheDocument()
    expect(
      screen.getByText(/Showing Privileged access management\. Click a domain below/i),
    ).toBeInTheDocument()
  })

  it('filters focus areas when a domain is selected', async () => {
    server.use(http.get(url('/api/review-guide'), () => HttpResponse.json(multiDomainReviewGuide)))
    const { user } = renderApp('/review-guide')

    expect(await screen.findByText('Control categories')).toBeInTheDocument()
    expect(screen.getByText('Privileged access management')).toBeInTheDocument()

    await user.click(
      screen.getByRole('button', { name: /Domain 4: Security Operations.*2 missed/i }),
    )

    expect(screen.queryByText('Control categories')).not.toBeInTheDocument()
    expect(screen.getByText('Privileged access management')).toBeInTheDocument()
    expect(
      screen.getByText(/Showing subjects in Domain 4: Security Operations/i),
    ).toBeInTheDocument()
  })

  it('shows every focus area again when the selected domain is toggled off', async () => {
    server.use(http.get(url('/api/review-guide'), () => HttpResponse.json(multiDomainReviewGuide)))
    const { user } = renderApp('/review-guide')

    const domainButton = await screen.findByRole('button', {
      name: /Domain 1: General Security Concepts.*1 missed/i,
    })
    await user.click(domainButton)
    expect(screen.queryByText('Privileged access management')).not.toBeInTheDocument()

    await user.click(domainButton)
    expect(screen.getByText('Privileged access management')).toBeInTheDocument()
  })
})
