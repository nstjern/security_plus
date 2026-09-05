import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

import { API_BASE_URL } from '../api/client'
import * as fixtures from './fixtures'

export const url = (path: string) => `${API_BASE_URL}${path}`

/** Signed in, nothing answered yet. Individual tests override what they care about. */
export const defaultHandlers = [
  http.get(url('/api/auth/me'), () => HttpResponse.json(fixtures.user)),
  http.get(url('/api/catalog'), () => HttpResponse.json(fixtures.catalog)),
  http.get(url('/api/progress/summary'), () => HttpResponse.json(fixtures.emptyProgress)),
  http.get(url('/api/progress/subjects'), () => HttpResponse.json([])),
  http.get(url('/api/progress/missed'), () =>
    HttpResponse.json({
      all: { count: 0, question_ids: [] },
      unresolved: { count: 0, question_ids: [] },
    }),
  ),
  http.get(url('/api/review-guide'), () => HttpResponse.json(fixtures.emptyReviewGuide)),
]

export const server = setupServer(...defaultHandlers)

export const signedOut = http.get(url('/api/auth/me'), () =>
  HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 }),
)
