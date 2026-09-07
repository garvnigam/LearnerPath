export type GoalType = 'job' | 'certification' | 'project' | 'curiosity' | 'exam_prep'
export type FormatPref = 'video' | 'text' | 'hands-on'
export type PacePref = 'solo' | 'cohort' | 'paced'
export type BudgetPref = 'strictly_free' | 'free_and_audit' | 'free_and_paid'

export type TopicInput = {
  user_id?: string | null
  subjects: string[]
  duration_months: number
  hours_per_day: number
  goal?: GoalType
  preferred_formats: FormatPref[]
  pace?: PacePref
  budget: BudgetPref
}

export type ChatMessage = { role: 'user' | 'assistant' | 'system'; content: string }

export type ChatResponse = {
  message: ChatMessage
  ready_for_assessment: boolean
  focus_areas: string[]
}

export type MCQOption = { key: 'A' | 'B' | 'C' | 'D'; text: string }
export type MCQ = {
  id: number
  subject: string
  question: string
  options: MCQOption[]
  correct: 'A' | 'B' | 'C' | 'D'
  explanation: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  concepts?: string[]
}

export type Course = {
  title: string
  provider: string
  url: string
  level: string
  description: string
  duration?: string | null
  image?: string | null
  topics: string[]
  format?: 'course' | 'playlist' | 'lectures' | null
  price_type?: 'free' | 'audit_free' | 'paid' | 'freemium' | null
  price_amount?: number | null
  price_currency?: string | null
  certificate_price?: number | null
}

export type WeekPlan = {
  week: number
  focus: string
  primary_resource: string
  secondary_resource?: string | null
  checkpoint: string
}

export type RecommendationResponse = {
  level: 'beginner' | 'intermediate' | 'advanced'
  level_by_subject: Record<string, 'beginner' | 'intermediate' | 'advanced'>
  score: number
  total: number
  strengths: string[]
  gaps: string[]
  weekly_plan: WeekPlan[]
  courses: Course[]
}

export const WEEK_TEST_TOTAL = 10
export const WEEK_TEST_PASSING = 8

export type WeekTestRequest = {
  user_id?: string | null
  session_id: string
  topic_input: TopicInput
  week: number
  week_focus: string
  resources: string[]
  subjects?: string[]
  level: 'beginner' | 'intermediate' | 'advanced'
  attempt: number
  weak_concepts?: string[]
  covered_concepts?: string[]
}

export type WeekTestResponse = {
  week: number
  attempt: number
  total: number
  passing_score: number
  questions: MCQ[]
}

export type RefresherResource = {
  title: string
  kind: 'text' | 'video' | 'practice'
  url?: string | null
  provider?: string | null
  why: string
}

export type RefresherModule = {
  week: number
  title: string
  weak_concepts: string[]
  summary: string
  notes: string
  est_minutes: number
  resources: RefresherResource[]
}

export type WeekTestSubmitResponse = {
  week: number
  attempt: number
  score: number
  total: number
  passing_score: number
  passed: boolean
  correct_concepts: string[]
  weak_concepts: string[]
  refresher?: RefresherModule | null
}

/** Where a week sits in the completion → test → refresher → retest loop. */
export type WeekStatus =
  | 'locked'
  | 'in_progress'
  | 'testing'
  | 'refresher'
  | 'passed'
  | 'skipped'

export type WeekProgress = {
  status: WeekStatus
  attempts: number
  bestScore: number | null
  lastScore: number | null
  weakConcepts: string[]
  coveredConcepts: string[]
  refresher: RefresherModule | null
  refresherDone: boolean
}

export type SavedPlanResponse = {
  topic_input: TopicInput
  recommendation: RecommendationResponse
}
