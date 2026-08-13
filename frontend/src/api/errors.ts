/** Turning API failures into something a learner can act on. */

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

const STATUS_FALLBACKS: Record<number, string> = {
  401: 'Your session has ended. Sign in again to continue.',
  403: 'That request could not be verified. Reload the page and try again.',
  404: 'We could not find what you were looking for.',
  409: 'That is no longer available.',
  429: 'Too many attempts. Wait a moment and try again.',
  500: 'Something went wrong on our side.',
  503: 'The study service is starting up. Try again in a moment.',
}

/** FastAPI reports a string for deliberate errors and a list for validation failures. */
export function messageFromPayload(payload: unknown, status: number): string {
  const detail = (payload as { detail?: unknown } | undefined)?.detail

  if (typeof detail === 'string' && detail.length > 0) {
    return detail
  }

  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: unknown } | undefined
    if (typeof first?.msg === 'string') {
      return first.msg
    }
  }

  return STATUS_FALLBACKS[status] ?? 'Something went wrong.'
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  // A rejected fetch means the request never reached the API at all.
  if (error instanceof TypeError) {
    return 'Could not reach the study service. Check that the API is running.'
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return 'Something went wrong.'
}

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401
}

interface FetchResult<T> {
  data?: T
  error?: unknown
  response: Response
}

export function unwrap<T>(result: FetchResult<T>): T {
  if (result.data === undefined) {
    throw new ApiError(
      result.response.status,
      messageFromPayload(result.error, result.response.status),
    )
  }
  return result.data
}

/** For endpoints that answer 204 and therefore have no body to unwrap. */
export function unwrapEmpty(result: Pick<FetchResult<unknown>, 'error' | 'response'>): void {
  if (!result.response.ok) {
    throw new ApiError(
      result.response.status,
      messageFromPayload(result.error, result.response.status),
    )
  }
}
