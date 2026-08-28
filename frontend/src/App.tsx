import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import type { TopicInput, ChatMessage, RecommendationResponse, SavedPlanResponse } from './lib/types'
import { entraConfigured } from './lib/authConfig'
import { useSessionQuota } from './lib/useSessionQuota'
import TabTopics from './components/TabTopics'
import TabChat from './components/TabChat'
import TabAdaptiveAssessment from './components/TabAdaptiveAssessment'
import TabResults from './components/TabResults'
import AuthGate from './components/AuthGate'
import LoginPage from './components/LoginPage'
import { GraduationCap, MessageSquare, ListChecks, Sparkles, Clock } from 'lucide-react'

type Stage = 'topics' | 'chat' | 'assessment' | 'results'

export default function App() {
  const { instance, accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const session = useSessionQuota()

  const [userId, setUserId] = useState<string | null>(null)
  const [sessionId] = useState<string>(() => crypto.randomUUID())

  const [stage, setStage] = useState<Stage>('topics')
  const [topicInput, setTopicInput] = useState<TopicInput | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [focusAreas, setFocusAreas] = useState<string[]>([])
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null)

  useEffect(() => {
    const acct = accounts[0]
    if (acct) {
      setUserId(acct.localAccountId ?? acct.homeAccountId ?? null)
    } else {
      setUserId(null)
    }
  }, [accounts])

  // DEV: Entra login gate disabled temporarily — hindering local development.
  // Uncomment to re-enable login enforcement.
  // if (entraConfigured && !isAuthenticated) {
  //   return <LoginPage />
  // }

  if (session.status === 'blocked') {
    return (
      <>
        <LoginPage />
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-6">
          <div className="glass max-w-md w-full p-8 text-center space-y-4 border border-white/15">
            <h1 className="text-2xl font-display font-semibold">Login not allowed</h1>
            <p className="text-slate-300 text-sm leading-relaxed">{session.reason}</p>
            <p className="text-xs text-slate-500">
              This is an MVP running on a minimum budget. Only one login is allowed per account.
            </p>
            <button
              className="btn-primary w-full"
              onClick={() => instance.logoutRedirect({ postLogoutRedirectUri: window.location.origin })}
            >
              Sign out
            </button>
          </div>
        </div>
      </>
    )
  }

  if (session.status === 'expired') {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="glass max-w-md w-full p-8 text-center space-y-4">
          <h1 className="text-2xl font-display font-semibold">Session ended</h1>
          <p className="text-slate-300 text-sm">Your 2-minute session has expired. Signing you out…</p>
        </div>
      </div>
    )
  }

  const sessionActive = session.status === 'active'
  const isUnlimited = sessionActive && session.isUnlimited
  const remaining = sessionActive ? session.remaining : 0

  const tabs: { id: Stage; label: string; icon: any }[] = [
    { id: 'topics', label: 'What to learn', icon: GraduationCap },
    { id: 'chat', label: 'Refine focus', icon: MessageSquare },
    { id: 'assessment', label: 'Quick quiz', icon: ListChecks },
    { id: 'results', label: 'Your path', icon: Sparkles },
  ]

  return (
    <div className="min-h-screen relative">
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-24 -left-16 w-[36rem] h-[36rem] rounded-full blur-3xl bg-amber-400/[0.05]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[28rem] h-[28rem] rounded-full blur-3xl bg-white/[0.03]" />
      </div>

      <header className="relative border-b border-white/10 backdrop-blur-md sticky top-0 z-40 bg-slate-950/70 overflow-hidden">
        <div className="relative max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-md border border-amber-300/30 bg-amber-400/10 flex items-center justify-center flex-shrink-0">
              <GraduationCap className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <h1 className="text-xl font-display font-semibold tracking-tight text-slate-100">LearnPath</h1>
              <p className="label-caps">Personalized learning from top universities</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {sessionActive && !isUnlimited && (
              <span
                className={`hidden sm:inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full border ${
                  remaining <= 30
                    ? 'bg-rose-500/15 border-rose-400/40 text-rose-300'
                    : 'bg-white/5 border-white/10 text-slate-300'
                }`}
                title="MVP session — you'll be signed out after this timer"
              >
                <Clock className="w-3 h-3" />
                {Math.floor(remaining / 60)}:{String(remaining % 60).padStart(2, '0')}
              </span>
            )}
            {isUnlimited && (
              <span className="hidden sm:inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-white/5 border border-white/15 text-slate-300">
                unlimited
              </span>
            )}
            <AuthGate />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="glass p-2 mb-8 flex gap-1 overflow-x-auto">
          {tabs.map((t, i) => {
            const Icon = t.icon
            const active = t.id === stage
            const enabled =
              i === 0 ||
              (i === 1 && !!topicInput) ||
              (i === 2 && !!topicInput) ||
              (i === 3 && !!recommendation)
            return (
              <button
                key={t.id}
                disabled={!enabled}
                onClick={() => enabled && setStage(t.id)}
                className={`relative flex-1 min-w-[140px] px-4 py-3 rounded-md font-sans font-medium text-sm transition flex items-center justify-center gap-2
                  ${active ? 'text-slate-950' : 'text-slate-300 hover:bg-white/5'}
                  ${!enabled ? 'opacity-40 cursor-not-allowed' : ''}`}
              >
                {active && (
                  <motion.span
                    layoutId="tab-pill"
                    className="absolute inset-0 rounded-md bg-amber-400/90"
                    transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                  />
                )}
                <Icon className="relative z-10 w-4 h-4" />
                <span className="relative z-10 hidden sm:inline">{t.label}</span>
                <span className="relative z-10 text-xs opacity-60">Step {i + 1}</span>
              </button>
            )
          })}
        </div>

        {stage === 'topics' && (
          <TabTopics
            userId={userId}
            onSubmit={(ti) => {
              setTopicInput(ti)
              setMessages([])
              setFocusAreas([])
              setStage('chat')
            }}
            onResume={(plan: SavedPlanResponse) => {
              setTopicInput(plan.topic_input)
              setRecommendation(plan.recommendation)
              setStage('results')
            }}
          />
        )}

        {stage === 'chat' && topicInput && (
          <TabChat
            userId={userId}
            sessionId={sessionId}
            topicInput={topicInput}
            messages={messages}
            setMessages={setMessages}
            onReady={async (focus) => {
              setFocusAreas(focus)
              setStage('assessment')
            }}
          />
        )}

        {stage === 'assessment' && topicInput && (
          <TabAdaptiveAssessment
            sessionId={sessionId}
            topicInput={topicInput}
            focusAreas={focusAreas}
            userId={userId}
            onSubmit={(rec) => {
              setRecommendation(rec)
              setStage('results')
            }}
          />
        )}

        {stage === 'results' && recommendation && topicInput && (
          <TabResults
            recommendation={recommendation}
            topicInput={topicInput}
            onRestart={() => {
              setTopicInput(null)
              setMessages([])
              setFocusAreas([])
              setRecommendation(null)
              setStage('topics')
            }}
          />
        )}
      </main>

      <footer className="text-center text-xs text-slate-500 py-8">
        Built with Azure OpenAI • Courses from MIT, Stanford, Harvard, IITs, top YouTube playlists & more
      </footer>
    </div>
  )
}
