import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, Loader2, Target } from 'lucide-react'
import type { MCQ } from '../lib/types'

type Props = {
  week: number
  attempt: number
  total: number
  passingScore: number
  questions: MCQ[]
  submitting: boolean
  onSubmit: (answers: Record<number, 'A' | 'B' | 'C' | 'D'>) => void
  onCancel: () => void
}

export default function WeekTest({
  week,
  attempt,
  total,
  passingScore,
  questions,
  submitting,
  onSubmit,
  onCancel,
}: Props) {
  const [answers, setAnswers] = useState<Record<number, 'A' | 'B' | 'C' | 'D'>>({})
  const answeredCount = useMemo(() => Object.keys(answers).length, [answers])
  const allAnswered = answeredCount === questions.length

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-6 border border-amber-300/25"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 mb-1">
        <h4 className="text-lg font-display font-semibold flex items-center gap-2">
          <Target className="w-5 h-5 text-amber-300" />
          Week {week} checkpoint test
        </h4>
        <div className="flex items-center gap-2 text-xs">
          {attempt > 1 && (
            <span className="px-2.5 py-1 rounded-full bg-white/10 border border-white/10 text-slate-300">
              Attempt {attempt}
            </span>
          )}
          <span className="px-2.5 py-1 rounded-full bg-amber-400/10 border border-amber-300/30 text-amber-300 font-medium">
            Pass mark {passingScore}/{total}
          </span>
        </div>
      </div>
      <p className="text-sm text-slate-400 mb-4">
        {total} questions, 1 mark each. Score {passingScore} or more to clear this week — below that we add a
        refresher on exactly what you missed.
      </p>

      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full bg-amber-400/80 transition-all duration-300"
            style={{ width: `${(answeredCount / questions.length) * 100}%` }}
          />
        </div>
        <span className="text-xs text-slate-400 tabular-nums">
          {answeredCount}/{questions.length}
        </span>
      </div>

      <div className="space-y-5">
        {questions.map((q, qi) => (
          <div key={q.id} className="border border-white/10 rounded-lg p-4 bg-white/[0.02]">
            <div className="flex items-start gap-3 mb-3">
              <span className="w-8 h-8 rounded-md border border-amber-300/30 bg-amber-400/10 text-amber-300 flex items-center justify-center text-sm font-bold flex-shrink-0">
                {qi + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="font-medium leading-relaxed">{q.question}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-400 capitalize">
                    {q.difficulty}
                  </span>
                  {q.subject && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-300">
                      {q.subject}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-2.5">
              {q.options.map(o => {
                const active = answers[q.id] === o.key
                return (
                  <button
                    key={o.key}
                    type="button"
                    disabled={submitting}
                    onClick={() => setAnswers(prev => ({ ...prev, [q.id]: o.key }))}
                    className={`text-left px-3 py-2.5 rounded-md border transition-all flex items-start gap-3
                      ${active
                        ? 'bg-amber-400/10 border-amber-300/50'
                        : 'bg-white/5 border-white/10 hover:bg-white/10'}
                      ${submitting ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    <span
                      className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold flex-shrink-0 transition
                        ${active ? 'bg-amber-400/90 text-slate-950' : 'bg-white/10 text-slate-300'}`}
                    >
                      {active ? <CheckCircle2 className="w-3.5 h-3.5" /> : o.key}
                    </span>
                    <span className="text-sm flex-1">{o.text}</span>
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3 mt-6">
        <button
          type="button"
          className="btn-primary flex items-center gap-2"
          disabled={!allAnswered || submitting}
          onClick={() => onSubmit(answers)}
        >
          {submitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" /> Scoring…
            </>
          ) : (
            <>Submit test</>
          )}
        </button>
        <button type="button" className="btn-ghost" disabled={submitting} onClick={onCancel}>
          Back
        </button>
        {!allAnswered && (
          <span className="text-xs text-slate-500">
            Answer all {questions.length} questions to submit.
          </span>
        )}
      </div>
    </motion.div>
  )
}
