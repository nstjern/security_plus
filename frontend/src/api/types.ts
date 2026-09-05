import type { components } from './schema'

type Schemas = components['schemas']

export type User = Schemas['UserResponse']
export type Catalog = Schemas['CatalogResponse']
export type StudySession = Schemas['StudySessionResponse']
export type SessionQuestion = Schemas['SessionQuestionResponse']
export type SessionSummary = Schemas['SessionSummaryResponse']
export type AnswerResponse = Schemas['AnswerResponse']
export type AttemptResult = Schemas['AttemptResult']
export type ProgressSummary = Schemas['ProgressSummaryResponse']
export type GroupStats = Schemas['GroupStatsResponse']
export type MissedQuestions = Schemas['MissedQuestionsResponse']
export type MissedScope = Schemas['MissedScope']
export type ReviewGuide = Schemas['ReviewGuide']
export type FocusArea = Schemas['FocusArea']
export type StudyMode = Schemas['StudyMode']
export type SessionCreateRequest = Schemas['SessionCreateRequest']

/** The letters a learner can pick, as the API presents them. */
export type ChoiceLetter = 'a' | 'b' | 'c' | 'd'

export const CHOICE_LETTERS: readonly ChoiceLetter[] = ['a', 'b', 'c', 'd']
