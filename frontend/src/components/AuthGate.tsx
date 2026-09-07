import { LogOut, User } from 'lucide-react'

type Props = {
  username: string
  onSignOut: () => void
}

export default function AuthGate({ username, onSignOut }: Props) {
  return (
    <div className="flex items-center gap-3">
      <div className="hidden sm:flex items-center gap-2 text-sm text-slate-300">
        <User className="w-4 h-4" />
        <span>{username}</span>
      </div>
      <button className="btn-ghost text-sm" onClick={onSignOut}>
        <LogOut className="w-4 h-4 inline mr-1" /> Sign out
      </button>
    </div>
  )
}