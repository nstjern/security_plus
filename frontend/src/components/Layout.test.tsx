import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { renderApp } from '../test/render'
import { server, signedOut, url } from '../test/server'

describe('the layout', () => {
  it('shows navigation and the signed-in username', async () => {
    renderApp('/')

    expect(await screen.findByRole('navigation', { name: 'Main' })).toBeInTheDocument()
    expect(screen.getByText('learner')).toBeInTheDocument()
  })

  it('hides navigation from a visitor who is not signed in', async () => {
    server.use(signedOut)
    renderApp('/sign-in')

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(screen.queryByRole('navigation', { name: 'Main' })).not.toBeInTheDocument()
  })

  it('returns to the sign-in page after signing out', async () => {
    server.use(
      http.post(url('/api/auth/logout'), () => {
        // The real API revokes the session, so asking who you are stops working.
        server.use(signedOut)
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { user } = renderApp('/')

    await user.click(await screen.findByRole('button', { name: 'Sign out' }))

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('offers a way to skip past the navigation', async () => {
    renderApp('/')

    expect(await screen.findByRole('link', { name: 'Skip to content' })).toHaveAttribute(
      'href',
      '#main',
    )
  })
})
