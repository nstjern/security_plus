import { describe, expect, it } from 'vitest'

import { reviewGuidePath } from './reviewGuidePaths'

describe('reviewGuidePath', () => {
  it('returns the unfiltered review guide route by default', () => {
    expect(reviewGuidePath()).toBe('/review-guide')
  })

  it('encodes the domain query parameter', () => {
    expect(reviewGuidePath('Domain 4: Security Operations')).toBe(
      '/review-guide?domain=Domain%204%3A%20Security%20Operations',
    )
  })

  it('encodes the subject query parameter', () => {
    expect(reviewGuidePath({ subject: 'Privileged access management' })).toBe(
      '/review-guide?subject=Privileged%20access%20management',
    )
  })
})
