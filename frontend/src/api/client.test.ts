import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { server, url } from '../test/server'
import { CSRF_HEADER_NAME, api, readCookie } from './client'

describe('readCookie', () => {
  it('returns the value of a named cookie', () => {
    document.cookie = 'sp_csrf=token-value'
    expect(readCookie('sp_csrf')).toBe('token-value')
  })

  it('returns null when the cookie is absent', () => {
    expect(readCookie('sp_csrf')).toBeNull()
  })

  it('does not confuse a cookie whose name is a suffix of another', () => {
    document.cookie = 'other_sp_csrf=wrong'
    document.cookie = 'sp_csrf=right'
    expect(readCookie('sp_csrf')).toBe('right')
  })
})

describe('CSRF middleware', () => {
  it('echoes the CSRF cookie on state-changing requests', async () => {
    document.cookie = 'sp_csrf=the-token'
    let received: string | null = null
    server.use(
      http.post(url('/api/auth/logout'), ({ request }) => {
        received = request.headers.get(CSRF_HEADER_NAME)
        return new HttpResponse(null, { status: 204 })
      }),
    )

    await api.POST('/api/auth/logout')
    expect(received).toBe('the-token')
  })

  it('leaves safe requests alone', async () => {
    document.cookie = 'sp_csrf=the-token'
    let received: string | null = 'not-checked'
    server.use(
      http.get(url('/api/catalog'), ({ request }) => {
        received = request.headers.get(CSRF_HEADER_NAME)
        return HttpResponse.json({})
      }),
    )

    await api.GET('/api/catalog')
    expect(received).toBeNull()
  })

  it('sends nothing when there is no CSRF cookie to echo', async () => {
    let received: string | null = 'not-checked'
    server.use(
      http.post(url('/api/auth/logout'), ({ request }) => {
        received = request.headers.get(CSRF_HEADER_NAME)
        return new HttpResponse(null, { status: 204 })
      }),
    )

    await api.POST('/api/auth/logout')
    expect(received).toBeNull()
  })
})
