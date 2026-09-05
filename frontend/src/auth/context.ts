import { createContext, use } from 'react'

import type { User } from '../api/types'

export interface AuthState {
  user: User | null
  /** True only until the first answer from the API; used to avoid a sign-in flash on reload. */
  isResolving: boolean
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const state = use(AuthContext)
  if (state === null) {
    throw new Error('useAuth must be used inside an AuthProvider')
  }
  return state
}
