import React from 'react'
import ReactDOM from 'react-dom/client'
import { MsalProvider } from '@azure/msal-react'
import { EventType } from '@azure/msal-browser'
import App from './App'
import './index.css'
import { msalInstance, entraConfigured } from './lib/authConfig'

async function bootstrap() {
  if (entraConfigured) {
    await msalInstance.initialize()
    const accounts = msalInstance.getAllAccounts()
    if (accounts.length > 0) msalInstance.setActiveAccount(accounts[0])
    msalInstance.addEventCallback((event) => {
      if (event.eventType === EventType.LOGIN_SUCCESS && event.payload && 'account' in event.payload) {
        msalInstance.setActiveAccount((event.payload as any).account)
      }
    })
    await msalInstance.handleRedirectPromise().catch((e) => console.error('[msal] redirect error', e))
  }

  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </React.StrictMode>
  )
}

bootstrap()
