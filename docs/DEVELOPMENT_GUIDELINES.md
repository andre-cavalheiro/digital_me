# Next.js Clean Code Guidelines

Opinionated, Next.js-focused guidelines for modular, readable, maintainable code.

---

## 1. General Principles

- Keep **files small** and single-purpose (aim <200 lines; hard cap ~400).
- Prefer **composition over conditionals** and giant components.
- Separate **data fetching**, **business logic**, and **presentation**.
- Prefer **pure functions** where possible; keep side effects explicit.
- Default to **TypeScript** everywhere; no `any` unless justified.

---

## 2. Project & Folder Structure

Prefer feature-oriented structure over type-based dumping grounds.

```txt
app/
  (segment)/
    feature/
      page.tsx
      layout.tsx
      data.ts          # server data loaders
      actions.ts       # server actions (mutations)
      types.ts         # feature-specific types
      constants.ts
      _components/     # internal UI for this route
      _hooks/          # internal hooks for this route
      _schemas/        # zod/yup schemas
src/
  components/          # shared, reusable components
  lib/                 # shared utilities (api, auth, db, validation)
  hooks/               # shared hooks
  styles/              # global styles, tokens

Rules
	•	If a component/hook is used in only one route, keep it under that route.
	•	If reused across routes, move it to src/components or src/hooks.
	•	Use leading underscore (e.g. _components) for “not routes, not public API”.

⸻

3. page.tsx / Route Modules

page.tsx should be a thin orchestrator.

Do
	•	Fetch data.
	•	Compose feature components.
	•	Pass props.

Don’t
	•	Contain huge JSX trees.
	•	Implement business logic.
	•	Implement complex forms or tables.

// app/dashboard/page.tsx
import { getDashboardData } from "./data";
import { DashboardShell } from "./_components/dashboard-shell";
import { StatsSection } from "./_components/stats-section";
import { ActivityTable } from "./_components/activity-table";

export default async function DashboardPage() {
  const data = await getDashboardData();

  return (
    <DashboardShell>
      <StatsSection stats={data.stats} />
      <ActivityTable items={data.items} />
    </DashboardShell>
  );
}


⸻

4. Server vs Client Components

Default to Server Components; opt into Client Components only when needed.

Server component when:
	•	No React hooks (useState, useEffect, etc.).
	•	Just rendering data / static markup.
	•	Data fetching, composition, layouts.

Client component when:
	•	Needs interactivity (forms, buttons with handlers).
	•	Uses browser APIs or context that depends on the client.
	•	Needs local state or effects.

// app/feature/_components/shell.tsx  (server by default)
export function FeatureShell({ children }: { children: React.ReactNode }) {
  return <section className="space-y-4">{children}</section>;
}

// app/feature/_components/filter-bar.tsx
"use client";

import { useState } from "react";

export function FilterBar(props: FilterBarProps) {
  const [query, setQuery] = useState("");

  // ...
}


⸻

5. Data Fetching & Server Actions

Keep data fetchers and server actions out of components and colocated per feature.

// app/feature/data.ts
import { db } from "@/lib/db";

export async function getFeatureData(userId: string) {
  const [items, stats] = await Promise.all([
    db.item.findMany({ where: { userId } }),
    db.stat.findMany({ where: { userId } }),
  ]);

  return { items, stats };
}

// app/feature/actions.ts
"use server";

import { db } from "@/lib/db";
import { revalidatePath } from "next/cache";

export async function markItemDone(id: string) {
  await db.item.update({ where: { id }, data: { done: true } });
  revalidatePath("/feature");
}

Guidelines
	•	Functions in data.ts should be pure I/O: input → query → typed result.
	•	Functions in actions.ts should:
	•	Validate input (schema).
	•	Perform mutation.
	•	Revalidate relevant paths.
	•	Avoid mixing validation, db, and UI logic in one place.

⸻

6. Components

6.1. Responsibilities
	•	One component = one responsibility.
	•	If a component:
	•	Breaks 150–200 lines, or
	•	Has deeply nested JSX, or
	•	Handles multiple “sections”
→ split into smaller components.

Pattern: Shell + Sections

// app/feature/_components/feature-shell.tsx
export function FeatureShell({ header, children }: FeatureShellProps) {
  return (
    <div className="space-y-6">
      {header}
      <main className="space-y-4">{children}</main>
    </div>
  );
}

// app/feature/_components/list-section.tsx
export function ListSection({ items }: { items: Item[] }) {
  if (!items.length) return <EmptyState />;

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <ListRow key={item.id} item={item} />
      ))}
    </ul>
  );
}

6.2. Props & Types
	•	Always type props explicitly; avoid React.FC unless needed.
	•	Prefer narrow, domain-specific props over dumping raw backend objects.

type ItemRowProps = {
  id: string;
  title: string;
  status: "open" | "done";
};

export function ItemRow({ id, title, status }: ItemRowProps) {
  // ...
}

Use mappers when needed:

// app/feature/mappers.ts
export function mapDbItemToRow(item: DbItem): ItemRowProps {
  return {
    id: item.id,
    title: item.name,
    status: item.done ? "done" : "open",
  };
}


⸻

7. Hooks
	•	Use hooks to encapsulate stateful or derived logic, not as dumping grounds.
	•	Keep feature-specific hooks near their feature (app/feature/_hooks).

// app/feature/_hooks/use-filters.ts
"use client";

import { useState } from "react";

export function useFilters(initial: Filters) {
  const [filters, setFilters] = useState(initial);

  function setStatus(status: Filters["status"]) {
    setFilters((prev) => ({ ...prev, status }));
  }

  return { filters, setStatus };
}

Rules
	•	One hook should have one clear purpose.
	•	If a hook grows too large, split into smaller ones.

⸻

8. Error, Loading & Empty States

Use Next’s error.tsx, loading.tsx, and explicit empty states.

// app/feature/loading.tsx
export default function Loading() {
  return <div>Loading feature…</div>;
}

// app/feature/error.tsx
"use client";

export default function Error({ error }: { error: Error }) {
  return <div>Something went wrong: {error.message}</div>;
}

// app/feature/_components/empty-state.tsx
export function EmptyState() {
  return <p className="text-muted-foreground">No items yet.</p>;
}


⸻

9. Styling & Class Names
	•	Use a consistent styling approach (e.g. Tailwind + design system).
	•	Extract repeated UI into shared components (buttons, cards, inputs).
	•	Use utility helpers for class merging.

// src/lib/utils.ts
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// src/components/ui/button.tsx
import { cn } from "@/lib/utils";

export function Button({ className, ...props }: ButtonProps) {
  return <button className={cn("inline-flex items-center", className)} {...props} />;
}


⸻

10. Naming
	•	Files: kebab-case or dash-case (activity-table.tsx).
	•	Components: PascalCase (ActivityTable).
	•	Hooks: useCamelCase (useDashboardFilters).
	•	Functions: verbNoun (getDashboardData, createSession).
	•	Avoid generic names: no utils.ts, helpers.ts at root; prefer date-utils.ts, validation.ts, etc.

⸻

11. Types & Validation
	•	Centralize domain types in types.ts or shared /src/types.
	•	Use zod/yup for validating server inputs and map to TS types.

// app/feature/_schemas/create-item.ts
import { z } from "zod";

export const createItemSchema = z.object({
  title: z.string().min(1),
  priority: z.enum(["low", "medium", "high"]),
});

export type CreateItemInput = z.infer<typeof createItemSchema>;

// app/feature/actions.ts
"use server";

import { createItemSchema } from "./_schemas/create-item";

export async function createItem(raw: unknown) {
  const data = createItemSchema.parse(raw);
  // ...
}


⸻

12. API & Lib Layer

Keep external concerns (db, auth, external APIs) in src/lib.

// src/lib/db.ts
import { PrismaClient } from "@prisma/client";

export const db = new PrismaClient();

// src/lib/auth.ts
export async function getCurrentUser() {
  // read cookies/session, return user
}

Rules
	•	UI should not import from raw backend clients directly if you can avoid it.
	•	Prefer small, focused helpers wrapping 3rd-party SDKs.

⸻

13. Performance & Data
	•	Avoid unnecessary use client; each client boundary increases JS sent.
	•	Use streaming / Suspense where appropriate rather than giant client trees.
	•	Use select queries and shape data close to where it’s fetched.
	•	Memoize expensive calculations in client components (useMemo, useCallback) only when profiling shows a need.

⸻

14. Testing & Confidence
	•	Prefer unit tests for pure functions (mappers, validators, formatters).
	•	Lightweight component tests for critical components (forms, complex widgets).
	•	Keep test files next to source when possible (component.test.tsx).

⸻

15. Code Review Checklist

Before merging:
	•	Is page.tsx thin (data + composition only)?
	•	Are interactive parts isolated in small client components?
	•	Is logic in hooks / helpers rather than in JSX?
	•	Are types explicit and narrow (no any / unknown leaking into UI)?
	•	Are errors, loading, and empty states explicitly handled?
	•	Is new shared functionality placed under src/components / src/lib (not duplicated)?

If the answer is “no” to more than one of these, refactor before shipping.

⸻


