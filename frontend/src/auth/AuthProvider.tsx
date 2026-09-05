import { useMemo } from 'react'
import type { ReactNode } from 'react'

import { useCurrentUser } from '../api/hooks'
import { AuthContext, type AuthState } from './context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const { data, isPending } = useCurrentUser()

  const value = useMemo<AuthState>(
    () => ({ user: data ?? null, isResolving: isPending }),
    [data, isPending],
  )

  return <AuthContext value={value}>{children}</AuthContext>
}
