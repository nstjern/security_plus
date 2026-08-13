import type {
  AnswerResponse,
  Catalog,
  ProgressSummary,
  ReviewGuide,
  SessionQuestion,
  SessionSummary,
  StudySession,
  User,
} from '../api/types'

export const SESSION_ID = '11111111-2222-3333-4444-555555555555'

export const user: User = {
  id: 1,
  username: 'learner',
  created_at: '2026-08-12T00:00:00Z',
}

export const catalog: Catalog = {
  domains: ['Domain 1: General Security Concepts', 'Domain 4: Security Operations'],
  chapters: ['Chapter 1: Security Fundamentals'],
  subjects: ['Password spraying', 'Privileged access management'],
  objectives: ['Mitigate social engineering'],
  question_count: 136,
}

export const emptyProgress: ProgressSummary = {
  attempts: 0,
  correct: 0,
  incorrect: 0,
  skipped: 0,
  graded: 0,
  accuracy: 0,
  domains: [],
}

export const progress: ProgressSummary = {
  attempts: 10,
  correct: 6,
  incorrect: 3,
  skipped: 1,
  graded: 9,
  accuracy: 6 / 9,
  domains: [
    {
      name: 'Domain 1: General Security Concepts',
      attempts: 5,
      correct: 4,
      incorrect: 1,
      skipped: 0,
      graded: 5,
      accuracy: 0.8,
    },
    {
      name: 'Domain 4: Security Operations',
      attempts: 5,
      correct: 2,
      incorrect: 2,
      skipped: 1,
      graded: 4,
      accuracy: 0.5,
    },
  ],
}

export const studySession: StudySession = {
  id: SESSION_ID,
  mode: 'practice',
  filters: {},
  total_questions: 2,
  answered: 0,
  status: 'active',
  shuffle_answers: false,
  created_at: '2026-08-12T00:00:00Z',
  ended_at: null,
}

export const sessionQuestion: SessionQuestion = {
  position: 1,
  total: 2,
  question: {
    id: 'clean-d04-q004',
    domain: 'Domain 4: Security Operations',
    chapter: 'Chapter 10: Identity and Access Operations',
    subject: 'Privileged access management',
    objective: 'Privileged session control',
    question:
      'Which solution BEST fits emergency database maintenance without disclosing the root password?',
    choices: {
      a: 'A standard account added permanently to the administrators group',
      b: 'A PAM system that brokers and records a time-limited privileged session',
      c: 'A shared spreadsheet containing the root password',
      d: 'A portal that stores only application bookmarks',
    },
  },
}

export const correctAnswer: AnswerResponse = {
  result: 'correct',
  correct_choice: 'b',
  correct_choice_text: 'A PAM system that brokers and records a time-limited privileged session',
  explanation: 'A privileged access management system injects vaulted credentials just in time.',
  correction_note: null,
  position: 1,
  total: 2,
  session_status: 'active',
  next_available: true,
}

export const incorrectFinalAnswer: AnswerResponse = {
  ...correctAnswer,
  result: 'incorrect',
  position: 2,
  session_status: 'finished',
  next_available: false,
}

export const sessionSummary: SessionSummary = {
  session_id: SESSION_ID,
  status: 'finished',
  total_questions: 2,
  answered: 2,
  correct: 1,
  incorrect: 1,
  skipped: 0,
  accuracy: 0.5,
}

export const emptyReviewGuide: ReviewGuide = {
  generated_at: '2026-08-12T00:00:00Z',
  total_graded: 0,
  total_correct: 0,
  total_incorrect: 0,
  overall_accuracy: 0,
  focus_areas: [],
  priority_domains: [],
}

export const reviewGuide: ReviewGuide = {
  generated_at: '2026-08-12T00:00:00Z',
  total_graded: 9,
  total_correct: 6,
  total_incorrect: 3,
  overall_accuracy: 6 / 9,
  priority_domains: [
    {
      rank: 1,
      domain: 'Domain 4: Security Operations',
      incorrect: 2,
      accuracy: 0.5,
      weakness_score: 1.4,
    },
  ],
  focus_areas: [
    {
      rank: 1,
      domain: 'Domain 4: Security Operations',
      subject: 'Privileged access management',
      correct: 1,
      incorrect: 2,
      accuracy: 0.33,
      weakness_score: 1.4,
      concepts: [
        {
          question_id: 'clean-d04-q004',
          prompt: 'Which solution BEST fits emergency database maintenance?',
          correct_choice: 'A PAM system that brokers and records a time-limited session',
          explanation: 'Privileged access management injects vaulted credentials just in time.',
          objective: 'Privileged session control',
          chapter: 'Chapter 10: Identity and Access Operations',
          correction_note: null,
        },
      ],
    },
  ],
}
