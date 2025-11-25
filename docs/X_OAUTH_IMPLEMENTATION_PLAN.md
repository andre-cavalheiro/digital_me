# X OAuth Integration Plan

This plan describes how to add X (Twitter) OAuth to the product while **leaving the DB schema unchanged** and keeping backend churn minimal. The goal is to persist X authentication artifacts inside each plugin’s `credentials` JSON, driven primarily from the frontend/Next.js layer.

## Goals & Constraints
- No schema changes; reuse `plugin.credentials` (JSON) to store auth artifacts.
- Minimize FastAPI changes; prefer handling OAuth in the Next.js app (server routes) while the API simply persists credentials.
- Keep secrets off the client; token exchange/refresh happens server-side (Next.js route or a small API endpoint if absolutely required).
- Avoid exposing raw tokens in `PluginRead` responses (current API already omits `credentials`).

## Assumptions
- We have X API credentials (client_id + client_secret) and allowed redirect URIs we can configure.
- The frontend can register a Next.js route handler (e.g., `/api/integrations/x/callback`) that can use server-side env vars.
- Existing plugin CRUD endpoints remain as-is (`POST /plugins`, `PUT /plugins/{id}`) and accept a `credentials` payload for persistence.
- Only one X plugin per organization is expected (mirrors current `data_source` usage in the UI).

## Happy-Path Flow (with data passed step-to-step)
1. **User clicks “Install X”**
   - FE checks for an existing X plugin via `GET /plugins`; if none, it `POST`s `/plugins` with `data_source: "x"`, `title: "X"`, `credentials: {status: "pending"}`.
   - Output: `plugin_id` to bind the OAuth attempt to a record.
2. **Generate OAuth parameters on FE**
   - FE creates a `state` blob `{ plugin_id, nonce, return_path }` (base64/URL-safe JSON) for CSRF + context and stores it in `sessionStorage`.
   - FE generates PKCE `code_verifier` + `code_challenge` and stores the verifier in client storage tied to `plugin_id` (or better: an httpOnly, short-lived cookie set by a server “/start” route) to satisfy X’s PKCE requirement.
3. **Redirect user to X authorize endpoint**
   - Endpoint: `https://twitter.com/i/oauth2/authorize`.
   - Parameters: `client_id`, `redirect_uri` (Next.js server route), `response_type=code`, `scope=users.read tweet.read offline.access` (or required scope set), `code_challenge`, `code_challenge_method=S256`, `state`.
   - Why: scopes define accessible operations; PKCE is required per X docs; `state` ties callback to `plugin_id`.
4. **X redirects to callback with `code` + `state`**
   - Handled by Next.js **server route** (not a client page) at `/api/integrations/x/callback`.
   - It validates `state` (parse + compare `nonce` against stored value) and reads `code_verifier` from server cookies/session or encrypted token echoed back by the FE (if we forward it with `state`).
5. **Server-side token exchange**
   - Endpoint: `https://api.x.com/2/oauth2/token`.
   - The server route calls X’s token endpoint with `grant_type=authorization_code`, `code`, `code_verifier`, `redirect_uri`, `client_id`, and **server-held** `client_secret` when using confidential client credentials (PKCE still required).
   - Output: `{ access_token, refresh_token, expires_in, scope, token_type }` (bearer). Offline refresh requires the `offline.access` scope.
   - Optional: call `GET users/me` with the new token to fetch `{ user_id, username, name, profile_image_url }` for plugin metadata.
6. **Persist credentials to the API**
   - Server route calls `PUT /plugins/{plugin_id}` with:
     - `credentials`: `{ access_token, refresh_token, expires_at: now+expires_in, token_type, scope, obtained_at: now, status: "connected" }`.
     - `properties` (optional quality-of-life): `{ x_user_id, username, name, avatar_url }` for display.
   - Rationale: keep tokens in `credentials`; keep non-sensitive profile metadata in `properties` for UI use.
7. **Return user to the app**
   - Redirect to `/plugins?connected=x` (or `return_path`) for a success toast.
   - UI reads plugin list again to reflect the “connected” state (it won’t see credentials, only properties/status).

