import type { RecommendationResponse, TopicInput, Course } from '../lib/types'
import { Award, TrendingUp, AlertTriangle, Calendar, ExternalLink, RefreshCw, CheckCircle2, ChevronDown, BookOpen, GraduationCap } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'

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
  const [activeTab, setActiveTab] = useState<'weekly' | 'courses'>('weekly')
  const [expandedWeek, setExpandedWeek] = useState<number | null>(null)

  const findCourseForWeek = (weekPlan: typeof r.weekly_plan[0]): Course | undefined => {
    return r.courses.find(c => c.title === weekPlan.primary_resource)
  }

  const CourseCard = ({ course, index }: { course: Course; index?: number }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: (index || 0) * 0.05 }}
      className="group relative"
      style={{
        transformStyle: 'preserve-3d',
        perspective: '1000px',
      }}
    >
      {/* 3D Card with shadow layers */}
      <div className="relative">
        {/* Shadow layer 1 (deepest) */}
        <div className="absolute inset-0 bg-amber-400/5 rounded-lg translate-x-2 translate-y-2 blur-sm" />
        {/* Shadow layer 2 */}
        <div className="absolute inset-0 bg-amber-400/10 rounded-lg translate-x-1 translate-y-1" />
        
        {/* Main card */}
        <motion.div
          whileHover={{ 
            y: -4,
            rotateX: 2,
            rotateY: -2,
            transition: { duration: 0.2 }
          }}
          className="relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 border border-white/10 rounded-lg p-5 backdrop-blur-sm hover:border-amber-300/30 transition-all duration-300"
          style={{
            transformStyle: 'preserve-3d',
            boxShadow: '0 10px 30px rgba(0,0,0,0.3), 0 1px 8px rgba(251,191,36,0.1)',
          }}
        >
          {/* Shine effect on hover */}
          <div className="absolute inset-0 bg-gradient-to-br from-amber-400/0 via-amber-400/5 to-amber-400/0 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg pointer-events-none" />
          
          <div className="relative z-10">
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-center gap-2 flex-wrap min-w-0">
                <span className="text-xs px-2.5 py-1 rounded-full bg-white/10 border border-white/10 text-slate-300 font-medium">
                  {course.provider}
                </span>
                <span className="text-xs text-slate-500 capitalize font-medium">{course.level}</span>
              </div>
              {index !== undefined && (
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-amber-400/20 border border-amber-300/30 flex items-center justify-center text-sm font-bold text-amber-300">
                  {index + 1}
                </span>
              )}
            </div>

            <h4 className="font-semibold text-base leading-snug group-hover:text-amber-300 transition mb-2">
              {course.title}
            </h4>
            <p className="text-sm text-slate-400 line-clamp-2 mb-4">{course.description}</p>

            <div className="flex items-center gap-2 flex-wrap mb-4">
              {course.format && course.format !== 'course' && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 border border-white/10 text-slate-300 capitalize">
                  {course.format === 'playlist' ? 'Playlist' : course.format}
                </span>
              )}
              {(() => {
                const pt = course.price_type
                if (!pt || pt === 'free') {
                  return (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-green-400/10 border border-green-400/30 text-green-300 font-medium">
                      Free
                    </span>
                  )
                }
                if (pt === 'audit_free') {
                  return (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-400/10 border border-blue-400/30 text-blue-300 font-medium">
                      Audit free
                    </span>
                  )
                }
                const price = course.price_amount ? `$${Math.round(course.price_amount)}` : 'Paid'
                return (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-amber-400/10 border border-amber-300/30 text-amber-300 font-medium">
                    {price}
                  </span>
                )
              })()}
            </div>

            {course.topics && course.topics.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {course.topics.slice(0, 5).map((topic, ti) => (
                  <span key={ti} className="text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-400">
                    {topic}
                  </span>
                ))}
                {course.topics.length > 5 && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-500">
                    +{course.topics.length - 5}
                  </span>
                )}
              </div>
            )}

            <motion.a
              href={course.url}
              target="_blank"
              rel="noreferrer"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-400/10 hover:bg-amber-400/20 border border-amber-300/30 hover:border-amber-300/50 text-amber-300 text-sm font-medium transition-all"
            >
              <ExternalLink className="w-4 h-4" />
              Open Course
            </motion.a>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )

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
              boxShadow: activeTab === 'weekly' 
                ? '0 8px 20px rgba(251,191,36,0.2), inset 0 1px 0 rgba(255,255,255,0.1)' 
                : 'none'
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
              boxShadow: activeTab === 'courses' 
                ? '0 8px 20px rgba(251,191,36,0.2), inset 0 1px 0 rgba(255,255,255,0.1)' 
                : 'none'
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
            <h3 className="text-xl font-display font-semibold mb-1 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-amber-300" />
              Week-by-Week Learning Path
            </h3>
            <p className="text-sm text-slate-400 mb-6">Click any week to see the course details</p>

            {r.weekly_plan.length ? (
              <div className="space-y-3">
                {r.weekly_plan.map((w, i) => {
                  const matchedCourse = findCourseForWeek(w)
                  const isExpanded = expandedWeek === w.week
                  return (
                    <motion.div
                      key={w.week}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      style={{ perspective: '1000px', transformStyle: 'preserve-3d' }}
                    >
                      {/* Week Card (3D) */}
                      <motion.div
                        whileHover={{ y: -2, rotateX: 1 }}
                        onClick={() => setExpandedWeek(isExpanded ? null : w.week)}
                        className="relative cursor-pointer group"
                        style={{ transformStyle: 'preserve-3d' }}
                      >
                        {/* Shadow layers */}
                        <div className="absolute inset-0 bg-white/5 rounded-lg translate-x-1 translate-y-1 blur-sm" />
                        
                        <div className={`relative bg-gradient-to-br from-slate-800/80 to-slate-900/80 border rounded-lg p-5 transition-all duration-300 ${
                          isExpanded 
                            ? 'border-amber-300/40 bg-amber-400/5' 
                            : 'border-white/10 hover:border-white/20'
                        }`}
                        style={{
                          boxShadow: isExpanded 
                            ? '0 8px 24px rgba(251,191,36,0.15), 0 2px 8px rgba(0,0,0,0.2)'
                            : '0 4px 12px rgba(0,0,0,0.1)'
                        }}>
                          <div className="flex items-start gap-4">
                            {/* Week number badge */}
                            <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-amber-400/30 to-amber-500/20 border-2 border-amber-300/40 flex items-center justify-center font-bold text-amber-300 text-lg"
                              style={{
                                boxShadow: '0 4px 12px rgba(251,191,36,0.2), inset 0 1px 0 rgba(255,255,255,0.1)'
                              }}>
                              {w.week}
                            </div>

                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-2">
                                <div className="label-caps text-amber-300/80">Week {w.week}</div>
                                <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} />
                              </div>
                              <p className="font-semibold text-base leading-relaxed mb-3">{w.focus}</p>
                              
                              <div className="flex flex-wrap gap-2 mb-3">
                                <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-white/10 border border-white/10 text-slate-300">
                                  <BookOpen className="w-3 h-3" />
                                  {w.primary_resource}
                                </span>
                                {w.secondary_resource && (
                                  <span className="text-xs px-2.5 py-1 rounded-full bg-white/10 border border-white/10 text-slate-400">
                                    {w.secondary_resource}
                                  </span>
                                )}
                              </div>
                              
                              <div className="flex items-start gap-2 text-xs text-slate-400">
                                <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-400" />
                                <span>{w.checkpoint}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </motion.div>

                      {/* Expanded Course Card */}
                      <AnimatePresence>
                        {isExpanded && matchedCourse && (
                          <motion.div
                            initial={{ opacity: 0, height: 0, y: -20 }}
                            animate={{ opacity: 1, height: 'auto', y: 0 }}
                            exit={{ opacity: 0, height: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                            className="mt-3 ml-16"
                          >
                            <CourseCard course={matchedCourse} />
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm text-slate-500">—</p>
            )}
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
          style={{
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
          }}
        >
          <RefreshCw className="w-4 h-4" /> Start over with new subjects
        </motion.button>
      </motion.div>
    </motion.div>
  )
}
