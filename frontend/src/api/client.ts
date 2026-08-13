import createClient, { type Middleware } from 'openapi-fetch'

import type { paths } from './schema'

/**
 * The API lives on its own origin, so every request must opt into sending cookies and the
 * browser will only allow it because the API names this origin in CORS_ORIGINS.
 */
export const API_BASE_URL = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8000'

export const CSRF_COOKIE_NAME = 'sp_csrf'
export const CSRF_HEADER_NAME = 'X-CSRF-Token'

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])

export function readCookie(name: string): string | null {
  const match = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith(`${name}=`))
    ?.slice(name.length + 1)
  return match ? decodeURIComponent(match) : null
}

/**
 * The session cookie is HttpOnly and rides along automatically. The CSRF cookie is readable
 * precisely so it can be echoed here; the API compares it against the session it stored.
 */
const csrfMiddleware: Middleware = {
  onRequest({ request }) {
    if (SAFE_METHODS.has(request.method)) {
      return undefined
    }
    const token = readCookie(CSRF_COOKIE_NAME)
    if (token) {
      request.headers.set(CSRF_HEADER_NAME, token)
    }
    return request
  },
}

export const api = createClient<paths>({
  baseUrl: API_BASE_URL,
  credentials: 'include',
  // Looked up per request instead of captured when this module loads, so anything that
  // replaces fetch later — a test double, an instrumentation wrapper — is actually used.
  fetch: (request) => globalThis.fetch(request),
})

api.use(csrfMiddleware)
