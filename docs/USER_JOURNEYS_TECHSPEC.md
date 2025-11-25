# Digital Me - Core Writing Flows (Sequenced) & API Calls

Audience: frontend devs. Goal: get the three-panel experience working (left: sources, center: document, right: assistant). We will use all sources (no per-doc config yet) and can cut corners where endpoints are stubbed.

## Assumptions
- Auth context provided by backend (org/user id). API root: `/api/v1`.
- Some endpoints are stubbed (`Not Implemented Yet`); noted inline. Use mocked responses client-side until implemented.
- Sources panel can pull from `/content` now; suggest endpoint is stubbed.

---

## Flow 1: Create/Open/Resume a Document
1) **Create (one click)**
   - Call `POST /documents` with `{ "title": "<auto or user title>" }`.
   - Store returned `document.id`.
2) **List recent docs (dashboard/file picker)**
   - `GET /documents` (pagination ok, default sorts).
3) **Open doc**
   - `GET /documents/{id}` for metadata (title, ids).
   - (Content load is Flow 2.)
4) **Re-open later**
   - Same as open: `GET /documents/{id}` + content fetch.

---

## Flow 2: Load & Edit Document Content
1) **Load content sections**
   - `GET /documents/{id}/content` → returns ordered sections (and derived full content once implemented).
2) **User types / edits**
   - On blur or autosave tick: send the full ordered sections array via `PUT /documents/{id}/content` (no PATCH for MVP).
3) **Section selection**
   - When user selects a paragraph/section, capture the text snippet locally (no backend call needed yet); use it to request suggestions (Flow 3).

---

## Flow 3: Surface Related Content (Left Panel)
We use all sources; no per-doc config.

1) **Initial load (when doc opens)**
   - Call `GET /content?limit=20&sorts=published_at:desc` to prefill the panel.
2) **While typing / on selection change**
   - Use `POST /documents/{id}/content/suggest` with `{ context: "<selection or recent text>", limit: 10 }` for per-doc relevance.
   - For broader search, use `POST /content/search` (optional filters: `source_ids`, `source_group_ids`, `limit`).
3) **View a content item**
   - `GET /content/{id}` to expand details (if needed for a preview modal).

---

## Flow 4: Drag & Drop Content into Document (Citations)
Endpoints are stubbed; frontend should insert markers and sync later.

1) **User drags item from sources → drops in document**
   - Insert inline marker `[n]` at drop position and keep `{marker -> content_id}`.
   - Persist via `POST /documents/{id}/citations` with `{ content_id, position_in_doc, citation_number }`.
2) **List/update/delete citations**
   - `GET /documents/{id}/citations`, `PATCH /citations/{id}`, `DELETE /citations/{id}`.

---

## Flow 5: Assistant Panel (Right) — Conversations & Messages
Conversations/messages endpoints exist; doc-scoped convenience and messaging bodies are stubbed.

1) **Load conversation list (top-right history)**
   - `GET /conversations?sorts=created_at:desc` (optionally filter `document_id` client-side for doc-only view).
2) **Create a new conversation**
   - `POST /conversations` with `{ "title": "<optional>", "document_id": <current doc id> }`. Returns `id`.
3) **Open a conversation**
   - `GET /conversations/{id}` (metadata), then `GET /conversations/{id}/messages`.
4) **Send a message**
   - `POST /conversations/{id}/messages` with `{ role: "user", content: "...", context_sources: [<content_ids>] }`; support streaming if implemented.

---

## Minimal Call Sequence to Recreate the Wireframe
- On app load: `GET /documents` (list), pick/create document.
- After creating/opening:
  - `GET /documents/{id}` (title/ids).
  - `GET /documents/{id}/content` → fill editor with sections.
  - `GET /content?limit=50` → fill left panel initially.
  - `GET /conversations?sorts=created_at:desc` → fill right panel list.
- As user types/selects:
  - `POST /documents/{id}/content/suggest` (doc-scoped relevance) or `POST /content/search` for broader queries.
  - `PUT /documents/{id}/content` on autosave with full sections array.
- Drag/drop source:
  - Insert `[n]` and call `POST /documents/{id}/citations`.
- Assistant:
  - `POST /conversations` to start.
  - `GET /conversations/{id}` + `GET /conversations/{id}/messages`.
  - `POST /conversations/{id}/messages` (with optional `context_sources`).

---

## What FE Should Mock vs. Call Now
- **Call:** `/documents` CRUD, `/documents/{id}/content` (GET/PUT), `/documents/{id}/content/suggest`, `/content` list/get/search, `/documents/{id}/citations` + `/citations/{id}`, `/conversations` CRUD, `/conversations/{id}/messages`.

---

## Near-Term Backend TODO (to unlock full flow)
- Implement and wire: document content GET/PUT; suggest (`/documents/{id}/content/suggest`) and/or `/content/search`; citations create/list/update/delete; messages create/list (with streaming for assistant replies if desired).
