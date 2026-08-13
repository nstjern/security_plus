/** One place to name cached queries, so invalidation cannot drift from fetching. */

export const queryKeys = {
  currentUser: ['auth', 'me'] as const,
  catalog: ['catalog'] as const,
  questions: (filters: object) => ['questions', filters] as const,
  sessions: ['sessions'] as const,
  session: (id: string) => ['sessions', id] as const,
  currentQuestion: (id: string) => ['sessions', id, 'current-question'] as const,
  sessionSummary: (id: string) => ['sessions', id, 'summary'] as const,
  progressSummary: ['progress', 'summary'] as const,
  weakestSubjects: (limit: number) => ['progress', 'subjects', limit] as const,
  missedQuestions: ['progress', 'missed'] as const,
  reviewGuide: (maxFocusAreas: number | undefined) => ['review-guide', maxFocusAreas] as const,
}

/** Everything that changes the moment an answer is submitted. */
export const progressRoot = ['progress'] as const
