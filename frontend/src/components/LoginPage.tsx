import { useMsal } from '@azure/msal-react'
import { motion } from 'framer-motion'
import { GraduationCap, Mail, Sparkles, ShieldCheck } from 'lucide-react'
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
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass p-8 max-w-md w-full text-center"
      >
        <div className="w-14 h-14 rounded-md border border-amber-300/30 bg-amber-400/10 mx-auto mb-6 flex items-center justify-center">
          <GraduationCap className="w-7 h-7 text-amber-300" />
        </div>
        <h1 className="text-2xl font-display font-semibold mb-2">Welcome to LearnPath</h1>
        <p className="text-sm text-slate-400 mb-8">
          Personalized learning paths from top universities. Sign in with your email to get started.
        </p>

        {!entraConfigured ? (
          <div className="text-sm text-amber-300 border border-amber-400/30 bg-amber-400/5 rounded-md p-4 text-left">
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
                <ShieldCheck className="w-4 h-4 mt-0.5 text-slate-300 flex-shrink-0" />
                <span>Secured by Microsoft Entra External ID with one-time passcode.</span>
              </div>
              <div className="flex items-start gap-2">
                <Sparkles className="w-4 h-4 mt-0.5 text-slate-300 flex-shrink-0" />
                <span>Your progress is saved so you can resume anytime.</span>
              </div>
            </div>
          </>
        )}
      </motion.div>
    </div>
  )
}
