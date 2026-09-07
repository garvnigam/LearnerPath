import { motion } from 'framer-motion'
import {
  AlertTriangle,
  Clock,
  ExternalLink,
  FileText,
  Loader2,
  PlayCircle,
  RotateCcw,
  SkipForward,
  Wrench,
} from 'lucide-react'
import type { RefresherModule, RefresherResource } from '../lib/types'

const KIND_ICON: Record<RefresherResource['kind'], typeof FileText> = {
  text: FileText,
  video: PlayCircle,
  practice: Wrench,
}

const KIND_LABEL: Record<RefresherResource['kind'], string> = {
  text: 'Read',
  video: 'Watch',
  practice: 'Practice',
}

type Props = {
  refresher: RefresherModule
  lastScore: number | null
  total: number
  passingScore: number
  attempt: number
  /** true once the learner has said they finished the refresher */
  done: boolean
  busy: boolean
  onMarkDone: () => void
  onRetake: () => void
  onSkip: () => void
}

export default function WeekRefresher({
  refresher,
  lastScore,
  total,
  passingScore,
  attempt,
  done,
  busy,
  onMarkDone,
  onRetake,
  onSkip,
}: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-6 border border-rose-400/25"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3">
          <span className="w-10 h-10 rounded-md border border-rose-400/30 bg-rose-400/10 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-rose-300" />
          </span>
          <div>
            <h4 className="text-lg font-display font-semibold">{refresher.title}</h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Added inside week {refresher.week} — finish this, then retake the test.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {lastScore !== null && (
            <span className="px-2.5 py-1 rounded-full bg-rose-400/10 border border-rose-400/30 text-rose-300 font-medium">
              Scored {lastScore}/{total} · need {passingScore}
            </span>
          )}
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white/10 border border-white/10 text-slate-300">
            <Clock className="w-3 h-3" />
            ~{refresher.est_minutes} min
          </span>
        </div>
      </div>

      {refresher.summary && <p className="text-sm text-slate-300 leading-relaxed mb-4">{refresher.summary}</p>}

      {refresher.weak_concepts.length > 0 && (
        <div className="mb-5">
          <div className="label-caps mb-2">Topics you're lacking</div>
          <div className="flex flex-wrap gap-2">
            {refresher.weak_concepts.map((c, i) => (
              <span
                key={i}
                className="text-xs px-2.5 py-1 rounded-full bg-rose-400/10 border border-rose-400/30 text-rose-200"
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {refresher.notes && (
        <details open className="mb-5 border border-white/10 rounded-lg bg-white/[0.02]">
          <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-slate-200 hover:text-white transition">
            Refresher notes
          </summary>
          <div className="px-4 pb-4 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
            {refresher.notes}
          </div>
        </details>
      )}

      {refresher.resources.length > 0 && (
        <div className="mb-6">
          <div className="label-caps mb-2">Refresher material</div>
          <div className="space-y-2.5">
            {refresher.resources.map((r, i) => {
              const Icon = KIND_ICON[r.kind] ?? FileText
              return (
                <div
                  key={i}
                  className="border border-white/10 rounded-lg p-3.5 bg-white/[0.02] flex items-start gap-3"
                >
                  <span className="w-8 h-8 rounded-md bg-white/10 border border-white/10 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-4 h-4 text-amber-300" />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 border border-white/10 text-slate-300">
                        {KIND_LABEL[r.kind] ?? 'Read'}
                      </span>
                      {r.provider && <span className="text-xs text-slate-500">{r.provider}</span>}
                    </div>
                    <p className="font-medium text-sm leading-snug">{r.title}</p>
                    {r.why && <p className="text-xs text-slate-400 mt-1 leading-relaxed">{r.why}</p>}
                    {r.url && (
                      <a
                        href={r.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 mt-2 text-xs text-amber-300 hover:text-amber-200 transition"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Open
                      </a>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        {!done ? (
          <button type="button" className="btn-primary" disabled={busy} onClick={onMarkDone}>
            I've completed the refresher
          </button>
        ) : (
          <button
            type="button"
            className="btn-primary flex items-center gap-2"
            disabled={busy}
            onClick={onRetake}
          >
            {busy ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Building retest…
              </>
            ) : (
              <>
                <RotateCcw className="w-4 h-4" /> Retake week {refresher.week} test (attempt {attempt + 1})
              </>
            )}
          </button>
        )}
        <button
          type="button"
          className="btn-ghost flex items-center gap-2"
          disabled={busy}
          onClick={onSkip}
        >
          <SkipForward className="w-4 h-4" /> Skip refresher and move on
        </button>
      </div>
      <p className="text-xs text-slate-500 mt-3">
        Skipping is always allowed — the week is marked skipped rather than passed, and you can come back to it.
      </p>
    </motion.div>
  )
}
