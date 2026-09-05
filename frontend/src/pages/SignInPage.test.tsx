import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import * as fixtures from '../test/fixtures'
import { renderApp } from '../test/render'
import { server, signedOut, url } from '../test/server'

describe('signing in', () => {
  it('sends the learner to the dashboard afterwards', async () => {
    server.use(
      signedOut,
      http.post(url('/api/auth/login'), () => HttpResponse.json(fixtures.user)),
    )
    const { user } = renderApp('/sign-in')

    await user.type(await screen.findByLabelText('Username'), 'learner')
    await user.type(screen.getByLabelText('Password'), 'correct-horse-battery')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('heading', { name: 'Your progress' })).toBeInTheDocument()
  })

  it('shows the reason the API gave for refusing', async () => {
    server.use(
      signedOut,
      http.post(url('/api/auth/login'), () =>
        HttpResponse.json({ detail: 'Invalid username or password' }, { status: 401 }),
      ),
    )
    const { user } = renderApp('/sign-in')

    await user.type(await screen.findByLabelText('Username'), 'learner')
    await user.type(screen.getByLabelText('Password'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid username or password')
  })

  it('explains a rate-limited response', async () => {
    server.use(
      signedOut,
      http.post(url('/api/auth/login'), () =>
        HttpResponse.json(
          { detail: 'Too many sign-in attempts. Try again shortly.' },
          { status: 429 },
        ),
      ),
    )
    const { user } = renderApp('/sign-in')

    await user.type(await screen.findByLabelText('Username'), 'learner')
    await user.type(screen.getByLabelText('Password'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/too many sign-in attempts/i)
  })
})

describe('creating an account', () => {
  it('switches to the registration form and back', async () => {
    server.use(signedOut)
    const { user } = renderApp('/sign-in')

    await user.click(await screen.findByRole('button', { name: 'Create one' }))
    expect(screen.getByRole('heading', { name: 'Create an account' })).toBeInTheDocument()
    expect(screen.getByText(/at least 12 characters/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('reports a username that is already taken', async () => {
    server.use(
      signedOut,
      http.post(url('/api/auth/register'), () =>
        HttpResponse.json({ detail: 'That username is already taken' }, { status: 409 }),
      ),
    )
    const { user } = renderApp('/sign-in')

    await user.click(await screen.findByRole('button', { name: 'Create one' }))
    await user.type(screen.getByLabelText('Username'), 'learner')
    await user.type(screen.getByLabelText('Password'), 'correct-horse-battery')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('That username is already taken')
  })
})

describe('the auth guard', () => {
  it('redirects an unauthenticated visitor to sign in', async () => {
    server.use(signedOut)
    renderApp('/review-guide')

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('lets a signed-in learner through', async () => {
    renderApp('/review-guide')

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Your review guide' })).toBeInTheDocument()
    })
  })
})
