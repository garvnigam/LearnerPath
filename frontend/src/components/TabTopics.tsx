import { useEffect, useState } from 'react'
import type { BudgetPref, FormatPref, GoalType, PacePref, SavedPlanResponse, TopicInput } from '../lib/types'
import { Rocket, History, Loader2, Briefcase, Award, Wrench, Compass, GraduationCap, Video, FileText, Users, User, CalendarClock, Wallet, X, Clock, CalendarRange } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { apiGet } from '../lib/api'

const SUBJECT_EMOJI: Record<string, string> = {
  'Computer Science': '💻', 'Machine Learning': '🤖', 'Deep Learning': '🧠', 'Data Science': '📊',
  'Mathematics': '➗', 'Physics': '⚛️', 'Statistics': '📈', 'Web Development': '🌐',
  'Cybersecurity': '🛡️', 'Robotics': '🦾', 'Economics': '💹', 'Business': '💼',
  'Music': '🎵', 'Arts': '🎨', 'History': '📜', 'Philosophy': '🧭', 'Psychology': '🧩', 'Biology': '🧬',
}

const SUGGESTED = Object.keys(SUBJECT_EMOJI)

const GOALS: { id: GoalType; label: string; icon: any }[] = [
  { id: 'job', label: 'Get a job', icon: Briefcase },
  { id: 'certification', label: 'Certification', icon: Award },
  { id: 'project', label: 'Build a project', icon: Wrench },
  { id: 'curiosity', label: 'Curiosity', icon: Compass },
  { id: 'exam_prep', label: 'Exam prep', icon: GraduationCap },
]

const FORMATS: { id: FormatPref; label: string; icon: any }[] = [
  { id: 'video', label: 'Video', icon: Video },
  { id: 'text', label: 'Text', icon: FileText },
  { id: 'hands-on', label: 'Hands-on', icon: Wrench },
]

const PACES: { id: PacePref; label: string; icon: any }[] = [
  { id: 'solo', label: 'Solo', icon: User },
  { id: 'cohort', label: 'Cohort', icon: Users },
  { id: 'paced', label: 'Paced w/ deadlines', icon: CalendarClock },
]

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
}
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0 },
}

const BUDGETS: { id: BudgetPref; label: string; hint: string }[] = [
  { id: 'strictly_free',  label: 'Strictly free',        hint: 'Only 100% free courses. No Coursera audit-only paid certs.' },
  { id: 'free_and_audit', label: 'Free + audit-only',    hint: 'Include Coursera courses you can watch free (cert costs money).' },
  { id: 'free_and_paid',  label: 'Open to paid',         hint: 'Show the best, paid or not.' },
]

