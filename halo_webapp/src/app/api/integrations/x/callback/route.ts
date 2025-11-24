import { NextRequest, NextResponse } from "next/server"
import { env } from "@/app/env"
import { serverEnv } from "@/app/env.server"

const TOKEN_URL = "https://api.x.com/2/oauth2/token"
const ME_URL = "https://api.x.com/2/users/me"
const AUTH_TOKEN_COOKIE = "x_auth_token"
const PKCE_VERIFIER_KEY_PREFIX = "x_pkce_verifier_"
const STATE_KEY_PREFIX = "x_oauth_state_"

function redirectWithParams(request: NextRequest, path: string, params: Record<string, string | number | undefined>) {
  const base = env.NEXT_PUBLIC_APP_URL || request.nextUrl.origin
  const url = new URL(path, base)
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, String(value))
    }
  })
  return NextResponse.redirect(url.toString())
}

function decodeState(state: string) {
  try {
    const decoded = Buffer.from(state, "base64").toString("utf-8")
    return JSON.parse(decoded) as { plugin_id: number; nonce: string; return_path?: string; is_new?: boolean }
  } catch {
    return null
  }
}

async function deletePluginIfNew(
  apiBase: string,
  pluginId: number,
  authToken: string,
  isNew?: boolean,
  reason?: string,
) {
  if (!isNew) return
  try {
    await fetch(`${apiBase}/plugins/${pluginId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${authToken}`,
        "X-Delete-Reason": reason || "oauth_failed",
      },
    })
  } catch (err) {
    console.warn("Failed to delete plugin after OAuth failure", err)
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl
  const code = searchParams.get("code")
  const stateParam = searchParams.get("state")
  const error = searchParams.get("error")

  if (error) {
    return redirectWithParams(request, "/plugins", { x_oauth_error: error })
  }

  if (!code || !stateParam) {
    return redirectWithParams(request, "/plugins", { x_oauth_error: "missing_params" })
  }

  const state = decodeState(stateParam)
  if (!state || !state.plugin_id || !state.nonce) {
    return redirectWithParams(request, "/plugins", { x_oauth_error: "invalid_state" })
  }

  const verifierKey = `${PKCE_VERIFIER_KEY_PREFIX}${state.plugin_id}`
  const stateKey = `${STATE_KEY_PREFIX}${state.plugin_id}`

  const cookies = request.cookies
  const storedState = cookies.get(stateKey)?.value
  const codeVerifier = cookies.get(verifierKey)?.value
  const authToken = cookies.get(AUTH_TOKEN_COOKIE)?.value

  if (!storedState || storedState !== stateParam) {
    const resp = redirectWithParams(request, state.return_path || "/plugins", { x_oauth_error: "state_mismatch" })
    resp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
    return resp
  }

  if (!codeVerifier) {
    const resp = redirectWithParams(request, state.return_path || "/plugins", { x_oauth_error: "missing_verifier" })
    resp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
    return resp
  }

  if (!authToken) {
    const resp = redirectWithParams(request, state.return_path || "/plugins", { x_oauth_error: "missing_auth" })
    resp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
    return resp
  }

  const apiBase = env.NEXT_PUBLIC_API_URL

  const clientId = env.NEXT_PUBLIC_X_OAUTH_CLIENT_ID
  const redirectUri = env.NEXT_PUBLIC_X_OAUTH_REDIRECT_URI
  const clientSecret = serverEnv.X_OAUTH_CLIENT_SECRET

  if (!clientId || !redirectUri || !clientSecret) {
    const resp = redirectWithParams(request, state.return_path || "/plugins", { x_oauth_error: "misconfigured" })
    resp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
    return resp
  }

  const tokenBody = new URLSearchParams({
    grant_type: "authorization_code",
    code,
    code_verifier: codeVerifier,
    redirect_uri: redirectUri,
    client_id: clientId,
  })

  const basicAuth = Buffer.from(`${clientId}:${clientSecret}`).toString("base64")

  const tokenResponse = await fetch(TOKEN_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Authorization: `Basic ${basicAuth}`,
    },
    body: tokenBody.toString(),
  })

  if (!tokenResponse.ok) {
    let errorDetail: string | undefined
    try {
      const text = await tokenResponse.text()
      console.error("X token exchange failed", { status: tokenResponse.status, body: text })
      errorDetail = text?.slice(0, 200)
    } catch (e) {
      console.error("X token exchange failed and body read errored", e)
    }

    const resp = redirectWithParams(request, state.return_path || "/plugins", {
      x_oauth_error: "token_exchange_failed",
      x_oauth_error_detail: errorDetail,
    })
    resp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
    if (apiBase && authToken) {
      await deletePluginIfNew(apiBase, state.plugin_id, authToken, state.is_new, "token_exchange_failed")
    }
    return resp
  }

  const tokenJson = await tokenResponse.json()
  const { access_token, refresh_token, scope } = tokenJson as {
    access_token?: string
    refresh_token?: string
    scope?: string
  }

  if (!refresh_token) {
    const resp = redirectWithParams(request, state.return_path || "/plugins", { x_oauth_error: "refresh_token_missing" })
    resp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
    if (apiBase && authToken) {
      await deletePluginIfNew(apiBase, state.plugin_id, authToken, state.is_new, "refresh_token_missing")
    }
    return resp
  }

  // We still need the access_token temporarily to fetch the user profile
  if (!access_token) {
    const resp = redirectWithParams(request, state.return_path || "/plugins", { x_oauth_error: "access_token_missing" })
    resp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
    if (apiBase && authToken) {
      await deletePluginIfNew(apiBase, state.plugin_id, authToken, state.is_new, "access_token_missing")
    }
    return resp
  }

  let profile: { id?: string; username?: string; name?: string; profile_image_url?: string } = {}
  try {
    const meResp = await fetch(`${ME_URL}?user.fields=profile_image_url`, {
      headers: { Authorization: `Bearer ${access_token}` },
    })
    if (meResp.ok) {
      const meJson = await meResp.json()
      if (meJson?.data) {
        profile = {
          id: meJson.data.id,
          username: meJson.data.username,
          name: meJson.data.name,
          profile_image_url: meJson.data.profile_image_url,
        }
      }
    }
  } catch (err) {
    console.warn("Failed to fetch X user profile", err)
  }

  if (!apiBase) {
    const resp = redirectWithParams(request, state.return_path || "/plugins", { x_oauth_error: "api_missing" })
    resp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
    return resp
  }

  const pluginUpdate = {
    credentials: {
      status: "connected",
      access_token,
      refresh_token,
      token_type: tokenJson.token_type || "bearer",
      expires_in: tokenJson.expires_in,
      token_obtained_at: new Date().toISOString(),
      scope: scope || env.NEXT_PUBLIC_X_OAUTH_SCOPES || "",
      connected_at: new Date().toISOString(),
    },
    properties: {
      x_user_id: profile.id,
      username: profile.username,
      name: profile.name,
      avatar_url: profile.profile_image_url,
      connected_at: new Date().toISOString(),
    },
  }

  const apiResp = await fetch(`${apiBase}/plugins/${state.plugin_id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${authToken}`,
    },
    body: JSON.stringify(pluginUpdate),
  })

  if (!apiResp.ok) {
    const resp = redirectWithParams(request, state.return_path || "/plugins", { x_oauth_error: "persist_failed" })
    resp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
    resp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
    await deletePluginIfNew(apiBase, state.plugin_id, authToken, state.is_new, "persist_failed")
    return resp
  }

  const successResp = redirectWithParams(request, state.return_path || "/plugins", {
    x_oauth_success: "true",
    plugin_id: state.plugin_id,
  })
  successResp.cookies.set(verifierKey, "", { path: "/", maxAge: 0 })
  successResp.cookies.set(stateKey, "", { path: "/", maxAge: 0 })
  successResp.cookies.set(AUTH_TOKEN_COOKIE, "", { path: "/", maxAge: 0 })
  return successResp
}
