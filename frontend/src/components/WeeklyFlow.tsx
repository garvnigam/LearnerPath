import { useCallback, useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  AlertTriangle,
  BookOpen,
  Calendar,
  CheckCircle2,
  ChevronDown,
  Lock,
  Loader2,
  RotateCcw,
  SkipForward,
  Target,
  Trophy,
} from 'lucide-react'
import type {
  RecommendationResponse,
  TopicInput,
  WeekPlan,
  WeekProgress,
  WeekStatus,
  WeekTestResponse,
  WeekTestSubmitResponse,
} from '../lib/types'
import { WEEK_TEST_PASSING, WEEK_TEST_TOTAL } from '../lib/types'
import { findCoursesForWeek, unresolvedResources } from '../lib/courseMatch'
import { apiPost } from '../lib/api'
import CourseCard from './CourseCard'
import WeekTest from './WeekTest'
import WeekRefresher from './WeekRefresher'

type Props = {
  recommendation: RecommendationResponse
  topicInput: TopicInput
  sessionId: string
  userId: string | null
}

const EMPTY_PROGRESS: WeekProgress = {
  status: 'locked',
  attempts: 0,
  bestScore: null,
  lastScore: null,
  weakConcepts: [],
  coveredConcepts: [],
  refresher: null,
  refresherDone: false,
}

const STATUS_STYLE: Record<WeekStatus, { label: string; badge: string; border: string; dot: string }> = {
  locked: {
    label: 'Locked',
    badge: 'bg-white/5 border-white/10 text-slate-500',
    border: 'border-white/5',
    dot: 'from-white/10 to-white/5 border-white/10 text-slate-500',
  },
  in_progress: {
    label: 'In progress',
    badge: 'bg-amber-400/10 border-amber-300/30 text-amber-300',
    border: 'border-white/10 hover:border-white/20',
    dot: 'from-amber-400/30 to-amber-500/20 border-amber-300/40 text-amber-300',
  },
  testing: {
    label: 'Test in progress',
    badge: 'bg-blue-400/10 border-blue-400/30 text-blue-300',
    border: 'border-blue-400/30',
    dot: 'from-blue-400/30 to-blue-500/20 border-blue-400/40 text-blue-200',
  },
  refresher: {
    label: 'Refresher added',
    badge: 'bg-rose-400/10 border-rose-400/30 text-rose-300',
    border: 'border-rose-400/30',
    dot: 'from-rose-400/30 to-rose-500/20 border-rose-400/40 text-rose-200',
  },
  passed: {
    label: 'Passed',
    badge: 'bg-green-400/10 border-green-400/30 text-green-300',
    border: 'border-green-400/25',
    dot: 'from-green-400/30 to-green-500/20 border-green-400/40 text-green-300',
  },
  skipped: {
    label: 'Skipped',
    badge: 'bg-white/10 border-white/20 text-slate-300',
    border: 'border-white/15',
    dot: 'from-white/15 to-white/5 border-white/20 text-slate-300',
  },
}

/** Stable-ish key so a learner's week progress survives a page reload. */
function progressKey(topicInput: TopicInput, weeks: WeekPlan[]): string {
  const sig = [
    topicInput.subjects.join('|').toLowerCase(),
    topicInput.duration_months,
    weeks.length,
    weeks[0]?.focus?.slice(0, 24) ?? '',
  ].join('::')
  let h = 0
  for (let i = 0; i < sig.length; i++) {
    h = (h * 31 + sig.charCodeAt(i)) | 0
  }
  return `learnpath:weekflow:${Math.abs(h).toString(36)}`
}

function loadProgress(key: string): Record<number, WeekProgress> {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return typeof parsed === 'object' && parsed ? parsed : {}
  } catch {
    return {}
  }
}