export default function TabTopics({
  userId,
  onSubmit,
  onResume,
}: {
  userId: string | null
  onSubmit: (t: TopicInput) => void
  onResume: (plan: SavedPlanResponse) => void
}) {
  const [selected, setSelected] = useState<string[]>([])
  const [custom, setCustom] = useState('')
  const [months, setMonths] = useState(6)
  const [hours, setHours] = useState(2)
  const [goal, setGoal] = useState<GoalType | undefined>(undefined)
  const [formats, setFormats] = useState<FormatPref[]>([])
  const [pace, setPace] = useState<PacePref | undefined>(undefined)
  const [budget, setBudget] = useState<BudgetPref>('strictly_free')

  const [resuming, setResuming] = useState(false)
  const [resumeError, setResumeError] = useState<string | null>(null)
  const [hasSavedPlan, setHasSavedPlan] = useState(false)

  useEffect(() => {
    setHasSavedPlan(false)
  }, [userId])

  function toggle(s: string) {
    setSelected((cur) => cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s])
  }

  function toggleFormat(f: FormatPref) {
    setFormats((cur) => cur.includes(f) ? cur.filter((x) => x !== f) : [...cur, f])
  }

  function addCustom() {
    const t = custom.trim()
    if (t && !selected.includes(t)) setSelected([...selected, t])
    setCustom('')
  }

  async function continueSaved() {
    if (!userId) return
    setResuming(true)
    setResumeError(null)
    try {
      const plan = await apiGet<SavedPlanResponse>(`/api/plan/${userId}`)
      onResume(plan)
    } catch (e: any) {
      setResumeError('No saved plan found, or it could not be loaded.')
    } finally {
      setResuming(false)
    }
  }

  const valid = selected.length > 0 && months > 0 && hours > 0

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {userId && (
        <motion.div variants={item} className="glass p-4 flex items-center justify-between gap-4">
          <div className="text-sm text-slate-300">
            Already have a plan? Pick up right where you left off.
          </div>
          <div className="flex items-center gap-2">
            {resumeError && <span className="text-xs text-rose-400">{resumeError}</span>}
            <button className="btn-ghost flex items-center gap-2" onClick={continueSaved} disabled={resuming}>
              {resuming ? <Loader2 className="w-4 h-4 animate-spin" /> : <History className="w-4 h-4" />}
              Continue my plan
            </button>
          </div>
        </motion.div>
      )}

      <motion.div variants={item} className="glass p-8 relative overflow-hidden">
        <div className="pointer-events-none absolute -top-16 -right-16 w-64 h-64 rounded-full bg-gradient-to-br from-amber-500/20 to-rose-500/10 blur-3xl" />
        <div className="relative flex items-center gap-3 mb-2">
          <motion.div
            initial={{ scale: 0.6, opacity: 0, rotate: -15 }}
            animate={{ scale: 1, opacity: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 220, damping: 16 }}
            className="w-11 h-11 rounded-2xl bg-gradient-to-br from-amber-500 via-orange-500 to-rose-500 flex items-center justify-center text-xl shadow-lg shadow-orange-500/30 flex-shrink-0"
          >
            🚀
          </motion.div>
          <h2 className="text-3xl font-display font-bold bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400 bg-clip-text text-transparent">
            What do you want to learn?
          </h2>
        </div>
        <p className="text-slate-400 mb-6">Pick one or more subjects. You can add your own too.</p>

        <div className="flex flex-wrap gap-2 mb-4">
          {SUGGESTED.map((s) => (
            <button
              key={s}
              onClick={() => toggle(s)}
              className={`chip ${selected.includes(s) ? 'chip-active' : ''}`}
            >
              <span className="mr-1">{SUBJECT_EMOJI[s]}</span>{s}
            </button>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            className="input"
            placeholder="Add your own subject (e.g. Bioinformatics)"
            value={custom}
            onChange={(e) => setCustom(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addCustom()}
          />
          <button className="btn-ghost" onClick={addCustom}>Add</button>
        </div>

        <AnimatePresence>
          {selected.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 flex flex-wrap items-center gap-2 overflow-hidden"
            >
              <span className="text-xs text-slate-500">Selected:</span>
              <AnimatePresence>
                {selected.map((s) => (
                  <motion.span
                    key={s}
                    initial={{ opacity: 0, scale: 0.7 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.7 }}
                    className="inline-flex items-center gap-1.5 text-xs pl-2.5 pr-1.5 py-1 rounded-full bg-gradient-to-r from-amber-500/20 to-rose-500/20 border border-amber-400/30 text-amber-200"
                  >
                    {SUBJECT_EMOJI[s] ?? '📌'} {s}
                    <button onClick={() => toggle(s)} className="hover:text-white transition p-0.5">
                      <X className="w-3 h-3" />
                    </button>
                  </motion.span>
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <motion.div variants={item} className="grid md:grid-cols-2 gap-4">
        <div className="glass p-6">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
            <span className="w-7 h-7 rounded-lg bg-amber-500/15 border border-amber-400/30 flex items-center justify-center text-amber-300">
              <CalendarRange className="w-4 h-4" />
            </span>
            How many months to prepare?
          </label>
          <div className="flex items-center gap-4">
            <input
              type="range" min={1} max={24}
              value={months}
              onChange={(e) => setMonths(+e.target.value)}
              className="flex-1 accent-amber-500"
            />
            <span className="text-2xl font-bold w-16 text-right">{months}mo</span>
          </div>
          <div className="flex flex-wrap gap-2 mt-3">
            {[1, 3, 6, 12].map((m) => (
              <button key={m} className={`chip ${months === m ? 'chip-active' : ''}`} onClick={() => setMonths(m)}>
                {m} month{m > 1 ? 's' : ''}
              </button>
            ))}
          </div>
        </div>

        <div className="glass p-6">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
            <span className="w-7 h-7 rounded-lg bg-orange-500/15 border border-orange-400/30 flex items-center justify-center text-orange-300">
              <Clock className="w-4 h-4" />
            </span>
            Hours per day you can study?
          </label>
          <div className="flex items-center gap-4">
            <input
              type="range" min={0.5} max={8} step={0.5}
              value={hours}
              onChange={(e) => setHours(+e.target.value)}
              className="flex-1 accent-orange-500"
            />
            <span className="text-2xl font-bold w-16 text-right">{hours}h</span>
          </div>
          <div className="flex flex-wrap gap-2 mt-3">
            {[1, 2, 3, 4].map((h) => (
              <button key={h} className={`chip ${hours === h ? 'chip-active' : ''}`} onClick={() => setHours(h)}>
                {h}h/day
              </button>
            ))}
          </div>
        </div>
      </motion.div>

      <motion.div variants={item} className="glass p-6">
        <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
          <span className="w-7 h-7 rounded-lg bg-rose-500/15 border border-rose-400/30 flex items-center justify-center text-rose-300">
            <Rocket className="w-4 h-4" />
          </span>
          What's your goal?
        </label>
        <div className="flex flex-wrap gap-2">
          {GOALS.map((g) => {
            const GoalIcon = g.icon
            return (
              <button
                key={g.id}
                className={`chip flex items-center gap-1.5 ${goal === g.id ? 'chip-active' : ''}`}
                onClick={() => setGoal((cur) => (cur === g.id ? undefined : g.id))}
              >
                <GoalIcon className="w-3.5 h-3.5" />
                {g.label}
              </button>
            )
          })}
        </div>
      </motion.div>

      <motion.div variants={item} className="grid md:grid-cols-2 gap-4">
        <div className="glass p-6">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
            <span className="w-7 h-7 rounded-lg bg-amber-500/15 border border-amber-400/30 flex items-center justify-center text-amber-300">
              <Video className="w-4 h-4" />
            </span>
            Prefer video, text, or hands-on? <span className="text-slate-500 font-normal">(pick any)</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {FORMATS.map((f) => {
              const FormatIcon = f.icon
              return (
                <button
                  key={f.id}
                  className={`chip flex items-center gap-1.5 ${formats.includes(f.id) ? 'chip-active' : ''}`}
                  onClick={() => toggleFormat(f.id)}
                >
                  <FormatIcon className="w-3.5 h-3.5" />
                  {f.label}
                </button>
              )
            })}
          </div>
        </div>

        <div className="glass p-6">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
            <span className="w-7 h-7 rounded-lg bg-orange-500/15 border border-orange-400/30 flex items-center justify-center text-orange-300">
              <Users className="w-4 h-4" />
            </span>
            Solo, cohort, or paced with deadlines?
          </label>
          <div className="flex flex-wrap gap-2">
            {PACES.map((p) => {
              const PaceIcon = p.icon
              return (
                <button
                  key={p.id}
                  className={`chip flex items-center gap-1.5 ${pace === p.id ? 'chip-active' : ''}`}
                  onClick={() => setPace((cur) => (cur === p.id ? undefined : p.id))}
                >
                  <PaceIcon className="w-3.5 h-3.5" />
                  {p.label}
                </button>
              )
            })}
          </div>
        </div>
      </motion.div>

      <motion.div variants={item} className="glass p-6">
        <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
          <span className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-400/30 flex items-center justify-center text-emerald-300">
            <Wallet className="w-4 h-4" />
          </span>
          What's your budget?
        </label>
        <p className="text-xs text-slate-500 mb-3">
          We have thousands of world-class free courses. Pick <b>Free only</b> to hide paid ones entirely.
        </p>
        <div className="flex flex-wrap gap-3">
          {BUDGETS.map((b) => (
            <button
              key={b.id}
              className={`chip flex flex-col items-start px-4 py-2 ${budget === b.id ? 'chip-active' : ''}`}
              onClick={() => setBudget(b.id)}
            >
              <span className="font-semibold">{b.label}</span>
              <span className="text-xs text-slate-400 font-normal">{b.hint}</span>
            </button>
          ))}
        </div>
      </motion.div>

      <motion.div variants={item} className="flex justify-end">
        <button
          className="btn-primary flex items-center gap-2"
          disabled={!valid}
          onClick={() =>
            onSubmit({
              subjects: selected,
              duration_months: months,
              hours_per_day: hours,
              goal,
              preferred_formats: formats,
              pace,
              budget,
            })
          }
        >
          Continue <Rocket className="w-4 h-4" />
        </button>
      </motion.div>
    </motion.div>
  )
}
