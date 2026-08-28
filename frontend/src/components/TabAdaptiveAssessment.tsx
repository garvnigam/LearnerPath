import { useEffect, useState } from 'react'
import type { MCQ, RecommendationResponse, TopicInput } from '../lib/types'
import { apiPost } from '../lib/api'
import { CheckCircle2, Brain, ListChecks, Sparkles, Target, TrendingUp, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import LoadingScene from './LoadingScene'

type Props = {
  userId: string | null
  sessionId: string
  topicInput: TopicInput
  focusAreas: string[]
  onSubmit: (rec: RecommendationResponse) => void
}

type AdaptiveResponse = {
  question: MCQ | null
  is_complete: boolean
  questions_per_subject: Record<string, number>
  message?: string
}

export default function TabAdaptiveAssessment({
  userId, sessionId, topicInput, focusAreas, onSubmit,
}: Props) {
  const [questions, setQuestions] = useState<MCQ[]>([])
  const [answers, setAnswers] = useState<Record<number, 'A' | 'B' | 'C' | 'D'>>({})
  const [currentQuestion, setCurrentQuestion] = useState<MCQ | null>(null)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [questionsPerSubject, setQuestionsPerSubject] = useState<Record<string, number>>({})
  const [isComplete, setIsComplete] = useState(false)

  // Fetch first question on mount
  useEffect(() => {
    fetchNextQuestion()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Auto-fetch next question when user answers current one
  useEffect(() => {
    if (currentQuestion && answers[currentQuestion.id] && !loading && !isComplete) {
      // Small delay for UX smoothness
      const timer = setTimeout(() => {
        fetchNextQuestion()
      }, 800)
      return () => clearTimeout(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [answers, currentQuestion?.id])

  async function fetchNextQuestion() {
    setLoading(true)
    setError(null)
    try {
      const response = await apiPost<AdaptiveResponse>('/api/assessment/adaptive', {
        session_id: sessionId,
        topic_input: topicInput,
        focus_areas: focusAreas,
        answered_questions: questions,
        answers,
      })

      setQuestionsPerSubject(response.questions_per_subject)

      if (response.is_complete) {
        setIsComplete(true)
        setCurrentQuestion(null)
        // Auto-submit after a brief moment
        setTimeout(() => {
          submitAssessment()
        }, 1500)
      } else if (response.question) {
        setQuestions([...questions, response.question])
        setCurrentQuestion(response.question)
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function submitAssessment() {
    setSubmitting(true)
    setError(null)
    try {
      const rec = await apiPost<RecommendationResponse>('/api/score', {
        user_id: userId,
        session_id: sessionId,
        topic_input: topicInput,
        focus_areas: focusAreas,
        questions,
        answers,
      })
      onSubmit(rec)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const totalAnswered = Object.keys(answers).length
  const totalQuestions = questions.length
  const minQuestions = topicInput.subjects.length * 5
  const maxQuestions = topicInput.subjects.length * 10

  if (submitting) {
    return (
      <LoadingScene
        title="Building your learning path"
        icons={[Brain, Target, ListChecks, Sparkles]}
        messages={[
          'Scoring every answer against difficulty and topic…',
          'Determining your level per subject…',
          'Matching courses from MIT, Stanford, Harvard, IITs…',
          'Assembling your week-by-week study plan…',
        ]}
      />
    )
  }

  if (error) return <div className="glass p-6 text-rose-400">{error}</div>

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      {/* Progress Header */}
      <div className="glass p-6 sticky top-24 z-10 backdrop-blur-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Brain className="w-5 h-5 text-amber-300" />
              Adaptive Assessment
            </h2>
            <p className="text-sm text-slate-400">
              {isComplete 
                ? 'Assessment complete! Generating your personalized path...'
                : 'Each question adapts to your level — answer to continue'}
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">
              {totalAnswered}
              <span className="text-slate-500">/{minQuestions}-{maxQuestions}</span>
            </div>
            <div className="text-xs text-slate-400">answered</div>
          </div>
        </div>

        {/* Per-subject progress */}
        <div className="flex flex-wrap gap-3">
          {topicInput.subjects.map((subject) => {
            const count = questionsPerSubject[subject] || 0
            return (
              <div key={subject} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
                <span className="text-xs text-slate-300">{subject}</span>
                <span className="text-xs font-bold text-amber-300">{count}/5-10</span>
                {count >= 5 && count < 10 && <TrendingUp className="w-3 h-3 text-green-400" />}
                {count >= 10 && <CheckCircle2 className="w-3 h-3 text-green-400" />}
              </div>
            )
          })}
        </div>

        {/* Overall progress bar */}
        <div className="mt-4 w-full h-2 rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full bg-amber-400/80 transition-all duration-500"
            style={{
              width: `${(totalAnswered / maxQuestions) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Completion State */}
      <AnimatePresence>
        {isComplete && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="glass p-8 text-center"
          >
            <CheckCircle2 className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold mb-2">Assessment Complete!</h3>
            <p className="text-slate-400">
              Answered {totalAnswered} questions across {topicInput.subjects.length} subjects
            </p>
            <p className="text-sm text-slate-500 mt-2">Analyzing your results...</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Current Question */}
      <AnimatePresence mode="wait">
        {currentQuestion && !isComplete && (
          <motion.div
            key={currentQuestion.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="glass p-6"
          >
            <div className="flex items-start gap-3 mb-4">
              <span className="w-10 h-10 rounded-md border border-amber-300/30 bg-amber-400/10 text-amber-300 flex items-center justify-center text-sm font-bold flex-shrink-0">
                {currentQuestion.id}
              </span>
              <div className="flex-1">
                <p className="font-medium leading-relaxed text-lg">{currentQuestion.question}</p>
                <div className="flex items-center gap-2 mt-3">
                  <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-400 capitalize">
                    {currentQuestion.difficulty}
                  </span>
                  {currentQuestion.subject && (
                    <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-300">
                      {currentQuestion.subject}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-3 pl-0 sm:pl-13">
              {currentQuestion.options.map((o) => {
                const active = answers[currentQuestion.id] === o.key
                return (
                  <motion.button
                    key={o.key}
                    whileHover={{ scale: active ? 1 : 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => !active && setAnswers({ ...answers, [currentQuestion.id]: o.key })}
                    disabled={active}
                    className={`text-left px-4 py-3 rounded-md border transition-all flex items-start gap-3
                      ${active
                        ? 'bg-amber-400/10 border-amber-300/50 cursor-default'
                        : 'bg-white/5 border-white/10 hover:bg-white/10 cursor-pointer'}`}
                  >
                    <span className={`w-7 h-7 rounded-md flex items-center justify-center text-xs font-bold flex-shrink-0 transition
                      ${active ? 'bg-amber-400/90 text-slate-950' : 'bg-white/10 text-slate-300'}`}>
                      {active ? <CheckCircle2 className="w-4 h-4" /> : o.key}
                    </span>
                    <span className="text-sm flex-1">{o.text}</span>
                  </motion.button>
                )
              })}
            </div>

            {loading && (
              <div className="mt-4 flex items-center justify-center gap-2 text-sm text-slate-400">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                >
                  <Sparkles className="w-4 h-4" />
                </motion.div>
                <span>Analyzing your answer and preparing next question...</span>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Previously answered questions (collapsed) */}
      {questions.length > 1 && (
        <details className="glass p-4">
          <summary className="cursor-pointer text-sm text-slate-400 hover:text-slate-300 transition">
            View previous {questions.length - 1} question{questions.length - 1 !== 1 ? 's' : ''}
          </summary>
          <div className="mt-4 space-y-3">
            {questions.slice(0, -1).map((q) => {
              const userAnswer = answers[q.id]
              const isCorrect = userAnswer === q.correct
              return (
                <div key={q.id} className="border border-white/10 rounded-md p-3 text-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold text-slate-500">Q{q.id}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-slate-400 capitalize">
                      {q.difficulty}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-slate-300">
                      {q.subject}
                    </span>
                    {isCorrect ? (
                      <CheckCircle2 className="w-4 h-4 text-green-400 ml-auto" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-rose-400 ml-auto" />
                    )}
                  </div>
                  <p className="text-slate-300 line-clamp-2">{q.question}</p>
                </div>
              )
            })}
          </div>
        </details>
      )}
    </motion.div>
  )
}
