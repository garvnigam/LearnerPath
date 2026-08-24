import type { RecommendationResponse, TopicInput } from '../lib/types'
import { Award, TrendingUp, AlertTriangle, Calendar, ExternalLink, RefreshCw, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

type Props = {
  recommendation: RecommendationResponse
  topicInput: TopicInput
  onRestart: () => void
}

const LEVEL_COLORS: Record<string, string> = {
  beginner: 'from-emerald-500 to-teal-500',
  intermediate: 'from-amber-500 to-orange-500',
  advanced: 'from-pink-500 to-purple-500',
}

const LEVEL_DOT: Record<string, string> = {
  beginner: 'bg-emerald-400',
  intermediate: 'bg-amber-400',
  advanced: 'bg-pink-400',
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
        <div className={`absolute inset-0 bg-gradient-to-br ${LEVEL_COLORS[r.level]} opacity-10`} />
        <div className={`pointer-events-none absolute -top-10 -right-10 w-64 h-64 rounded-full bg-gradient-to-br ${LEVEL_COLORS[r.level]} opacity-20 blur-3xl animate-float-slow`} />
        <div className="relative">
          <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
            <Award className="w-4 h-4" /> Your level for {topicInput.subjects.join(', ')}
          </div>
          <div className="flex items-end gap-4 flex-wrap">
            <h2 className={`text-5xl font-bold bg-gradient-to-r ${LEVEL_COLORS[r.level]} bg-clip-text text-transparent capitalize`}>
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
        <div className="glass p-6 hover:border-emerald-400/30 border border-transparent transition">
          <div className="flex items-center gap-2 text-sm text-emerald-400 mb-3">
            <TrendingUp className="w-4 h-4" /> Strengths
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            {r.strengths.length ? r.strengths.map((s, i) => <li key={i}>• {s}</li>) : <li className="text-slate-500">—</li>}
          </ul>
        </div>
        <div className="glass p-6 hover:border-amber-400/30 border border-transparent transition">
          <div className="flex items-center gap-2 text-sm text-amber-400 mb-3">
            <AlertTriangle className="w-4 h-4" /> Gaps to close
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            {r.gaps.length ? r.gaps.map((s, i) => <li key={i}>• {s}</li>) : <li className="text-slate-500">—</li>}
          </ul>
        </div>
      </motion.div>

      {/* Weekly plan timeline */}
      <motion.div variants={item} className="glass p-6">
        <div className="flex items-center gap-2 text-sm text-teal-400 mb-4">
          <Calendar className="w-4 h-4" /> Week-by-week plan
        </div>
        {r.weekly_plan.length ? (
          <div className="relative pl-6 space-y-4">
            <div className="absolute left-[11px] top-2 bottom-2 w-px bg-gradient-to-b from-emerald-500/50 via-teal-500/40 to-transparent" />
            {r.weekly_plan.map((w, i) => (
              <motion.div
                key={w.week}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="relative"
              >
                <span className="absolute -left-6 top-1 w-6 h-6 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-[11px] font-bold text-white shadow">
                  {w.week}
                </span>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <div className="text-xs text-teal-300 font-medium mb-1">Week {w.week}</div>
                  <p className="font-medium text-sm leading-relaxed mb-2">{w.focus}</p>
                  <div className="flex flex-wrap gap-2 text-xs text-slate-400 mb-2">
                    <span className="px-2 py-0.5 rounded-full bg-white/5 border border-white/10">
                      📘 {w.primary_resource}
                    </span>
                    {w.secondary_resource && (
                      <span className="px-2 py-0.5 rounded-full bg-white/5 border border-white/10">
                        📗 {w.secondary_resource}
                      </span>
                    )}
                  </div>
                  <div className="flex items-start gap-1.5 text-xs text-emerald-300/90">
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

      {/* Course roadmap: animated connected flow */}
      <motion.div variants={item} className="glass p-6 md:p-8">
        <h3 className="text-xl font-display font-semibold mb-1">Your course roadmap ({r.courses.length})</h3>
        <p className="text-sm text-slate-400 mb-6">Follow the path — foundational first, advanced last.</p>

        <div className="relative">
          {r.courses.map((c, i) => {
            const isLast = i === r.courses.length - 1
            const gradient = LEVEL_COLORS[c.level] ?? 'from-emerald-500 to-teal-500'
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
                  <span className={`relative z-10 w-10 h-10 rounded-full bg-gradient-to-br ${gradient} ring-4 ring-slate-950 flex items-center justify-center text-sm font-bold text-white shadow-lg`}>
                    {i + 1}
                  </span>
                  {!isLast && (
                    <>
                      <div className="absolute top-10 left-1/2 -translate-x-1/2 w-px h-[calc(100%-0.5rem)] bg-white/10" />
                      <motion.div
                        initial={{ scaleY: 0 }}
                        whileInView={{ scaleY: 1 }}
                        viewport={{ once: true, margin: '-40px' }}
                        transition={{ delay: i * 0.05 + 0.15, duration: 0.5, ease: 'easeOut' }}
                        style={{ transformOrigin: 'top' }}
                        className={`absolute top-10 left-1/2 -translate-x-1/2 w-px h-[calc(100%-0.5rem)] bg-gradient-to-b ${gradient}`}
                      />
                      <span className="absolute top-10 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_10px_2px_rgba(129,140,248,0.8)] animate-pulse-travel motion-reduce:hidden" />
                    </>
                  )}
                </div>

                {/* card */}
                <motion.a
                  href={c.url}
                  target="_blank"
                  rel="noreferrer"
                  whileHover={{ y: -2 }}
                  className="group flex-1 min-w-0 rounded-2xl border border-white/10 bg-white/5 hover:bg-white/[0.08] hover:border-teal-400/40 hover:shadow-lg hover:shadow-teal-500/10 transition p-4 block"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2 flex-wrap min-w-0">
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-teal-400/30 text-teal-300 truncate">
                        {c.provider}
                      </span>
                      <span className="text-[11px] text-slate-500 capitalize">{c.level}</span>
                    </div>
                    <span className="flex items-center gap-1 text-[11px] font-medium text-teal-300 opacity-0 group-hover:opacity-100 -translate-x-1 group-hover:translate-x-0 transition flex-shrink-0">
                      Open <ExternalLink className="w-3.5 h-3.5" />
                    </span>
                  </div>

                  <h4 className="font-semibold text-sm leading-snug group-hover:text-teal-300 transition line-clamp-2">
                    {c.title}
                  </h4>
                  <p className="mt-1.5 text-xs text-slate-400 line-clamp-2">{c.description}</p>

                  <div className="flex items-center gap-2 flex-wrap mt-3">
                    {c.format && c.format !== 'course' && (
                      <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-rose-500/15 border border-rose-400/30 text-rose-300 capitalize">
                        {c.format === 'playlist' ? '▶ Playlist' : c.format}
                      </span>
                    )}
                    {(() => {
                      const pt = c.price_type
                      if (!pt || pt === 'free') {
                        return (
                          <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-400/30 text-emerald-300">
                            Free
                          </span>
                        )
                      }
                      if (pt === 'audit_free') {
                        return (
                          <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-400/30 text-emerald-300">
                            Audit free
                          </span>
                        )
                      }
                      const price = c.price_amount ? `$${Math.round(c.price_amount)}` : 'Paid'
                      return (
                        <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-amber-500/15 border border-amber-400/30 text-amber-300">
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
