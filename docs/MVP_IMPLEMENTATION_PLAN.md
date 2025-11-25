# MVP Implementation Plan — Core Writing Experience

## Goals & Scope
- Deliver the three-panel authenticated workspace (sources / document / assistant) for an MVP, leaving landing + auth intact.
- Align with techspec flows and guidelines: thin route modules, feature scoping under `app/(auth)/`, shared UI in `src/components`, API helpers in `src/lib/api`.
- Support: create/open/resume documents, edit content with autosave stubs, surface related sources, drag-and-drop citations, and assistant conversations with mocked messages.

## Architecture & Foldering
- Routes: `app/(auth)/documents/page.tsx` (list/create), `app/(auth)/documents/[id]/page.tsx` (workspace shell), with `_components`, `_hooks`, `_schemas`, and `data.ts`/`actions.ts` per route.
- Shared primitives: `src/components/editor/*` (lightweight rich text / text area + selection tracking), `src/components/panels/*` (sources, assistant), `src/components/layout/workspace-shell.tsx`.
- API layer: add modules for `documents`, `document-content`, `citations`, `content`, `conversations`, `messages` under `src/lib/api/`, typed via `src/types/*`. Use `NEXT_PUBLIC_USE_MOCKS` fallbacks for stubbed endpoints.
- State: minimal client state via React hooks; cache server data with per-feature hooks (e.g., `useDocumentContent`, `useSourcesFeed`). Avoid global stores until needed.
- Drag/drop: prefer React DnD or native HTML5; keep logic in a small client component co-located with the editor.

## Phased Implementation
1) Foundations
   - Confirm env vars (`NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_USE_MOCKS`) and extend mocks for content, conversations, and doc content/citations/messages.
   - Set up route scaffolds, loading/error states, and shared layout shell matching the wireframe proportions.
   - Define types/interfaces for Document, DocumentContent, ContentItem, Citation, Conversation, Message, SelectionContext.
2) Document lifecycle (Flow 1)
   - Implement document list fetch (`GET /documents`) with skeleton/empty states.
   - One-click create (`POST /documents`) and redirect into `[id]` workspace.
   - Open/resume: `GET /documents/{id}` fetcher + optimistic navigation/error guard.
3) Editor & content persistence (Flow 2)
   - Editor component with paragraph-level selection tracking (to drive suggestions); start with structured contenteditable/textarea + block parsing.
   - Load content sections: `GET /documents/{id}/content`; display word count/updated_at when available.
   - Autosave pipeline: debounce on change/blur, call `PUT /documents/{id}/content` with the full ordered sections array (no PATCH for MVP); keep local dirty state + last-saved indicator; handle failure toast.
4) Sources panel (Flow 3)
   - Initial feed: Empty state (no results until a section has text).
   - On section change (per-section basis): call `POST /content/search` with `{ query: <section text>, limit: 20 }` to surface related content.
5) Drag-and-drop citations (Flow 4)
   - Enable drag from sources list to editor drop targets; insert `[n]` markers and maintain `{marker -> content_id}` map with reorder/undo/remove.
   - Persist via `POST /documents/{id}/citations`, `GET /documents/{id}/citations`, `PATCH /citations/{id}`, `DELETE /citations/{id}`.
6) Assistant panel (Flow 5)
   - Conversation list: `GET /conversations?sorts=created_at:desc`, filter by `document_id` client-side for doc view.
   - Create conversation (`POST /conversations`) + load metadata (`GET /conversations/{id}`).
   - Messages: live `GET/POST /conversations/{id}/messages` with support for `context_sources` (add streaming/effects as implemented).
7) Cross-cutting quality
   - Add empty/loading/error components per route (guideline 8) and smoke tests for pure helpers (selection parser, citation numbering, mock suggest scorer).
   - Telemetry hooks for key events (doc created, autosave success/fail, citation added/removed, message sent).

## Decisions (closing open questions)
- Editor: start with minimal contenteditable/text-area + custom blocks; keep an adapter layer so we can swap to TipTap/Lexical if needed later.
- Autosave: debounce 800–1200ms after typing stops; also trigger on blur/navigation. Show “Saving…” / “Saved” states; retry with backoff on failure.
- Sections: delineated by double newline only; no max length. UI should clearly show a new paragraph/section on double newline.
- Citation UX: markers auto-renumber on insert/delete; maintain a sidebar/inline list for quick jump + delete. Drag/drop inserts `[n]` at drop point and updates the local `{marker -> content_id}` map and pending list for sync.
- Content relevance: defer optimization; keep simple keyword overlap heuristic as stub.
- Assistant context: attach full content item when dropped; cap later if needed.
- Offline/unsaved: rely on autosave + “pending” badge; warn only if pending fails repeatedly.
- Access control: assume org-level access to `/content`; no per-doc sharing modeled in FE (handled by backend).
