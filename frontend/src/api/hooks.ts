/** Typed data access. Every path and payload below is checked against contracts/openapi.json. */

import { useMutation, useQuery, useQueryClient, type UseQueryResult } from '@tanstack/react-query'

import { api } from './client'
import { unwrap, unwrapEmpty } from './errors'
import { progressRoot, queryKeys } from './queryKeys'
import type {
  AnswerResponse,
  Catalog,
  ChoiceLetter,
  MissedQuestions,
  ProgressSummary,
  ReviewGuide,
  SessionCreateRequest,
  SessionQuestion,
  SessionSummary,
  StudySession,
  User,
} from './types'

interface Credentials {
  username: string
  password: string
}

export function useCurrentUser(): UseQueryResult<User | null> {
  return useQuery({
    queryKey: queryKeys.currentUser,
    queryFn: async () => {
      const result = await api.GET('/api/auth/me')
      // Not being signed in is an ordinary state here, not a failure to report.
      if (result.response.status === 401) {
        return null
      }
      return unwrap(result)
    },
    retry: false,
    staleTime: 60_000,
  })
}

export function useSignIn() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (credentials: Credentials) =>
      unwrap(await api.POST('/api/auth/login', { body: credentials })),
    onSuccess: (user) => {
      queryClient.setQueryData(queryKeys.currentUser, user)
      void queryClient.invalidateQueries({ queryKey: progressRoot })
    },
  })
}

export function useRegister() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (credentials: Credentials) =>
      unwrap(await api.POST('/api/auth/register', { body: credentials })),
    onSuccess: (user) => {
      queryClient.setQueryData(queryKeys.currentUser, user)
    },
  })
}

export function useSignOut() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      unwrapEmpty(await api.POST('/api/auth/logout'))
    },
    onSettled: () => {
      // Record the signed-out state first. Clearing the whole cache instead would leave the
      // current-user observer holding its last snapshot with nothing to refetch from, and the
      // interface would bounce straight back into the signed-in views.
      queryClient.setQueryData(queryKeys.currentUser, null)
      // Then drop everything belonging to the session that just ended.
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'auth' })
    },
  })
}

export function useCatalog(): UseQueryResult<Catalog> {
  return useQuery({
    queryKey: queryKeys.catalog,
    queryFn: async () => unwrap(await api.GET('/api/catalog')),
    staleTime: Infinity,
  })
}

export function useCreateSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (request: SessionCreateRequest) =>
      unwrap(await api.POST('/api/sessions', { body: request })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.sessions })
    },
  })
}

export function useSession(sessionId: string): UseQueryResult<StudySession> {
  return useQuery({
    queryKey: queryKeys.session(sessionId),
    queryFn: async () =>
      unwrap(
        await api.GET('/api/sessions/{session_id}', {
          params: { path: { session_id: sessionId } },
        }),
      ),
  })
}

export function useCurrentQuestion(sessionId: string): UseQueryResult<SessionQuestion | null> {
  return useQuery({
    queryKey: queryKeys.currentQuestion(sessionId),
    queryFn: async () => {
      const result = await api.GET('/api/sessions/{session_id}/current-question', {
        params: { path: { session_id: sessionId } },
      })
      // A finished session has no current question; that is an outcome, not a failure.
      if (result.response.status === 409) {
        return null
      }
      return unwrap(result)
    },
  })
}

export function useSubmitAnswer(sessionId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (choice: ChoiceLetter | null): Promise<AnswerResponse> =>
      unwrap(
        await api.POST('/api/sessions/{session_id}/answer', {
          params: { path: { session_id: sessionId } },
          body: { choice },
        }),
      ),
    onSuccess: () => {
      // exact: true so we refresh session metadata without refetching the current question.
      // The backend advances on submit; refetching early would swap in the next question
      // while feedback for the one just answered is still on screen.
      void queryClient.invalidateQueries({ queryKey: queryKeys.session(sessionId), exact: true })
      void queryClient.invalidateQueries({ queryKey: progressRoot })
      void queryClient.invalidateQueries({ queryKey: ['review-guide'] })
    },
  })
}

export function useEndSession(sessionId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST('/api/sessions/{session_id}/end', {
          params: { path: { session_id: sessionId } },
        }),
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.session(sessionId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.sessions })
    },
  })
}

export function useSessionSummary(sessionId: string): UseQueryResult<SessionSummary> {
  return useQuery({
    queryKey: queryKeys.sessionSummary(sessionId),
    queryFn: async () =>
      unwrap(
        await api.GET('/api/sessions/{session_id}/summary', {
          params: { path: { session_id: sessionId } },
        }),
      ),
  })
}

export function useProgressSummary(): UseQueryResult<ProgressSummary> {
  return useQuery({
    queryKey: queryKeys.progressSummary,
    queryFn: async () => unwrap(await api.GET('/api/progress/summary')),
  })
}

export function useWeakestSubjects(limit = 10) {
  return useQuery({
    queryKey: queryKeys.weakestSubjects(limit),
    queryFn: async () =>
      unwrap(await api.GET('/api/progress/subjects', { params: { query: { limit } } })),
  })
}

export function useMissedQuestions(): UseQueryResult<MissedQuestions> {
  return useQuery({
    queryKey: queryKeys.missedQuestions,
    queryFn: async () => unwrap(await api.GET('/api/progress/missed')),
  })
}

export function useReviewGuide(maxFocusAreas?: number): UseQueryResult<ReviewGuide> {
  return useQuery({
    queryKey: queryKeys.reviewGuide(maxFocusAreas),
    queryFn: async () =>
      unwrap(
        await api.GET('/api/review-guide', {
          params: { query: maxFocusAreas ? { max_focus_areas: maxFocusAreas } : {} },
        }),
      ),
  })
}
