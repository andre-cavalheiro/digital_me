# Pydantic v2 / SQLModel 0.0.27 Migration Notes

## Phase 3 Worklog
- Updated `pyproject.toml` to pin `pydantic>=2.11`, `sqlmodel>=0.0.27`, and added `pydantic-settings` dependency (lockfile already reflects the Poetry add that was executed outside Codex).
- Migrated `src/fury_api/lib/settings.py` to `pydantic-settings.BaseSettings`, replaced legacy `Config` usage with `model_config`, and converted `@root_validator` call sites to `@model_validator`.
- Refactored `src/fury_api/lib/db/base.py` for Pydantic v2 compatibility: introduced `ConfigDict`, replaced `.dict()` usage with `.model_dump()`, and switched all `__fields__` access to `model_fields`.
- Updated string constraint helpers in `lib/db/base.py` to use Pydantic v2's `pattern=` keyword (replaces deprecated `regex=`).
- Replaced deprecated `sqlmodel.sql.sqltypes.AutoString()` usages across every Alembic migration with `sa.String()` to ensure forward compatibility with SQLModel 0.0.27.
- Updated filter utilities (`lib/model_filters/definitions.py`) to read aliases via `model_fields` and corrected an alias mapping bug exposed during the refactor.
- Normalized optional settings fields to supply explicit `None` defaults so Pydantic v2 treats them as optional (fixes missing-env startup failures).
- Removed legacy `json_loads/json_dumps` overrides from `BaseSQLModel.model_config`; Pydantic v2 no longer honors those settings.
- Swapped relationship annotations to SQLAlchemy 2.0 `Mapped[...]` typing in `domain/organizations/models.py` and `domain/users/models.py` to satisfy SQLModel 0.0.27.
- Detached `OrganizationRead` from the table model (`Organization`) so response schemas inherit from the non-table base instead of dragging SQLAlchemy relationship metadata into Pydantic models.
- Taught `lib/model_filters.get_default_ops_for_type` to normalize Annotated/Union-constrained types via `typing.get_origin`, preventing runtime `issubclass` crashes when controllers pass constrained aliases like `Identifier` or optional variants.
- Removed duplicate Alembic revision files (duplicate revision IDs triggered multi-head errors); keep a single canonical file per revision under `lib/db/migrations/versions/`.
- Relaxed `BigIntIDModel.id` to allow `None` prior to flush so autoincremented keys can be generated without validation errors during create flows.
- Added `BaseSQLModel.from_model()` helper so service/controller layers can convert create payloads into persistent models without manual dumping while preserving validation (falls back to `model_construct` to avoid primary-key requirements during inserts).

## Current Status
- `poetry run python -m fury_api` now fails earlier because `pydantic_settings` is not installed in the sandbox; network-restricted environment blocked `poetry add pydantic-settings@^2.5`.
- All code paths that previously relied on Pydantic v1 interfaces inside the API package have been lifted to v2 equivalents.
- Database migration scripts no longer depend on the removed `AutoString` helper.

## Required Follow-up
1. Run `poetry add pydantic-settings@^2.5` (or `poetry install`) in a network-enabled shell to materialize the new dependency.
2. Re-run the application (`poetry run python -m fury_api`) and smoke tests once the dependency is available.
3. Audit remaining modules for deprecated APIs during runtime testing; patch any additional `.dict()`/`.parse_raw()` regressions that surface.
