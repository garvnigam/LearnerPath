export type TopicInput = {
  user_id?: string | null
  subjects: string[]
  duration_months: number
  hours_per_day: number
  goal?: string
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
  question: string
  options: MCQOption[]
  correct: 'A' | 'B' | 'C' | 'D'
  explanation: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
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
}

export type RecommendationResponse = {
  level: 'beginner' | 'intermediate' | 'advanced'
  score: number
  total: number
  strengths: string[]
  gaps: string[]
  weekly_plan: string
  courses: Course[]
}
