## Content filters and includes

This documents how the Content domain handles filters (including `collection_id`) and the `include=author` flag for both search and list endpoints.

### Key behavior
- `collection_id` filters are virtual: content is linked to collections through `content_collection`, so filtering must go through that junction table.
- Author hydration is opt-in via `include=author` and is handled by the Content repository/service without changing the API surface.
- The generic filter infrastructure (`model_filters`, `FiltersAndSortsParser`, `SqlFilterAdapter`) is reused; only the repository provides custom handling for the virtual filter.

### How filtering works now
- `GenericSqlExtendedRepository` exposes a hook `_apply_custom_filters(query, filters, combine_logic, filter_context)` that runs before the generic adapter.
- `ContentRepository` implements this hook to consume `collection_id` filters by building a subquery on `content_collection`, respecting `FilterCombineLogic` (`AND`/`OR`) and ops `eq`, `in`, `neq`, `not_in`.
- `filter_context` must carry `organization_id` so the subquery scopes to the tenant; if `collection_id` is used without it, the repository raises a clear error.
- Remaining filters (e.g., `author_id`, `published_at`) still go through the generic adapter unchanged.

### Service usage
- List endpoint (`GET /content`): `ContentsService.get_items_paginated` now passes `filter_context={"organization_id": self.organization_id}` into `list_with_pagination`, so `collection_id` works with pagination and includes.
- Search endpoint (`POST /content/search`): semantic search calls `ContentRepository.apply_filters_to_semantic_query`, which delegates to the same custom filter hook, keeping search and list consistent.
- Author inclusion: when `include=author`, the service bulk-loads authors for the page results and attaches them to `ContentRead`; no change to filters or pagination shape.

### Adding new virtual filters
1) Extend the domain repository’s `_apply_custom_filters` to consume the new filter and return the modified query plus any remaining filters.
2) Pass any needed context (e.g., `organization_id`) from the service via `filter_context`.
3) Reuse the same hook for semantic search or other custom queries to avoid duplication.
