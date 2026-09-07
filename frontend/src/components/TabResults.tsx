import type { RecommendationResponse, TopicInput } from '../lib/types'
import { Award, TrendingUp, AlertTriangle, Calendar, RefreshCw, GraduationCap } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import CourseCard from './CourseCard'
import WeeklyFlow from './WeeklyFlow'

type Props = {
  recommendation: RecommendationResponse
  topicInput: TopicInput
  sessionId: string
  userId: string | null
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

export default function TabResults({ recommendation: r, topicInput, sessionId, userId, onRestart }: Props) {
  const pct = Math.round((r.score / r.total) * 100)
  const subjectLevels = Object.entries(r.level_by_subject)
  const [activeTab, setActiveTab] = useState<'weekly' | 'courses'>('weekly')

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Hero */}
      <motion.div variants={item} className="glass p-8 relative overflow-hidden">
        <div className="relative">
          <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
            <Award className="w-4 h-4" /> Your level for {topicInput.subjects.join(', ')}
          </div>
          <div className="flex items-end gap-4 flex-wrap">
            <h2 className="text-5xl font-display font-semibold text-amber-300 capitalize">{r.level}</h2>
            <div className="text-slate-400">
              <div className="text-3xl font-bold text-white">
                {r.score}/{r.total}
              </div>
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
            {r.strengths.length ? (
              r.strengths.map((s, i) => <li key={i}>• {s}</li>)
            ) : (
              <li className="text-slate-500">—</li>
            )}
          </ul>
        </div>
        <div className="glass p-6">
          <div className="flex items-center gap-2 text-sm text-slate-300 mb-3">
            <AlertTriangle className="w-4 h-4" /> Gaps to close
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            {r.gaps.length ? (
              r.gaps.map((s, i) => <li key={i}>• {s}</li>)
            ) : (
              <li className="text-slate-500">—</li>
            )}
          </ul>
        </div>
      </motion.div>

      {/* 3D Tab Navigation */}
      <motion.div variants={item} className="glass p-2">
        <div className="flex gap-2" style={{ perspective: '1000px' }}>
          <motion.button
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab('weekly')}
            className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
              activeTab === 'weekly'
                ? 'bg-gradient-to-br from-amber-400/20 to-amber-500/10 border-2 border-amber-300/40 text-amber-300 shadow-lg shadow-amber-400/20'
                : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10 hover:text-slate-300'
            }`}
            style={{
              transformStyle: 'preserve-3d',
              transform: activeTab === 'weekly' ? 'translateZ(10px)' : 'translateZ(0px)',
              boxShadow:
                activeTab === 'weekly'
                  ? '0 8px 20px rgba(251,191,36,0.2), inset 0 1px 0 rgba(255,255,255,0.1)'
                  : 'none',
            }}
          >
            <Calendar className="w-5 h-5" />
            Weekly Plan
          </motion.button>
          <motion.button
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab('courses')}
            className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
              activeTab === 'courses'
                ? 'bg-gradient-to-br from-amber-400/20 to-amber-500/10 border-2 border-amber-300/40 text-amber-300 shadow-lg shadow-amber-400/20'
                : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10 hover:text-slate-300'
            }`}
            style={{
              transformStyle: 'preserve-3d',
              transform: activeTab === 'courses' ? 'translateZ(10px)' : 'translateZ(0px)',
              boxShadow:
                activeTab === 'courses'
                  ? '0 8px 20px rgba(251,191,36,0.2), inset 0 1px 0 rgba(255,255,255,0.1)'
                  : 'none',
            }}
          >
            <GraduationCap className="w-5 h-5" />
            All Courses ({r.courses.length})
          </motion.button>
        </div>
      </motion.div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'weekly' && (
          <motion.div
            key="weekly"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
            variants={item}
            className="glass p-6"
          >
            <WeeklyFlow
              recommendation={r}
              topicInput={topicInput}
              sessionId={sessionId}
              userId={userId}
            />
          </motion.div>
        )}

        {activeTab === 'courses' && (
          <motion.div
            key="courses"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            variants={item}
            className="glass p-6"
          >
            <h3 className="text-xl font-display font-semibold mb-1 flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-amber-300" />
              Your Complete Course Roadmap
            </h3>
            <p className="text-sm text-slate-400 mb-6">
              {r.courses.length} curated courses — foundational to advanced
            </p>

            <div className="grid md:grid-cols-2 gap-6">
              {r.courses.map((course, i) => (
                <CourseCard key={course.url} course={course} index={i} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div variants={item} className="flex justify-center">
        <motion.button
          whileHover={{ scale: 1.05, y: -2 }}
          whileTap={{ scale: 0.95 }}
          className="btn-ghost flex items-center gap-2 px-6 py-3"
          onClick={onRestart}
          style={{ boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
        >
          <RefreshCw className="w-4 h-4" /> Start over with new subjects
        </motion.button>
      </motion.div>
    </motion.div>
  )
}
