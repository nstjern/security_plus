import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import type { QuestionSummary } from '../api/types'
import * as fixtures from '../test/fixtures'
import { renderApp } from '../test/render'
import { server, url } from '../test/server'

function question(id: string): QuestionSummary {
  return {
    id,
    domain: fixtures.catalog.domains[0] ?? '',
    chapter: 'Chapter 1: Security Fundamentals',
    subject: 'Password spraying',
    objective: 'Mitigate social engineering',
    question: `Question text for ${id}`,
    choices: { a: 'One', b: 'Two', c: 'Three', d: 'Four' },
  }
}

function withQuestions(total: number) {
  server.use(
    http.get(url('/api/questions'), ({ request }) => {
      const offset = Number(new URL(request.url).searchParams.get('offset') ?? 0)
      return HttpResponse.json({
        items: [question(`q-${offset + 1}`)],
        total,
        limit: 10,
        offset,
      })
    }),
  )
}

describe('browsing the bank', () => {
  it('lists questions without any answers or explanations', async () => {
    withQuestions(136)
    renderApp('/questions')

    expect(await screen.findByText('Question text for q-1')).toBeInTheDocument()
    expect(screen.queryByText(/why that is the answer/i)).not.toBeInTheDocument()
    expect(screen.getByText(/answers and explanations are not shown here/i)).toBeInTheDocument()
  })

  it('pages forward through the results', async () => {
    withQuestions(136)
    const { user } = renderApp('/questions')

    expect(await screen.findByText('Showing 1–10 of 136')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Next' }))

    expect(await screen.findByText('Showing 11–20 of 136')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Previous' })).toBeEnabled()
  })

  it('cannot page backwards from the first page', async () => {
    withQuestions(136)
    renderApp('/questions')

    expect(await screen.findByRole('button', { name: 'Previous' })).toBeDisabled()
  })

  it('narrows the list by domain and starts again from the first page', async () => {
    const requested: string[] = []
    server.use(
      http.get(url('/api/questions'), ({ request }) => {
        const query = new URL(request.url).searchParams
        requested.push(`${query.get('domain') ?? 'any'}@${query.get('offset') ?? '0'}`)
        return HttpResponse.json({ items: [question('q-1')], total: 40, limit: 10, offset: 0 })
      }),
    )
    const { user } = renderApp('/questions')

    await user.click(await screen.findByRole('button', { name: 'Next' }))
    await user.selectOptions(screen.getByLabelText('Domain'), fixtures.catalog.domains[0] ?? '')

    await screen.findByText('Showing 1–10 of 40')
    expect(requested.at(-1)).toBe(`${fixtures.catalog.domains[0]}@0`)
  })

  it('says so when a filter matches nothing', async () => {
    server.use(
      http.get(url('/api/questions'), () =>
        HttpResponse.json({ items: [], total: 0, limit: 10, offset: 0 }),
      ),
    )
    renderApp('/questions')

    expect(await screen.findByText('No questions match those filters')).toBeInTheDocument()
  })
})
