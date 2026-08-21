import type { RecommendationResponse, TopicInput } from '../lib/types'
import { Award, TrendingUp, AlertTriangle, Calendar, ExternalLink, RefreshCw, ArrowRight, CheckCircle2, ArrowDown } from 'lucide-react'
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

export default function TabResults({ recommendation: r, topicInput, onRestart }: Props) {
  const pct = Math.round((r.score / r.total) * 100)
  const subjectLevels = Object.entries(r.level_by_subject)

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Hero */}
      <div className="glass p-8 relative overflow-hidden">
        <div className={`absolute inset-0 bg-gradient-to-br ${LEVEL_COLORS[r.level]} opacity-10`} />
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
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="glass p-6">
          <div className="flex items-center gap-2 text-sm text-emerald-400 mb-3">
            <TrendingUp className="w-4 h-4" /> Strengths
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            {r.strengths.length ? r.strengths.map((s, i) => <li key={i}>• {s}</li>) : <li className="text-slate-500">—</li>}
          </ul>
        </div>
        <div className="glass p-6">
          <div className="flex items-center gap-2 text-sm text-amber-400 mb-3">
            <AlertTriangle className="w-4 h-4" /> Gaps to close
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            {r.gaps.length ? r.gaps.map((s, i) => <li key={i}>• {s}</li>) : <li className="text-slate-500">—</li>}
          </ul>
        </div>
      </div>

      {/* Weekly plan timeline */}
      <div className="glass p-6">
        <div className="flex items-center gap-2 text-sm text-indigo-400 mb-4">
          <Calendar className="w-4 h-4" /> Week-by-week plan
        </div>
        {r.weekly_plan.length ? (
          <div className="relative pl-6 space-y-4">
            <div className="absolute left-[11px] top-2 bottom-2 w-px bg-gradient-to-b from-indigo-500/50 via-purple-500/40 to-transparent" />
            {r.weekly_plan.map((w, i) => (
              <motion.div
                key={w.week}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="relative"
              >
                <span className="absolute -left-6 top-1 w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-[11px] font-bold text-white shadow">
                  {w.week}
                </span>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <div className="text-xs text-indigo-300 font-medium mb-1">Week {w.week}</div>
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
      </div>

      {/* Course roadmap: boxes + arrows */}
      <div className="glass p-6">
        <h3 className="text-xl font-semibold mb-1">Your course roadmap ({r.courses.length})</h3>
        <p className="text-sm text-slate-400 mb-5">Follow the arrows — foundational first, advanced last.</p>

        <div className="flex flex-wrap items-center gap-x-2 gap-y-6">
          {r.courses.map((c, i) => (
            <div key={c.url} className="flex items-center gap-2">
              <motion.a
                href={c.url}
                target="_blank"
                rel="noreferrer"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="group relative w-64 flex-shrink-0 rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-indigo-400/40 transition p-4 block"
              >
                <span className="absolute -top-3 -left-3 w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-xs font-bold text-white shadow">
                  {i + 1}
                </span>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-400/30 text-indigo-300 truncate">
                    {c.provider}
                  </span>
                  <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-400 flex-shrink-0" />
                </div>
                <h4 className="font-semibold text-sm mb-1 leading-snug group-hover:text-indigo-300 transition line-clamp-2">
                  {c.title}
                </h4>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] text-slate-500 capitalize">{c.level}</span>
                  {c.format && c.format !== 'course' && (
                    <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-rose-500/15 border border-rose-400/30 text-rose-300 capitalize">
                      {c.format === 'playlist' ? '▶ Playlist' : c.format}
                    </span>
                  )}
                </div>
              </motion.a>

              {i < r.courses.length - 1 && (
                <>
                  <ArrowRight className="hidden sm:block w-6 h-6 text-indigo-400/60 flex-shrink-0" />
                  <ArrowDown className="block sm:hidden w-5 h-5 text-indigo-400/60 flex-shrink-0" />
                </>
              )}
            </div>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-3 mt-6">
          {r.courses.map((c, i) => (
            <motion.a
              key={`desc-${c.url}`}
              href={c.url}
              target="_blank"
              rel="noreferrer"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.04 }}
              className="text-xs text-slate-400 hover:text-slate-300 bg-white/[0.02] border border-white/5 rounded-lg p-3 line-clamp-3"
            >
              <span className="font-medium text-slate-300">{i + 1}. {c.title}</span> — {c.description}
            </motion.a>
          ))}
        </div>
      </div>

      <div className="flex justify-center">
        <button className="btn-ghost flex items-center gap-2" onClick={onRestart}>
          <RefreshCw className="w-4 h-4" /> Start over with new subjects
        </button>
      </div>
    </motion.div>
  )
}
