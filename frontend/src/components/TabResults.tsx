import type { RecommendationResponse, TopicInput } from '../lib/types'
import { Award, TrendingUp, AlertTriangle, Calendar, ExternalLink, RefreshCw } from 'lucide-react'
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

export default function TabResults({ recommendation: r, topicInput, onRestart }: Props) {
  const pct = Math.round((r.score / r.total) * 100)
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
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
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
        <div className="glass p-6">
          <div className="flex items-center gap-2 text-sm text-indigo-400 mb-3">
            <Calendar className="w-4 h-4" /> Weekly plan
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">{r.weekly_plan || '—'}</p>
        </div>
      </div>

      <div className="glass p-6">
        <h3 className="text-xl font-semibold mb-4">Your curated courses ({r.courses.length})</h3>
        <div className="grid md:grid-cols-2 gap-4">
          {r.courses.map((c, i) => (
            <motion.a
              key={c.url}
              href={c.url}
              target="_blank"
              rel="noreferrer"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="group glass !bg-white/5 hover:!bg-white/10 p-5 transition block"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-400/30 text-indigo-300">
                    {c.provider}
                  </span>
                  {c.format && c.format !== 'course' && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-400/30 text-rose-300 capitalize">
                      {c.format === 'playlist' ? '▶ Playlist' : c.format}
                    </span>
                  )}
                  <span className="text-xs text-slate-500 capitalize">{c.level}</span>
                </div>
                <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-indigo-400" />
              </div>
              <h4 className="font-semibold mb-1 group-hover:text-indigo-300 transition">{c.title}</h4>
              <p className="text-sm text-slate-400 line-clamp-3">{c.description}</p>
              {c.duration && <p className="text-xs text-slate-500 mt-2">⏱ {c.duration}</p>}
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
