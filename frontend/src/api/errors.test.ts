import { describe, expect, it } from 'vitest'

import {
  ApiError,
  describeError,
  isUnauthorized,
  messageFromPayload,
  unwrap,
  unwrapEmpty,
} from './errors'

function responseWith(status: number): Response {
  return new Response(null, { status })
}

describe('messageFromPayload', () => {
  it('uses the API detail when it is a plain string', () => {
    expect(messageFromPayload({ detail: 'That username is taken' }, 409)).toBe(
      'That username is taken',
    )
  })

  it('uses the first message from a validation failure', () => {
    const payload = { detail: [{ msg: 'String should have at least 12 characters' }] }
    expect(messageFromPayload(payload, 422)).toContain('at least 12 characters')
  })

  it('falls back to a readable message for a known status', () => {
    expect(messageFromPayload(undefined, 401)).toMatch(/sign in again/i)
    expect(messageFromPayload({}, 429)).toMatch(/too many attempts/i)
  })

  it('falls back to something generic for an unexpected status', () => {
    expect(messageFromPayload(undefined, 418)).toBe('Something went wrong.')
  })
})

describe('describeError', () => {
  it('passes an ApiError message straight through', () => {
    expect(describeError(new ApiError(409, 'Already taken'))).toBe('Already taken')
  })

  it('explains a network failure rather than showing the raw message', () => {
    expect(describeError(new TypeError('Failed to fetch'))).toMatch(/could not reach/i)
  })

  it('handles values that are not errors at all', () => {
    expect(describeError('nonsense')).toBe('Something went wrong.')
  })
})

describe('unwrap', () => {
  it('returns the payload of a successful response', () => {
    expect(unwrap({ data: { id: 1 }, response: responseWith(200) })).toEqual({ id: 1 })
  })

  it('throws an ApiError carrying the status', () => {
    const failing = () => unwrap({ error: { detail: 'Not found' }, response: responseWith(404) })

    expect(failing).toThrow(ApiError)
    expect(failing).toThrow('Not found')
  })
})

describe('unwrapEmpty', () => {
  it('accepts a 204 with no body', () => {
    expect(() => unwrapEmpty({ response: responseWith(204) })).not.toThrow()
  })

  it('throws when the response failed', () => {
    expect(() => unwrapEmpty({ error: { detail: 'Nope' }, response: responseWith(403) })).toThrow(
      'Nope',
    )
  })
})

describe('isUnauthorized', () => {
  it('recognises only a 401', () => {
    expect(isUnauthorized(new ApiError(401, 'x'))).toBe(true)
    expect(isUnauthorized(new ApiError(403, 'x'))).toBe(false)
    expect(isUnauthorized(new Error('x'))).toBe(false)
  })
})