## Error & Recovery Flows
- **State/PKCE mismatch**: abort, log, and redirect to `/plugins?error=state` with no plugin update (credentials remain pending).
- **Token exchange failure**: keep plugin `credentials.status="error"` with `credentials.error_reason` for observability; surface a retry CTA.
- **User cancels**: callback receives `error=access_denied`; mark plugin as `credentials.status="cancelled"` or delete the placeholder plugin.
- **Refresh handling**: future cron/worker or x-client can refresh using `refresh_token`; store `refresh_token_expires_at` if X returns it. No schema change needed—store in `credentials`.

## Data Shapes to Persist in `plugin.credentials`
```json
{
  "status": "connected",
  "access_token": "…",
  "refresh_token": "…",
  "expires_at": "2025-03-01T12:00:00Z",
  "token_type": "bearer",
  "scope": "tweet.read users.read offline.access",
  "obtained_at": "2025-02-27T12:00:00Z",
  "refresh_token_expires_at": "2025-09-01T12:00:00Z",
  "nonce": "…",                // optional: to correlate the last handshake
  "error_reason": null         // set on failure paths
}
```
`plugin.properties` can carry non-sensitive display data:
```json
{
  "x_user_id": "12345",
  "username": "example",
  "name": "Example User",
  "avatar_url": "https://…/normal.jpg",
  "connected_at": "2025-02-27T12:00:00Z"
}
```

## Responsibility Split (minimal backend changes)
- **Frontend (client)**: trigger install, manage state/UI, generate PKCE, redirect to X, handle success/failure redirects.
- **Next.js server route**: validate state, perform token exchange with server-held secrets, optionally fetch `users/me`, and call `PUT /plugins/{id}` to persist credentials/properties.
- **FastAPI backend**: no schema changes; ensure `PUT /plugins/{id}` continues to accept `credentials` JSON. Optional: add lightweight validation/logging or redact credentials from logs; no new endpoints unless we decide to move token exchange into the API.

## Implementation Phases
1. **Prep**
   - Add X client ID/secret + redirect URI to envs (Next.js + optionally FastAPI for future use).
   - Document required scopes and redirect URIs in both environments.
2. **Frontend UI & state wiring**
   - Update the plugins page to use the OAuth start flow (create/find plugin, generate state + PKCE, redirect).
   - Add success/error toasts based on callback query params.
3. **Server-side OAuth handler**
   - Implement Next.js route for `/api/integrations/x/callback` (or `/api/integrations/x/start` + `/callback` pair if we want the start step server-side).
   - Handle state validation, token exchange, optional `users/me`, and persistence to `/api/v1/plugins/{id}`.
4. **Resilience & UX polish**
   - Handle cancel/error paths, pending state cleanup, and idempotent retries (reuse existing plugin if `credentials.status` is not connected).
   - Add minimal logging/metrics around handshake outcomes (log token exchange failures with status + truncated body and surface `x_oauth_error_detail` in redirect for debugging). Include `Authorization: Basic base64(client_id:client_secret)` on token exchange for X confidential clients.
5. **Post-launch follow-ups (out of scope now)**
  - Wire x-client/worker to read `credentials` from the DB and refresh tokens when expired.
  - Consider encrypting credentials at rest if required by compliance.

## X OAuth concrete configuration (current)
- Redirect URI: `https://digital-me.app/api/integrations/x/callback` (set `NEXT_PUBLIC_APP_URL=https://digital-me.app` in prod so redirects land on the correct host)
- Scopes: `tweet.read`, `follows.read`, `users.read`, `bookmark.read`, `offline.access` (offline.access is required to receive refresh tokens)
- Client ID: configured in `NEXT_PUBLIC_X_OAUTH_CLIENT_ID`
- Client secret (server-only): `X_OAUTH_CLIENT_SECRET`
- Frontend envs: `NEXT_PUBLIC_X_OAUTH_CLIENT_ID`, `NEXT_PUBLIC_X_OAUTH_REDIRECT_URI`, `NEXT_PUBLIC_X_OAUTH_SCOPES`
