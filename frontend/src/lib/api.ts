import { apiTokenRequest, entraConfigured, msalInstance } from './authConfig'
import { InteractionRequiredAuthError } from '@azure/msal-browser'

const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')

function apiUrl(path: string): string {
  if (!API) {
    throw new Error('Application API is not configured. Set VITE_API_URL to the deployed backend URL.')
  }
  return `${API.replace(/\/$/, '')}${path}`
}

async function getAccessToken(): Promise<string | null> {
  // DEV: login disabled temporarily — skip MSAL token acquisition entirely so a stale/
  // cached account doesn't trigger a background network call to Microsoft that can fail.
  // Uncomment the block below to re-enable once login is turned back on.
  return null

  // if (!entraConfigured) return null
  // const account = msalInstance.getActiveAccount() ?? msalInstance.getAllAccounts()[0]
  // if (!account) return null
  // try {
  //   const res = await msalInstance.acquireTokenSilent({ ...apiTokenRequest, account })
  //   return res.accessToken || res.idToken || null
  // } catch (e) {
  //   console.warn('[msal] silent token acquisition failed', e)
  //   if (e instanceof InteractionRequiredAuthError) {
  //     try {
  //       const res = await msalInstance.acquireTokenPopup({ ...apiTokenRequest, account })
  //       return res.accessToken || res.idToken || null
  //     } catch (err) {
  //       console.error('[msal] popup token acquisition failed', err)
  //       throw new Error('Sign-in required. Please sign in again.')
  //     }
  //   }
  //   throw new Error('Unable to acquire access token. Please sign in again.')
  // }
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = await getAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(apiUrl(path), {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const t = await res.text()
    throw new Error(`${res.status}: ${t}`)
  }
  return res.json() as Promise<T>
}

export async function apiGet<T>(path: string): Promise<T> {
  const headers: Record<string, string> = {}
  const token = await getAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(apiUrl(path), { method: 'GET', headers })
  if (!res.ok) {
    const t = await res.text()
    throw new Error(`${res.status}: ${t}`)
  }
  return res.json() as Promise<T>
}
