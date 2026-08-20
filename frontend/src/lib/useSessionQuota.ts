import { useEffect, useState } from 'react'
import { useIsAuthenticated } from '@azure/msal-react'
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
  const isAuthenticated = useIsAuthenticated()
  const [state, setState] = useState<SessionState>({ status: 'idle' })

  useEffect(() => {
    if (!entraConfigured || !isAuthenticated) return
    let cancelled = false
    setState({ status: 'checking' })
    // Fire-and-forget: quotas are disabled for MVP, but we still call
    // /session/start so backend logs the event. Any outcome -> unlimited.
    ;(async () => {
      try {
        await apiPost<StartResp>('/api/session/start', {})
      } catch {
        // ignore — quotas disabled on client side too
      }
      if (cancelled) return
      setState({
        status: 'active',
        expiresAt: Number.POSITIVE_INFINITY,
        isUnlimited: true,
        remaining: 0,
      })
    })()
    return () => {
      cancelled = true
    }
  }, [isAuthenticated])

  return state
}
