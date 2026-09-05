export type ReviewGuideFilters = {
  domain?: string
  subject?: string
}

export function reviewGuidePath(filters?: string | ReviewGuideFilters | null): string {
  if (!filters) {
    return '/review-guide'
  }

  const params: string[] = []
  if (typeof filters === 'string') {
    params.push(`domain=${encodeURIComponent(filters)}`)
  } else {
    if (filters.domain) {
      params.push(`domain=${encodeURIComponent(filters.domain)}`)
    }
    if (filters.subject) {
      params.push(`subject=${encodeURIComponent(filters.subject)}`)
    }
  }

  return params.length > 0 ? `/review-guide?${params.join('&')}` : '/review-guide'
}