/** Connector between two nodes in the flow. */
function Arrow({ tone = 'idle' }: { tone?: 'idle' | 'done' | 'warn' }) {
  const color =
    tone === 'done' ? 'bg-green-400/40' : tone === 'warn' ? 'bg-rose-400/40' : 'bg-white/15'
  const chevron =
    tone === 'done' ? 'text-green-400/60' : tone === 'warn' ? 'text-rose-400/60' : 'text-slate-600'
  return (
    <div className="flex flex-col items-center py-1.5 ml-6" aria-hidden>
      <div className={`w-px h-5 ${color}`} />
      <ChevronDown className={`w-4 h-4 -mt-1 ${chevron}`} />
    </div>
  )
}

export default function WeeklyFlow({ recommendation: r, topicInput, sessionId, userId }: Props) {
  const weeks = r.weekly_plan
  const storageKey = useMemo(() => progressKey(topicInput, weeks), [topicInput, weeks])

  const [progress, setProgress] = useState<Record<number, WeekProgress>>(() => loadProgress(storageKey))
  const [expandedWeek, setExpandedWeek] = useState<number | null>(weeks[0]?.week ?? null)
  const [activeTest, setActiveTest] = useState<WeekTestResponse | null>(null)
  const [busyWeek, setBusyWeek] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setProgress(loadProgress(storageKey))
    setActiveTest(null)
    setError(null)
  }, [storageKey])

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(progress))
    } catch {
      /* storage can be unavailable (private mode) — progress just won't persist */
    }
  }, [storageKey, progress])

  const getProgress = useCallback(
    (week: number, index: number): WeekProgress => {
      const stored = progress[week]
      if (stored) return stored
      // First week starts open; the rest wait on the previous week.
      return { ...EMPTY_PROGRESS, status: index === 0 ? 'in_progress' : 'locked' }
    },
    [progress],
  )

  const patch = (week: number, next: Partial<WeekProgress>, index: number) =>
    setProgress(prev => {
      const current = prev[week] ?? { ...EMPTY_PROGRESS, status: index === 0 ? 'in_progress' : 'locked' }
      return { ...prev, [week]: { ...current, ...next } }
    })

  const weekMeta = useMemo(
    () =>
      weeks.map((w, i) => {
        const matched = findCoursesForWeek(w, r.courses, weeks)
        return {
          plan: w,
          index: i,
          matched,
          unresolved: unresolvedResources(w, matched),
          resourceTitles: [w.primary_resource, w.secondary_resource].filter(
            (t): t is string => !!t && !!t.trim(),
          ),
        }
      }),
    [weeks, r.courses],
  )

  const clearedCount = weekMeta.filter(m => {
    const s = getProgress(m.plan.week, m.index).status
    return s === 'passed' || s === 'skipped'
  }).length

  // Unlock the next week once the previous one is cleared.
  useEffect(() => {
    setProgress(prev => {
      let changed = false
      const next = { ...prev }
      weekMeta.forEach((m, i) => {
        if (i === 0) return
        const prevWeek = weekMeta[i - 1].plan.week
        const prevStatus = (next[prevWeek] ?? prev[prevWeek])?.status
        const cleared = prevStatus === 'passed' || prevStatus === 'skipped'
        const own = next[m.plan.week]
        if (cleared && (!own || own.status === 'locked')) {
          next[m.plan.week] = { ...(own ?? EMPTY_PROGRESS), status: 'in_progress' }
          changed = true
        }
      })
      return changed ? next : prev
    })
  }, [weekMeta, progress])

  const levelForWeek = (): 'beginner' | 'intermediate' | 'advanced' => r.level

  const startTest = async (weekIdx: number, attempt: number) => {
    const meta = weekMeta[weekIdx]
    const week = meta.plan.week
    const p = getProgress(week, weekIdx)
    setBusyWeek(week)
    setError(null)
    try {
      const res = await apiPost<WeekTestResponse>('/api/week/test', {
        user_id: userId,
        session_id: sessionId,
        topic_input: topicInput,
        week,
        week_focus: meta.plan.focus,
        resources: meta.matched.length ? meta.matched.map(m => m.course.title) : meta.resourceTitles,
        subjects: topicInput.subjects,
        level: levelForWeek(),
        attempt,
        weak_concepts: attempt > 1 ? p.weakConcepts : [],
        covered_concepts: p.coveredConcepts,
      })
      setActiveTest(res)
      patch(week, { status: 'testing' }, weekIdx)
      setExpandedWeek(week)
    } catch (e: any) {
      setError(e?.message ?? 'Could not generate the week test. Please try again.')
    } finally {
      setBusyWeek(null)
    }
  }

  const submitTest = async (weekIdx: number, answers: Record<number, 'A' | 'B' | 'C' | 'D'>) => {
    const meta = weekMeta[weekIdx]
    const week = meta.plan.week
    if (!activeTest) return
    setBusyWeek(week)
    setError(null)
    try {
      const res = await apiPost<WeekTestSubmitResponse>('/api/week/submit', {
        user_id: userId,
        session_id: sessionId,
        topic_input: topicInput,
        week,
        week_focus: meta.plan.focus,
        resources: meta.matched.length ? meta.matched.map(m => m.course.title) : meta.resourceTitles,
        attempt: activeTest.attempt,
        questions: activeTest.questions,
        answers,
      })

      const p = getProgress(week, weekIdx)
      const covered = Array.from(
        new Set([...p.coveredConcepts, ...activeTest.questions.flatMap(q => q.concepts ?? [])]),
      )

      patch(
        week,
        {
          status: res.passed ? 'passed' : 'refresher',
          attempts: res.attempt,
          lastScore: res.score,
          bestScore: p.bestScore === null ? res.score : Math.max(p.bestScore, res.score),
          weakConcepts: res.weak_concepts,
          coveredConcepts: covered,
          refresher: res.passed ? null : res.refresher ?? null,
          refresherDone: false,
        },
        weekIdx,
      )
      setActiveTest(null)
    } catch (e: any) {
      setError(e?.message ?? 'Could not score the test. Please try again.')
    } finally {
      setBusyWeek(null)
    }
  }

  if (!weeks.length) {
    return <p className="text-sm text-slate-500">No weekly plan was generated.</p>
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-1">
        <h3 className="text-xl font-display font-semibold flex items-center gap-2">
          <Calendar className="w-5 h-5 text-amber-300" />
          Week-by-Week Learning Path
        </h3>
        <span className="text-xs text-slate-400">
          {clearedCount}/{weeks.length} weeks cleared
        </span>
      </div>
      <p className="text-sm text-slate-400 mb-4">
        Work through each week, mark the course complete, then clear the {WEEK_TEST_TOTAL}-mark checkpoint
        test ({WEEK_TEST_PASSING}/{WEEK_TEST_TOTAL} to pass). Miss the mark and a targeted refresher is added
        inside that same week.
      </p>

      <div className="h-2 rounded-full bg-white/10 overflow-hidden mb-6">
        <div
          className="h-full bg-amber-400/80 transition-all duration-500"
          style={{ width: `${(clearedCount / weeks.length) * 100}%` }}
        />
      </div>

      {error && (
        <div className="mb-5 flex items-start gap-2 text-sm text-rose-300 bg-rose-400/10 border border-rose-400/30 rounded-lg p-3">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div>
        {weekMeta.map((meta, i) => {
          const w = meta.plan
          const p = getProgress(w.week, i)
          const style = STATUS_STYLE[p.status]
          const locked = p.status === 'locked'
          const isExpanded = expandedWeek === w.week || p.status === 'testing'
          const busy = busyWeek === w.week
          const testForThisWeek = activeTest && activeTest.week === w.week ? activeTest : null

          return (
            <div key={w.week}>
              {i > 0 && (
                <Arrow
                  tone={
                    getProgress(weekMeta[i - 1].plan.week, i - 1).status === 'passed'
                      ? 'done'
                      : getProgress(weekMeta[i - 1].plan.week, i - 1).status === 'refresher'
                        ? 'warn'
                        : 'idle'
                  }
                />
              )}

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(i * 0.04, 0.4) }}
                style={{ perspective: '1000px', transformStyle: 'preserve-3d' }}
              >
                {/* Week node */}
                <motion.div
                  whileHover={locked ? undefined : { y: -2, rotateX: 1 }}
                  onClick={() => {
                    if (locked) return
                    setExpandedWeek(prev => (prev === w.week ? null : w.week))
                  }}
                  className={`relative group ${locked ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
                  style={{ transformStyle: 'preserve-3d' }}
                >
                  <div className="absolute inset-0 bg-white/5 rounded-lg translate-x-1 translate-y-1 blur-sm" />

                  <div
                    className={`relative bg-gradient-to-br from-slate-800/80 to-slate-900/80 border rounded-lg p-5 transition-all duration-300 ${
                      isExpanded ? 'bg-amber-400/5 border-amber-300/40' : style.border
                    }`}
                    style={{
                      boxShadow: isExpanded
                        ? '0 8px 24px rgba(251,191,36,0.15), 0 2px 8px rgba(0,0,0,0.2)'
                        : '0 4px 12px rgba(0,0,0,0.1)',
                    }}
                  >
                    <div className="flex items-start gap-4">
                      {/* Week number node */}
                      <div
                        className={`flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br border-2 flex items-center justify-center font-bold text-lg ${style.dot}`}
                        style={{
                          boxShadow: '0 4px 12px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.1)',
                        }}
                      >
                        {p.status === 'passed' ? (
                          <CheckCircle2 className="w-6 h-6" />
                        ) : p.status === 'skipped' ? (
                          <SkipForward className="w-5 h-5" />
                        ) : locked ? (
                          <Lock className="w-5 h-5" />
                        ) : (
                          w.week
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-3 mb-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="label-caps text-amber-300/80">Week {w.week}</span>
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full border font-medium ${style.badge}`}
                            >
                              {style.label}
                            </span>
                            {p.bestScore !== null && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-400">
                                best {p.bestScore}/{WEEK_TEST_TOTAL}
                              </span>
                            )}
                            {p.attempts > 1 && (
                              <span className="text-xs text-slate-500">{p.attempts} attempts</span>
                            )}
                          </div>
                          {!locked && (
                            <ChevronDown
                              className={`w-5 h-5 text-slate-400 transition-transform duration-300 flex-shrink-0 ${
                                isExpanded ? 'rotate-180' : ''
                              }`}
                            />
                          )}
                        </div>

                        <p className="font-semibold text-base leading-relaxed mb-3">{w.focus}</p>

                        <div className="flex flex-wrap gap-2 mb-3">
                          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-white/10 border border-white/10 text-slate-300">
                            <BookOpen className="w-3 h-3" />
                            {w.primary_resource}
                          </span>
                          {w.secondary_resource && (
                            <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-white/10 border border-white/10 text-slate-400">
                              <BookOpen className="w-3 h-3" />
                              {w.secondary_resource}
                            </span>
                          )}
                          {meta.matched.length > 1 && (
                            <span className="text-xs px-2.5 py-1 rounded-full bg-amber-400/10 border border-amber-300/30 text-amber-300">
                              {meta.matched.length} courses
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

                {/* Expanded week body */}
                <AnimatePresence initial={false}>
                  {isExpanded && !locked && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-3 ml-6 pl-6 border-l border-white/10 space-y-4 pb-1">
                        {/* Every course this week refers to — primary AND secondary */}
                        {meta.matched.length > 0 ? (
                          <div
                            className={
                              meta.matched.length > 1 ? 'grid lg:grid-cols-2 gap-4' : 'grid gap-4'
                            }
                          >
                            {meta.matched.map(m => (
                              <CourseCard
                                key={m.course.url}
                                course={m.course}
                                roleLabel={m.role === 'primary' ? 'Primary' : 'Secondary'}
                              />
                            ))}
                          </div>
                        ) : (
                          <div className="border border-amber-300/30 rounded-lg p-4 bg-white/[0.02]">
                            <p className="text-amber-300 font-medium mb-1">Week {w.week} resources</p>
                            <p className="text-sm text-slate-300">{meta.resourceTitles.join(' · ')}</p>
                            <p className="text-xs text-slate-500 mt-2">
                              Full course details aren't available for this week's resources.
                            </p>
                          </div>
                        )}

                        {meta.unresolved.length > 0 && meta.matched.length > 0 && (
                          <p className="text-xs text-slate-500">
                            Also listed for this week (no course card matched):{' '}
                            {meta.unresolved.join(' · ')}
                          </p>
                        )}

                        {/* Test / refresher zone */}
                        {testForThisWeek ? (
                          <WeekTest
                            week={w.week}
                            attempt={testForThisWeek.attempt}
                            total={testForThisWeek.total}
                            passingScore={testForThisWeek.passing_score}
                            questions={testForThisWeek.questions}
                            submitting={busy}
                            onSubmit={answers => submitTest(i, answers)}
                            onCancel={() => {
                              setActiveTest(null)
                              patch(w.week, { status: 'in_progress' }, i)
                            }}
                          />
                        ) : p.status === 'refresher' && p.refresher ? (
                          <WeekRefresher
                            refresher={p.refresher}
                            lastScore={p.lastScore}
                            total={WEEK_TEST_TOTAL}
                            passingScore={WEEK_TEST_PASSING}
                            attempt={p.attempts}
                            done={p.refresherDone}
                            busy={busy}
                            onMarkDone={() => patch(w.week, { refresherDone: true }, i)}
                            onRetake={() => startTest(i, p.attempts + 1)}
                            onSkip={() => patch(w.week, { status: 'skipped' }, i)}
                          />
                        ) : p.status === 'passed' ? (
                          <div className="flex flex-wrap items-center gap-3 rounded-lg border border-green-400/25 bg-green-400/5 p-4">
                            <Trophy className="w-5 h-5 text-green-300 flex-shrink-0" />
                            <p className="text-sm text-green-200 flex-1 min-w-[12rem]">
                              Week {w.week} cleared with {p.lastScore}/{WEEK_TEST_TOTAL}. Week{' '}
                              {weekMeta[i + 1]?.plan.week ?? '—'}
                              {weekMeta[i + 1] ? ' is now unlocked.' : ' — that was the last week.'}
                            </p>
                            <button
                              type="button"
                              className="btn-ghost flex items-center gap-2 text-sm"
                              disabled={busy}
                              onClick={() => startTest(i, p.attempts + 1)}
                            >
                              <RotateCcw className="w-4 h-4" /> Retake test
                            </button>
                          </div>
                        ) : p.status === 'skipped' ? (
                          <div className="flex flex-wrap items-center gap-3 rounded-lg border border-white/15 bg-white/[0.03] p-4">
                            <SkipForward className="w-5 h-5 text-slate-300 flex-shrink-0" />
                            <p className="text-sm text-slate-300 flex-1 min-w-[12rem]">
                              You skipped week {w.week}
                              {p.lastScore !== null ? ` after scoring ${p.lastScore}/${WEEK_TEST_TOTAL}` : ''}.
                              You can come back and clear it any time.
                            </p>
                            <button
                              type="button"
                              className="btn-ghost text-sm"
                              disabled={busy}
                              onClick={() => startTest(i, p.attempts + 1)}
                            >
                              Take the test now
                            </button>
                          </div>
                        ) : (
                          <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
                            <p className="text-sm text-slate-300 mb-3">
                              Finished week {w.week}? Mark it complete and we'll generate a{' '}
                              {WEEK_TEST_TOTAL}-mark test on this week's material.
                            </p>
                            <button
                              type="button"
                              className="btn-primary flex items-center gap-2"
                              disabled={busy}
                              onClick={() => startTest(i, p.attempts + 1)}
                            >
                              {busy ? (
                                <>
                                  <Loader2 className="w-4 h-4 animate-spin" /> Generating test…
                                </>
                              ) : (
                                <>
                                  <Target className="w-4 h-4" /> I've completed this week's course
                                </>
                              )}
                            </button>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
