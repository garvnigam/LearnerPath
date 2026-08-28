import type { RecommendationResponse, TopicInput } from '../lib/types'
import { Award, TrendingUp, AlertTriangle, Calendar, ExternalLink, RefreshCw, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

type Props = {
  recommendation: RecommendationResponse
  topicInput: TopicInput
  onRestart: () => void
}

const LEVEL_DOT: Record<string, string> = {
  beginner: 'bg-slate-400',
  intermediate: 'bg-amber-300',
  advanced: 'bg-slate-100',
}

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
}
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0 },
}

export default function TabResults({ recommendation: r, topicInput, onRestart }: Props) {
  const pct = Math.round((r.score / r.total) * 100)
  const subjectLevels = Object.entries(r.level_by_subject)

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Hero */}
      <motion.div variants={item} className="glass p-8 relative overflow-hidden">
        <div className="relative">
          <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
            <Award className="w-4 h-4" /> Your level for {topicInput.subjects.join(', ')}
          </div>
          <div className="flex items-end gap-4 flex-wrap">
            <h2 className="text-5xl font-display font-semibold text-amber-300 capitalize">
              {r.level}
            </h2>
            <div className="text-slate-400">
              <div className="text-3xl font-bold text-white">{r.score}/{r.total}</div>
              <div className="text-xs">{pct}% correct</div>
            </div>
          </div>

          {subjectLevels.length > 1 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {subjectLevels.map(([subj, lvl]) => (
                <span
                  key={subj}
                  className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10"
                >
                  <span className={`w-2 h-2 rounded-full ${LEVEL_DOT[lvl]}`} />
                  {subj} <span className="text-slate-400 capitalize">· {lvl}</span>
                </span>
              ))}
            </div>
          )}
        </div>
      </motion.div>

      <motion.div variants={item} className="grid md:grid-cols-2 gap-4">
        <div className="glass p-6">
          <div className="flex items-center gap-2 text-sm text-slate-300 mb-3">
            <TrendingUp className="w-4 h-4" /> Strengths
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            {r.strengths.length ? r.strengths.map((s, i) => <li key={i}>• {s}</li>) : <li className="text-slate-500">—</li>}
          </ul>
        </div>
        <div className="glass p-6">
          <div className="flex items-center gap-2 text-sm text-slate-300 mb-3">
            <AlertTriangle className="w-4 h-4" /> Gaps to close
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            {r.gaps.length ? r.gaps.map((s, i) => <li key={i}>• {s}</li>) : <li className="text-slate-500">—</li>}
          </ul>
        </div>
      </motion.div>

      {/* Weekly plan timeline */}
      <motion.div variants={item} className="glass p-6">
        <div className="flex items-center gap-2 text-sm text-slate-300 mb-4">
          <Calendar className="w-4 h-4" /> Week-by-week plan
        </div>
        {r.weekly_plan.length ? (
          <div className="relative pl-6 space-y-4">
            <div className="absolute left-[11px] top-2 bottom-2 w-px bg-white/10" />
            {r.weekly_plan.map((w, i) => (
              <motion.div
                key={w.week}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="relative"
              >
                <span className="absolute -left-6 top-1 w-6 h-6 rounded-full border border-amber-300/30 bg-amber-400/10 flex items-center justify-center text-[11px] font-bold text-amber-300 shadow">
                  {w.week}
                </span>
                <div className="bg-white/5 border border-white/10 rounded-md p-4">
                  <div className="label-caps mb-1">Week {w.week}</div>
                  <p className="font-medium text-sm leading-relaxed mb-2">{w.focus}</p>
                  <div className="flex flex-wrap gap-2 text-xs text-slate-400 mb-2">
                    <span className="px-2 py-0.5 rounded-full bg-white/5 border border-white/10">
                      {w.primary_resource}
                    </span>
                    {w.secondary_resource && (
                      <span className="px-2 py-0.5 rounded-full bg-white/5 border border-white/10">
                        {w.secondary_resource}
                      </span>
                    )}
                  </div>
                  <div className="flex items-start gap-1.5 text-xs text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                    <span>{w.checkpoint}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">—</p>
        )}
      </motion.div>

      {/* Course roadmap: connected flow */}
      <motion.div variants={item} className="glass p-6 md:p-8">
        <h3 className="text-xl font-display font-semibold mb-1">Your course roadmap ({r.courses.length})</h3>
        <p className="text-sm text-slate-400 mb-6">Follow the path — foundational first, advanced last.</p>

        <div className="relative">
          {r.courses.map((c, i) => {
            const isLast = i === r.courses.length - 1
            return (
              <motion.div
                key={c.url}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ delay: i * 0.05, duration: 0.4 }}
                className={`relative flex gap-5 ${isLast ? '' : 'pb-9'}`}
              >
                {/* node + connector */}
                <div className="relative flex-shrink-0 w-10 flex flex-col items-center">
                  <span className="relative z-10 w-10 h-10 rounded-full border border-amber-300/30 bg-amber-400/10 ring-4 ring-slate-950 flex items-center justify-center text-sm font-bold text-amber-300">
                    {i + 1}
                  </span>
                  {!isLast && (
                    <div className="absolute top-10 left-1/2 -translate-x-1/2 w-px h-[calc(100%-0.5rem)] bg-white/10" />
                  )}
                </div>

                {/* card */}
                <motion.a
                  href={c.url}
                  target="_blank"
                  rel="noreferrer"
                  whileHover={{ y: -2 }}
                  className="group flex-1 min-w-0 rounded-md border border-white/10 bg-white/5 hover:bg-white/[0.08] hover:border-white/20 transition p-4 block"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2 flex-wrap min-w-0">
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-300 truncate">
                        {c.provider}
                      </span>
                      <span className="text-[11px] text-slate-500 capitalize">{c.level}</span>
                    </div>
                    <span className="flex items-center gap-1 text-[11px] font-medium text-amber-300 opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition flex-shrink-0">
                      Open <ExternalLink className="w-3.5 h-3.5" />
                    </span>
                  </div>

                  <h4 className="font-semibold text-sm leading-snug group-hover:text-amber-300 transition line-clamp-2">
                    {c.title}
                  </h4>
                  <p className="mt-1.5 text-xs text-slate-400 line-clamp-2">{c.description}</p>

                  <div className="flex items-center gap-2 flex-wrap mt-3">
                    {c.format && c.format !== 'course' && (
                      <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-300 capitalize">
                        {c.format === 'playlist' ? 'Playlist' : c.format}
                      </span>
                    )}
                    {(() => {
                      const pt = c.price_type
                      if (!pt || pt === 'free') {
                        return (
                          <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-300">
                            Free
                          </span>
                        )
                      }
                      if (pt === 'audit_free') {
                        return (
                          <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-300">
                            Audit free
                          </span>
                        )
                      }
                      const price = c.price_amount ? `$${Math.round(c.price_amount)}` : 'Paid'
                      return (
                        <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-amber-400/10 border border-amber-300/30 text-amber-300">
                          {price}
                        </span>
                      )
                    })()}
                  </div>
                </motion.a>
              </motion.div>
            )
          })}
        </div>
      </motion.div>

      <motion.div variants={item} className="flex justify-center">
        <button className="btn-ghost flex items-center gap-2" onClick={onRestart}>
          <RefreshCw className="w-4 h-4" /> Start over with new subjects
        </button>
      </motion.div>
    </motion.div>
  )
}
