import { env } from "@/app/env"
import { auth } from "@/lib/auth/firebase"

const AUTHORIZE_URL = "https://twitter.com/i/oauth2/authorize"
const PKCE_VERIFIER_KEY_PREFIX = "x_pkce_verifier_"
const STATE_KEY_PREFIX = "x_oauth_state_"
const AUTH_TOKEN_COOKIE = "x_auth_token"

type XOauthConfig = {
  clientId: string
  redirectUri: string
  scopes: string[]
}

const textEncoder = new TextEncoder()

function base64UrlEncode(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ""
  bytes.forEach((b) => {
    binary += String.fromCharCode(b)
  })
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
}

function getConfig(): XOauthConfig {
  const clientId = env.NEXT_PUBLIC_X_OAUTH_CLIENT_ID
  const redirectUri = env.NEXT_PUBLIC_X_OAUTH_REDIRECT_URI
  const scopes = (env.NEXT_PUBLIC_X_OAUTH_SCOPES || "").replace(/"/g, "").split(/\s+/).filter(Boolean)

  if (!clientId || !redirectUri) {
    throw new Error("X OAuth is not configured (missing client id or redirect URI)")
  }
  if (scopes.length === 0) {
    throw new Error("X OAuth scopes are not configured")
  }

  return { clientId, redirectUri, scopes }
}

function randomString(byteLength = 32): string {
  const bytes = new Uint8Array(byteLength)
  crypto.getRandomValues(bytes)
  return base64UrlEncode(bytes.buffer)
}

async function generateCodeChallenge(verifier: string): Promise<string> {
  const data = textEncoder.encode(verifier)
  const digest = await crypto.subtle.digest("SHA-256", data)
  return base64UrlEncode(digest)
}

function storeTemporary(key: string, value: string): void {
  if (typeof window === "undefined") return
  sessionStorage.setItem(key, value)
}

function setCookie(name: string, value: string, minutes = 10): void {
  if (typeof document === "undefined") return
  const expires = new Date(Date.now() + minutes * 60 * 1000).toUTCString()
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax; secure`
}

function buildVerifierKey(pluginId: number): string {
  return `${PKCE_VERIFIER_KEY_PREFIX}${pluginId}`
}

function buildStateKey(pluginId: number): string {
  return `${STATE_KEY_PREFIX}${pluginId}`
}

export function getStoredVerifier(pluginId: number): string | null {
  if (typeof window === "undefined") return null
  return sessionStorage.getItem(buildVerifierKey(pluginId))
}

export function getStoredState(pluginId: number): string | null {
  if (typeof window === "undefined") return null
  return sessionStorage.getItem(buildStateKey(pluginId))
}

export async function buildAuthorizeUrl(pluginId: number, returnPath = "/plugins", isNew = false): Promise<string> {
  const { clientId, redirectUri, scopes } = getConfig()

  const codeVerifier = randomString(64)
  const codeChallenge = await generateCodeChallenge(codeVerifier)
  const nonce = randomString(32)

  const statePayload = { plugin_id: pluginId, nonce, return_path: returnPath, is_new: isNew }
  const state = btoa(JSON.stringify(statePayload))

  storeTemporary(buildVerifierKey(pluginId), codeVerifier)
  storeTemporary(buildStateKey(pluginId), state)
  setCookie(buildVerifierKey(pluginId), codeVerifier)
  setCookie(buildStateKey(pluginId), state)

  try {
    const idToken = await auth.currentUser?.getIdToken()
    if (idToken) {
      setCookie(AUTH_TOKEN_COOKIE, idToken)
    }
  } catch (err) {
    console.warn("Could not read Firebase ID token for OAuth flow", err)
  }

  const params = new URLSearchParams({
    response_type: "code",
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: scopes.join(" "),
    state,
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
  })

  return `${AUTHORIZE_URL}?${params.toString()}`
}

export async function startXOauth(pluginId: number, returnPath = "/plugins", isNew = false): Promise<void> {
  if (typeof window === "undefined") {
    throw new Error("OAuth flow must be started from the browser")
  }
  const authorizeUrl = await buildAuthorizeUrl(pluginId, returnPath, isNew)
  window.location.href = authorizeUrl
}
