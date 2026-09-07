import { motion } from 'framer-motion'
import { ExternalLink } from 'lucide-react'
import type { Course } from '../lib/types'

type Props = {
  course: Course
  /** 1-based badge shown in the corner (omit to hide) */
  index?: number
  /** small label above the title, e.g. "Primary" / "Secondary" */
  roleLabel?: string
}

export default function CourseCard({ course, index, roleLabel }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: (index || 0) * 0.05 }}
      className="group relative"
      style={{ transformStyle: 'preserve-3d', perspective: '1000px' }}
    >
      <div className="relative">
        {/* 3D shadow layers */}
        <div className="pointer-events-none absolute inset-0 bg-amber-400/5 rounded-lg translate-x-2 translate-y-2 blur-sm" />
        <div className="pointer-events-none absolute inset-0 bg-amber-400/10 rounded-lg translate-x-1 translate-y-1" />

        <motion.div
          whileHover={{ y: -4, rotateX: 2, rotateY: -2, transition: { duration: 0.2 } }}
          className="relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 border border-white/10 rounded-lg p-5 backdrop-blur-sm hover:border-amber-300/30 transition-all duration-300"
          style={{
            transformStyle: 'preserve-3d',
            boxShadow: '0 10px 30px rgba(0,0,0,0.3), 0 1px 8px rgba(251,191,36,0.1)',
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-amber-400/0 via-amber-400/5 to-amber-400/0 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg pointer-events-none" />

          <div className="relative z-10">
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-center gap-2 flex-wrap min-w-0">
                {roleLabel && (
                  <span className="text-xs px-2.5 py-1 rounded-full bg-amber-400/10 border border-amber-300/30 text-amber-300 font-medium">
                    {roleLabel}
                  </span>
                )}
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
                  <span
                    key={ti}
                    className="text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-400"
                  >
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
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="relative z-20 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-400/10 hover:bg-amber-400/20 border border-amber-300/30 hover:border-amber-300/50 text-amber-300 text-sm font-medium transition-all"
            >
              <ExternalLink className="w-4 h-4" />
              Open Course
            </motion.a>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}
