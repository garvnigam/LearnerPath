import { useState } from 'react'
import type { TopicInput } from '../lib/types'
import { Rocket } from 'lucide-react'
import { motion } from 'framer-motion'

const SUGGESTED = [
  'Computer Science', 'Machine Learning', 'Deep Learning', 'Data Science',
  'Mathematics', 'Physics', 'Statistics', 'Web Development',
  'Cybersecurity', 'Robotics', 'Economics', 'Business',
  'Music', 'Arts', 'History', 'Philosophy', 'Psychology', 'Biology',
]

export default function TabTopics({ onSubmit }: { onSubmit: (t: TopicInput) => void }) {
  const [selected, setSelected] = useState<string[]>([])
  const [custom, setCustom] = useState('')
  const [months, setMonths] = useState(6)
  const [hours, setHours] = useState(2)
  const [goal, setGoal] = useState('')

  function toggle(s: string) {
    setSelected((cur) => cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s])
  }

  function addCustom() {
    const t = custom.trim()
    if (t && !selected.includes(t)) setSelected([...selected, t])
    setCustom('')
  }

  const valid = selected.length > 0 && months > 0 && hours > 0

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
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
          What's your goal? <span className="text-slate-500 font-normal">(optional)</span>
        </label>
        <textarea
          className="input min-h-[80px] resize-none"
          placeholder="e.g. Get an ML engineer job in 6 months, or just curious about deep learning"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
        />
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
              goal: goal || undefined,
            })
          }
        >
          Continue <Rocket className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  )
}
