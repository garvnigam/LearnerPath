import { useEffect, useState } from 'react'
import type { FormatPref, GoalType, PacePref, SavedPlanResponse, TopicInput } from '../lib/types'
import { Rocket, History, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { apiGet } from '../lib/api'

const SUGGESTED = [
  'Computer Science', 'Machine Learning', 'Deep Learning', 'Data Science',
  'Mathematics', 'Physics', 'Statistics', 'Web Development',
  'Cybersecurity', 'Robotics', 'Economics', 'Business',
  'Music', 'Arts', 'History', 'Philosophy', 'Psychology', 'Biology',
]

const GOALS: { id: GoalType; label: string }[] = [
  { id: 'job', label: 'Get a job' },
  { id: 'certification', label: 'Certification' },
  { id: 'project', label: 'Build a project' },
  { id: 'curiosity', label: 'Curiosity' },
  { id: 'exam_prep', label: 'Exam prep' },
]

const FORMATS: { id: FormatPref; label: string }[] = [
  { id: 'video', label: 'Video' },
  { id: 'text', label: 'Text' },
  { id: 'hands-on', label: 'Hands-on' },
]

const PACES: { id: PacePref; label: string }[] = [
  { id: 'solo', label: 'Solo' },
  { id: 'cohort', label: 'Cohort' },
  { id: 'paced', label: 'Paced w/ deadlines' },
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
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {userId && (
        <div className="glass p-4 flex items-center justify-between gap-4">
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
        </div>
      )}

      <div className="glass p-8">
        <h2 className="text-3xl font-bold mb-2 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          What do you want to learn?
        </h2>
        <p className="text-slate-400 mb-6">Pick one or more subjects. You can add your own too.</p>

        <div className="flex flex-wrap gap-2 mb-4">
          {SUGGESTED.map((s) => (
            <button
              key={s}
              onClick={() => toggle(s)}
              className={`chip ${selected.includes(s) ? 'chip-active' : ''}`}
            >
              {s}
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

        {selected.length > 0 && (
          <div className="mt-4 text-sm text-slate-300">
            <span className="text-slate-500">Selected:</span>{' '}
            <span className="font-medium">{selected.join(', ')}</span>
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="glass p-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            How many months to prepare?
          </label>
          <div className="flex items-center gap-4">
            <input
              type="range" min={1} max={24}
              value={months}
              onChange={(e) => setMonths(+e.target.value)}
              className="flex-1 accent-indigo-500"
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
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Hours per day you can study?
          </label>
          <div className="flex items-center gap-4">
            <input
              type="range" min={0.5} max={8} step={0.5}
              value={hours}
              onChange={(e) => setHours(+e.target.value)}
              className="flex-1 accent-indigo-500"
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
      </div>

      <div className="glass p-6">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          What's your goal?
        </label>
        <div className="flex flex-wrap gap-2">
          {GOALS.map((g) => (
            <button
              key={g.id}
              className={`chip ${goal === g.id ? 'chip-active' : ''}`}
              onClick={() => setGoal((cur) => (cur === g.id ? undefined : g.id))}
            >
              {g.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="glass p-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Prefer video, text, or hands-on? <span className="text-slate-500 font-normal">(pick any)</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {FORMATS.map((f) => (
              <button
                key={f.id}
                className={`chip ${formats.includes(f.id) ? 'chip-active' : ''}`}
                onClick={() => toggleFormat(f.id)}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div className="glass p-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Solo, cohort, or paced with deadlines?
          </label>
          <div className="flex flex-wrap gap-2">
            {PACES.map((p) => (
              <button
                key={p.id}
                className={`chip ${pace === p.id ? 'chip-active' : ''}`}
                onClick={() => setPace((cur) => (cur === p.id ? undefined : p.id))}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end">
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
            })
          }
        >
          Continue <Rocket className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  )
}
