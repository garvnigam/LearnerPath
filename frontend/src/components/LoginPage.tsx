import { useMsal } from '@azure/msal-react'
import { motion } from 'framer-motion'
import { Mail, Sparkles, ShieldCheck } from 'lucide-react'
import { entraConfigured, loginRequest } from '../lib/authConfig'

export default function LoginPage() {
  const { instance, inProgress } = useMsal()
  const busy = inProgress !== 'none'

  async function signIn() {
    try {
      await instance.loginRedirect(loginRequest)
    } catch (e) {
      console.error('[msal] login failed', e)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -top-20 -left-16 w-[32rem] h-[32rem] rounded-full bg-indigo-500/20 blur-3xl animate-float-slow" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[28rem] h-[28rem] rounded-full bg-pink-500/15 blur-3xl animate-float" />
      </div>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass p-8 max-w-md w-full text-center"
      >
        <motion.div
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 14 }}
          className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 mx-auto mb-6 flex items-center justify-center text-3xl shadow-lg shadow-indigo-500/30"
        >
          🎓
        </motion.div>
        <h1 className="text-2xl font-bold mb-2">Welcome to LearnPath</h1>
        <p className="text-sm text-slate-400 mb-8">
          Personalized learning paths from top universities. Sign in with your email to get started.
        </p>

        {!entraConfigured ? (
          <div className="text-sm text-amber-400 border border-amber-500/30 bg-amber-500/5 rounded-lg p-4 text-left">
            <strong>Entra External ID not configured.</strong>
            <p className="mt-2 text-slate-300">
              Set <code>VITE_ENTRA_TENANT_SUBDOMAIN</code> and <code>VITE_ENTRA_CLIENT_ID</code> in{' '}
              <code>frontend/.env</code>, then restart Vite.
            </p>
          </div>
        ) : (
          <>
            <button
              onClick={signIn}
              disabled={busy}
              className="btn-primary w-full flex items-center justify-center gap-2 py-3"
            >
              <Mail className="w-4 h-4" />
              {busy ? 'Opening secure sign-in…' : 'Sign in with email'}
            </button>

            <div className="mt-6 space-y-2 text-xs text-slate-400 text-left">
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 mt-0.5 text-emerald-400 flex-shrink-0" />
                <span>Secured by Microsoft Entra External ID with one-time passcode.</span>
              </div>
              <div className="flex items-start gap-2">
                <Sparkles className="w-4 h-4 mt-0.5 text-purple-400 flex-shrink-0" />
                <span>Your progress is saved so you can resume anytime.</span>
              </div>
            </div>
          </>
        )}
      </motion.div>
    </div>
  )
}
