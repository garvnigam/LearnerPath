import { useEffect, useState } from 'react'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import { apiPost } from './api'
import { entraConfigured } from './authConfig'

export type SessionState =
  | { status: 'idle' }
  | { status: 'checking' }
  | { status: 'active'; expiresAt: number; isUnlimited: boolean; remaining: number }
  | { status: 'blocked'; reason: string }
  | { status: 'network_error'; message: string }
  | { status: 'expired' }

type StartResp = {
  allowed: boolean
  is_unlimited: boolean
  ttl_seconds: number
  session_expires_at: number
}

export function useSessionQuota() {
  const { instance } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const [state, setState] = useState<SessionState>({ status: 'idle' })

  useEffect(() => {
    if (!entraConfigured || !isAuthenticated) return
    let cancelled = false
    setState({ status: 'checking' })
    ;(async () => {
      try {
        const r = await apiPost<StartResp>('/api/session/start', {})
        if (cancelled) return
        const expiresAtMs = r.session_expires_at * 1000
        setState({
          status: 'active',
          expiresAt: expiresAtMs,
          isUnlimited: r.is_unlimited,
          remaining: Math.max(0, Math.floor((expiresAtMs - Date.now()) / 1000)),
        })
      } catch (e: any) {
        if (cancelled) return
        const msg = String(e?.message || '')
        if (msg.startsWith('403')) {
          const reason = msg.replace(/^403:\s*/, '').replace(/^"|"$/g, '')
          setState({ status: 'blocked', reason: reason || 'Login not allowed.' })
        } else {
          setState({ status: 'network_error', message: msg || 'Could not reach the backend.' })
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [isAuthenticated])

  useEffect(() => {
    if (state.status !== 'active' || state.isUnlimited) return
    const tick = () => {
      const remaining = Math.max(0, Math.floor((state.expiresAt - Date.now()) / 1000))
      if (remaining <= 0) {
        setState({ status: 'expired' })
        instance.logoutRedirect({ postLogoutRedirectUri: window.location.origin }).catch(() => {})
        return
      }
      setState({ ...state, remaining })
    }
    tick()
    const id = window.setInterval(tick, 1000)
    return () => window.clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.status, (state as any).expiresAt, (state as any).isUnlimited])

  return state
}
