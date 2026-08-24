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

export type SavedPlanResponse = {
  topic_input: TopicInput
  recommendation: RecommendationResponse
}
