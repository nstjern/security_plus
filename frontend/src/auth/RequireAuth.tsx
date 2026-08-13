import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { Loading } from '../components/Feedback'
import { useAuth } from './context'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, isResolving } = useAuth()
  const location = useLocation()

  if (isResolving) {
    return <Loading label="Checking your session" />
  }

  if (user === null) {
    // Remembered so signing in returns the learner to where they were headed.
    return <Navigate to="/sign-in" replace state={{ from: location.pathname }} />
  }

  return <>{children}</>
}
