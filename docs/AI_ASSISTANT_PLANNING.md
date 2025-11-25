# AI Assistant Planning

## Goals
- Provide a conversational assistant inside the document workspace that feels responsive, explains what it is doing, and is easy to extend with richer orchestration later.
- Reuse Fury’s reusable services (SqlService, UnitOfWork) and avoid bespoke “one-off” code while leaving space for background jobs, telemetry, and tool integrations.
- Ship an MVP quickly (mocked assistant replies) without compromising the end-state architecture.

## Target Experience
1. User submits a prompt in the assistant panel, optionally attaching document sections or source IDs.
2. Backend immediately acknowledges, persists the user message, and emits “status” events (queued → collecting context → generating → completed) over a live connection so the UI can show progress.
3. Once the model finishes, the assistant message is saved and streamed to the client; contextual metadata (token counts, references, tool calls) is attached for display.
4. Historical conversations/messages remain queryable via the standard `/conversations` and `/conversations/{id}/messages` endpoints.

## Architecture Overview

### API Surface
- `POST /conversations/{id}/messages`: accepts `{ role, content, context, model_hint }`. Persists the user message, spawns assistant work, and returns `{ message_id, stream_token }`.
  - `context` structure:
    ```json
    {
      "section_ids": [1, 3, 5],
      "content_ids": [42, 89],
      "selection": {
        "text": "selected text...",
        "section_index": 2,
        "start": 100,
        "end": 250
      }
    }
    ```
- `GET /conversations/{id}/messages/stream?token=...`: Server-Sent Events stream that pushes progress packets (`status`, `delta_text`, `completed`, `error`). Backed by `EventSourceResponse` (FastAPI) + an async generator.
- Existing `GET` endpoints keep serving pagination for historical data.

### Persistence
- Extend `Message` with:
  - `status: Literal["queued","running","completed","failed"]`.
  - `metadata: JSON` for trace steps, token counts, tool call info, etc.
  - Optional `parent_message_id` for threading and `response_for_id` to pair assistant replies with user prompts.
- Optional future table `message_events` if we decide to store every streamed status for analytics.

### Workflow Execution
- POST handler validates data, sets organization/conversation IDs via SqlService, and enqueues work.
- **Short term:** synchronous mock – immediately create both user + assistant messages.
- **Future:** background worker (Celery/Dramatiq/async queue) pulls jobs, performs:
  1. Gather context (document sections, citations, explicit IDs).
  2. Build prompt/tool spec.
  3. Call LLM provider (OpenAI, Vertex, Bedrock).
  4. Persist assistant reply + metadata, push stream events.

### Streaming Channel
- For MVP: in-memory `dict[int, asyncio.Queue]` keyed by conversation, populated inside the POST handler to fake progress.
- Later: replace the queue with Redis pub/sub or Kafka so multiple app instances can publish/consume events.
- Event schema:
  ```json
  {"type":"status","stage":"collecting_context"}
  {"type":"delta","chunk":"Hello, "}
  {"type":"delta","chunk":"world!"}
  {"type":"completed","assistant_message_id":123}
  {"type":"error","message":"Model timeout"}
  ```

### Context Window Management (Industry Best Practice)

**Token Budget Strategy:**
- Reserve 500 tokens for system prompt
- Reserve 1000 tokens for user message + response buffer
- Remaining ~6500 tokens (for 8k context models) split:
  - 40% conversation history (recent messages for continuity)
  - 60% attached context (document sections + cited sources)

**Context Sources (Priority Order):**
1. **User Selection** - Currently selected text (auto-included if present)
2. **Explicit Attachments** - Sections/sources user drags into chat
3. **Conversation History** - Last 5 messages for context continuity

**Over-Budget Handling:**
1. Truncate oldest conversation messages first
2. Summarize long sections (first 200 + last 100 characters)
3. For sources: prefer excerpt/summary fields over full body
4. Log token counts in message metadata for observability

**Prompt Construction Template:**
```
System: [System prompt with document context instructions]

[Conversation history - last N messages]

Context:
Document Sections:
- Section 1: [content]
- Section 3: [content]

Related Sources:
- Source title: [summary/excerpt]

User Selection: [if present]

User: [current message]
```

## Implementation Phases

1. **Step 1 – MVP (mocked assistant)**
   - Update `Message` model with `status` + `metadata`.
   - POST `/messages`: persist user message, immediately create assistant reply with canned text, set `status="completed"`.
   - Add SSE endpoint that emits a scripted sequence (`queued → generating → completed`) while the synchronous logic runs. No background jobs yet.
   - FE can already render progress + consume final data.

2. **Step 2 – Async job skeleton**
   - Introduce an internal `AssistantWorkflowService` plus a simple asyncio task queue (or Celery if infra ready).
   - POST only persists user message + enqueues job, SSE relays real task progress.
   - Assistant reply is persisted once the worker finishes; UI receives text via SSE and sees it in standard list endpoint.

3. **Step 3 – Real LLM + context retrieval**
   - Integrate provider client(s), implement context fetcher (document sections, citations, uploaded files).
   - Support configurable models and plugin/tool execution.
   - Store detailed metadata for analytics/auditing.

4. **Step 4 – Advanced UX**
   - Bidirectional streaming (WebSockets) if needed, cancellation, retries, telemetry hooks, user-tunable system prompts.

## Immediate Next Actions
1. Land Step-1 code changes (schema update, mocked assistant reply, SSE stub).
2. Update API docs to include the new SSE endpoint and message fields.
3. Align frontend to consume the stream and display status pills.
