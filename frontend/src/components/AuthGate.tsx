import { useMsal } from '@azure/msal-react'
import { LogOut, User } from 'lucide-react'
import { entraConfigured } from '../lib/authConfig'

export default function AuthGate() {
  const { instance, accounts } = useMsal()

  if (!entraConfigured) {
    return <span className="text-xs text-amber-400">Auth not configured</span>
  }

  const account = accounts[0]
  if (!account) return null

  const label =
    account.username ||
    (account.idTokenClaims as any)?.email ||
    (account.idTokenClaims as any)?.phone_number ||
    account.name ||
    'Signed in'

  async function signOut() {
    await instance.logoutRedirect({ postLogoutRedirectUri: window.location.origin })
  }

  return (
    <div className="flex items-center gap-3">
      <div className="hidden sm:flex items-center gap-2 text-sm text-slate-300">
        <User className="w-4 h-4" />
        <span>{label}</span>
      </div>
      <button className="btn-ghost text-sm" onClick={signOut}>
        <LogOut className="w-4 h-4 inline mr-1" /> Sign out
      </button>
    </div>
  )
}
