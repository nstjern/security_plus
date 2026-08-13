import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { describeError } from '../api/errors'
import { useRegister, useSignIn } from '../api/hooks'
import { useAuth } from '../auth/context'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { TextField } from '../components/Field'

const MINIMUM_PASSWORD_LENGTH = 12

export function SignInPage() {
  const { user } = useAuth()
  const location = useLocation()
  const [isCreating, setIsCreating] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const signIn = useSignIn()
  const register = useRegister()
  const active = isCreating ? register : signIn

  if (user) {
    const from = (location.state as { from?: string } | null)?.from
    return <Navigate to={from ?? '/'} replace />
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    active.mutate({ username, password })
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">
        {isCreating ? 'Create an account' : 'Sign in'}
      </h1>
      <p className="mb-6 text-sm text-slate-400">
        Your progress, weak areas, and review guide are stored against your account.
      </p>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <TextField
            label="Username"
            name="username"
            autoComplete="username"
            required
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />

          <TextField
            label="Password"
            name="password"
            type="password"
            autoComplete={isCreating ? 'new-password' : 'current-password'}
            required
            minLength={isCreating ? MINIMUM_PASSWORD_LENGTH : undefined}
            hint={
              isCreating
                ? `At least ${MINIMUM_PASSWORD_LENGTH} characters. Length matters more than symbols.`
                : undefined
            }
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {active.isError ? <Alert tone="error">{describeError(active.error)}</Alert> : null}

          <Button type="submit" className="w-full" disabled={active.isPending}>
            {active.isPending ? 'Working…' : isCreating ? 'Create account' : 'Sign in'}
          </Button>
        </form>
      </Card>

      <p className="mt-4 text-center text-sm text-slate-400">
        {isCreating ? 'Already have an account?' : 'Need an account?'}{' '}
        <button
          type="button"
          className="font-medium text-brand-300 underline underline-offset-4"
          onClick={() => {
            setIsCreating((previous) => !previous)
            signIn.reset()
            register.reset()
          }}
        >
          {isCreating ? 'Sign in' : 'Create one'}
        </button>
      </p>
    </div>
  )
}
