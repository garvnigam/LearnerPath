import { type FormEvent, useState } from 'react'
import { motion } from 'framer-motion'
import { LockKeyhole, User } from 'lucide-react'

const ACCOUNTS: Record<string, string> = {
  Gaurav_001: 'Admin@123',
  Shyam_001: 'Admin@456',
}

type Props = {
  onLogin: (username: string) => void
}

export default function LoginPage({ onLogin }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (ACCOUNTS[username] !== password) {
      setError('Incorrect username or password.')
      return
    }
    onLogin(username)
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 relative overflow-hidden">
      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={signIn}
        className="glass p-8 max-w-md w-full"
      >
        <img
          src="/realty-shiksha-logo.jpeg"
          alt="Realty Shiksha"
          className="w-24 h-24 object-contain rounded-full mx-auto mb-5"
        />
        <div className="text-center mb-7">
          <h1 className="text-3xl font-display font-semibold">Realty Shiksha</h1>
          <p className="text-sm text-slate-400 mt-2">Knowledge that builds futures.</p>
        </div>

        <label className="block text-sm font-medium text-slate-300 mb-2" htmlFor="username">
          Username
        </label>
        <div className="relative mb-5">
          <User className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
          <input
            id="username"
            className="input pl-10"
            autoComplete="username"
            value={username}
            onChange={event => setUsername(event.target.value)}
            required
          />
        </div>

        <label className="block text-sm font-medium text-slate-300 mb-2" htmlFor="password">
          Password
        </label>
        <div className="relative">
          <LockKeyhole className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
          <input
            id="password"
            type="password"
            className="input pl-10"
            autoComplete="current-password"
            value={password}
            onChange={event => setPassword(event.target.value)}
            required
          />
        </div>

        {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}

        <button type="submit" className="btn-primary w-full mt-6">
          Sign in
        </button>
      </motion.form>
    </div>
  )
}