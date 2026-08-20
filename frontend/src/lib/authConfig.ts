import { Configuration, LogLevel, PublicClientApplication } from '@azure/msal-browser'

const tenantSubdomain = import.meta.env.VITE_ENTRA_TENANT_SUBDOMAIN as string | undefined
const clientId = import.meta.env.VITE_ENTRA_CLIENT_ID as string | undefined
const apiScope = import.meta.env.VITE_ENTRA_API_SCOPE as string | undefined

export const entraConfigured = Boolean(tenantSubdomain && clientId)

export const authority = tenantSubdomain
  ? `https://${tenantSubdomain}.ciamlogin.com/${tenantSubdomain}.onmicrosoft.com`
  : ''

export const msalConfig: Configuration = {
  auth: {
    clientId: clientId ?? '',
    authority,
    knownAuthorities: tenantSubdomain ? [`${tenantSubdomain}.ciamlogin.com`] : [],
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
    navigateToLoginRequestUrl: false,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message) => {
        if (level === LogLevel.Error) console.error('[msal]', message)
      },
      logLevel: LogLevel.Warning,
    },
  },
}

export const loginRequest = {
  scopes: ['openid', 'profile', 'offline_access', ...(apiScope ? [apiScope] : [])],
}

export const apiTokenRequest = {
  scopes: apiScope ? [apiScope] : ['openid'],
}

export const msalInstance = new PublicClientApplication(msalConfig)
