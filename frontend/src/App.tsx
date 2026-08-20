import { useEffect, useState } from 'react'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import type { TopicInput, ChatMessage, RecommendationResponse, MCQ } from './lib/types'
import { entraConfigured } from './lib/authConfig'
import { useSessionQuota } from './lib/useSessionQuota'
import TabTopics from './components/TabTopics'
import TabChat from './components/TabChat'
import TabAssessment from './components/TabAssessment'
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
  const [questions, setQuestions] = useState<MCQ[]>([])
  const [answers, setAnswers] = useState<Record<number, 'A' | 'B' | 'C' | 'D'>>({})
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null)

  useEffect(() => {
    const acct = accounts[0]
    if (acct) {
      setUserId(acct.localAccountId ?? acct.homeAccountId ?? null)
    } else {
      setUserId(null)
    }
  }, [accounts])

  if (entraConfigured && !isAuthenticated) {
    return <LoginPage />
  }

  if (session.status === 'blocked') {
    return (
      <>
        <LoginPage />
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-6">
          <div className="glass max-w-md w-full p-8 text-center space-y-4 border border-rose-400/30">
            <div className="w-12 h-12 mx-auto rounded-full bg-rose-500/20 border border-rose-400/40 flex items-center justify-center text-2xl">
              🚫
            </div>
            <h1 className="text-2xl font-bold">Login not allowed</h1>
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
          <h1 className="text-2xl font-bold">Session ended</h1>
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
    <div className="min-h-screen">
      <header className="border-b border-white/5 backdrop-blur-md sticky top-0 z-40 bg-slate-950/60">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-lg">
              🎓
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">LearnPath</h1>
              <p className="text-xs text-slate-400">Personalized learning from top universities</p>
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
              <span className="hidden sm:inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-emerald-500/15 border border-emerald-400/40 text-emerald-300">
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
              (i === 2 && questions.length > 0) ||
              (i === 3 && !!recommendation)
            return (
              <button
                key={t.id}
                disabled={!enabled}
                onClick={() => enabled && setStage(t.id)}
                className={`flex-1 min-w-[140px] px-4 py-3 rounded-xl font-medium text-sm transition flex items-center justify-center gap-2
                  ${active ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg' : 'text-slate-300 hover:bg-white/5'}
                  ${!enabled ? 'opacity-40 cursor-not-allowed' : ''}`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{t.label}</span>
                <span className="text-xs opacity-60">Step {i + 1}</span>
              </button>
            )
          })}
        </div>

        {stage === 'topics' && (
          <TabTopics
            onSubmit={(ti) => {
              setTopicInput(ti)
              setMessages([])
              setFocusAreas([])
              setStage('chat')
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
            onQuestionsReady={(qs) => setQuestions(qs)}
          />
        )}

        {stage === 'assessment' && topicInput && (
          <TabAssessment
            sessionId={sessionId}
            topicInput={topicInput}
            focusAreas={focusAreas}
            questions={questions}
            setQuestions={setQuestions}
            answers={answers}
            setAnswers={setAnswers}
            onSubmit={(rec) => {
              setRecommendation(rec)
              setStage('results')
            }}
            userId={userId}
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
              setQuestions([])
              setAnswers({})
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
