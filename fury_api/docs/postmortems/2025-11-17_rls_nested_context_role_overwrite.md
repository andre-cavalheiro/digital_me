# Postmortem: Row-Level Security Permission Denied on Citation Table

**Date:** November 17, 2025
**Severity:** Critical
**Status:** Resolved
**Author:** Engineering Team

---

## Executive Summary

A critical permissions error (`permission denied for table citation`) prevented INSERT operations on the newly created `citation` table despite having a working PostgreSQL Row-Level Security (RLS) setup. After extensive investigation involving multiple fix attempts, the root cause was identified as **nested UnitOfWork contexts overwriting database roles on shared connections**.

**Impact:** All citation creation operations failed with permission denied errors.
**Duration:** ~4 hours of investigation and debugging.
**Root Cause:** Nested dependency injection with different read_only flags caused role thrashing on shared database connections.

---

## Impact

### User-Facing Impact
- **Citation creation completely broken**: All POST requests to `/citations` endpoint returned 500 errors
- **Data integrity concerns**: Users unable to link content sources to documents

### Technical Impact
- Exposed fundamental architectural issue with nested UnitOfWork patterns
- Revealed gap in understanding of SQLAlchemy session connection pooling behavior
- Demonstrated that RLS role switching is connection-based, not session-based

---

## Root Cause Analysis

### The Problem

The `create_citation` endpoint had **two service dependencies** that both required database access with **different security contexts**:

```python
@router.post("/")
async def create_citation(
    citation_service: CitationService = Depends(get_citation_service),  # read_only=False → tenant_user
    content_service: ContentService = Depends(get_content_service),      # read_only=True → tenant_user_ro
    ...
):
    # Both services use the SAME underlying database connection!
```

### What Was Happening

1. **First context** (`citation_service`):
   - Calls `uow.with_organization(org_id, read_only=False)`
   - Sets `_context_depth = 1`
   - Calls `post_begin_session_hook()`
   - Executes `SET ROLE tenant_user` on connection (pid=267)

2. **Nested context** (`content_service`):
   - Calls `uow.with_organization(org_id, read_only=True)` **on the same UoW instance**
   - Increments `_context_depth = 2`
   - Calls `post_begin_session_hook()` **again**
   - Executes `SET ROLE tenant_user_ro` **overwriting the previous role**

3. **INSERT operation**:
   - Attempts to insert citation with `tenant_user_ro` role (read-only!)
   - PostgreSQL RLS policy rejects: "permission denied for table citation"

### Why This Wasn't Caught Earlier

- Other tables worked because they didn't have this specific nested dependency pattern
- Connection pooling masked the issue - same connection was reused
- The `_context_depth` counter existed but wasn't being checked in `post_begin_session_hook()`

---

## Timeline of Investigation

### Attempt 1: Migration Pattern Analysis
**Hypothesis:** New migration used wrong schema references
**Action:** Analyzed the citation migration file
**Finding:** Migration explicitly specified `schema="platform"` instead of relying on `search_path`
**Fix Attempted:**
- Removed all `schema="platform"` parameters from table definitions
- Removed `platform.` prefixes from foreign key references
**Result:** ❌ Failed - Same error persisted

### Attempt 2: RLS Policy Missing WITH CHECK
**Hypothesis:** RLS policies missing INSERT/UPDATE permissions
**Action:** Reviewed RLS policy definitions
**Finding:** Policies only had `USING` clause, missing `WITH CHECK` for mutations
**Fix Attempted:**
```sql
CREATE POLICY tenant_policy ON citation TO tenant_user
    USING (organization_id = current_setting('app.current_organization_id')::bigint)
    WITH CHECK (organization_id = current_setting('app.current_organization_id')::bigint);
```
**Result:** ❌ Failed - Same error persisted

### Attempt 3: Missing Role Permissions
**Hypothesis:** `tenant_user` role lacks permissions on new tables
**Action:** Added explicit permission grants to migration
**Fix Attempted:**
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform TO tenant_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA platform TO tenant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA platform GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tenant_user;
```
**Result:** ❌ Failed - Same error persisted

### Attempt 4: Role Membership Missing
**Hypothesis:** Database user can't `SET ROLE tenant_user` due to missing role membership
**Action:** Updated genesis RLS migration to grant roles to current user
**Fix Attempted:**
```sql
-- In genesis migration
EXECUTE 'GRANT tenant_user TO ' || current_user;
EXECUTE 'GRANT tenant_user_ro TO ' || current_user;
```
**Result:** ❌ Failed - User was frustrated: "Purged the database, re-created it, re-ran all migrations. Still the same bullshit error."

### Attempt 5: Premature Hook Execution
**Hypothesis:** `post_begin_session_hook()` called before `organization_id` set
**Action:** Traced code flow in `UnitOfWork.__aenter__()`
**Finding:** `post_begin_session_hook()` was incorrectly called in `_begin_new_session()` before organization context was established
**Fix Attempted:**
```python
async def _begin_new_session(self):
    self.session = self._session_factory()
    # REMOVED: await self.post_begin_session_hook()  ← Hook called too early!
    return self.session
```
**Result:** ❌ Failed - User: "I don't understand how this can possibly be true, but i continue to get the exact same error. WHAT IS GOING ON?"

### Attempt 6: Debug Logging (Breakthrough)
**Hypothesis:** Need to trace exact role state at time of INSERT
**Action:** Added comprehensive logging to track role changes and connection PIDs
**Logging Added:**
```python
# In post_begin_session_hook()
logger.info(f"🔍 post_begin_session_hook: org_id={self.organization_id}, enabled={...}, read_only={self.read_only}")
logger.info(f"✅ Setting role to: {role}")
result = await self.session.exec(text("SELECT current_role, pg_backend_pid()"))
current_role, backend_pid = result.one()
logger.info(f"✅ Verified: current_role = {current_role}, backend_pid = {backend_pid}")

# In generic_sql.py add()
result = await session.exec(text("SELECT current_role, pg_backend_pid()"))
role_before_flush, pid = result.one()
logger.info(f"🚨 RIGHT BEFORE FLUSH: role={role_before_flush}, pid={pid}, table={self._model_cls.__tablename__}")
```

**Result:** ✅ **ROOT CAUSE IDENTIFIED!**

**Debug Output Revealed:**
```
17:08:17,025 | ✅ Setting role to: tenant_user (pid=267)           ← First context
17:08:17,029 | ✅ Verified: current_role = tenant_user, backend_pid = 267

17:08:17,029 | ✅ Setting role to: tenant_user_ro (pid=267)        ← NESTED CONTEXT OVERWRITES!
17:08:17,031 | ✅ Verified: current_role = tenant_user_ro, backend_pid = 267

17:08:17,033 | 🚨 RIGHT BEFORE FLUSH: role=tenant_user_ro, pid=267 ← WRONG ROLE!
```

**Key Insight:** Both contexts used the **same connection** (pid=267) but the nested context overwrote the role!

---

## Resolution

### The Fix

Added a check in `post_begin_session_hook()` to **skip role setting in nested contexts**:

```python
async def post_begin_session_hook(self) -> None:
    """This method is called after creating a new session."""
    import logging
    logger = logging.getLogger(__name__)

    # Skip if we're in a nested context - don't override the parent's role!
    if self._context_depth > 1:
        logger.info(f"🔍 post_begin_session_hook: SKIPPING (nested context depth={self._context_depth})")
        return

    logger.info(f"🔍 post_begin_session_hook: org_id={self.organization_id}, enabled={config.database.TENANT_ROLE_ENABLED}, read_only={self.read_only}")

    if config.database.TENANT_ROLE_ENABLED and self.organization_id is not None:
        # ... existing role setup code ...
```

### Why This Works

1. The `_context_depth` counter tracks nested `with_organization` contexts
2. Only the **outermost context** (depth=1) sets the database role
3. **Inner contexts** (depth>1) skip role setup entirely, preserving the parent's role
4. When the inner context exits, the outer context's role remains active
5. INSERT operations execute with the correct role from the outermost context

---

## Files Modified

### 1. `fury_api/src/fury_api/lib/unit_of_work.py`

**Location:** `post_begin_session_hook()` method in `UnitOfWork` class

**Change:**
```python
async def post_begin_session_hook(self) -> None:
    """This method is called after creating a new session."""
    import logging
    logger = logging.getLogger(__name__)

    # ✅ ADD THIS CHECK AT THE START
    # Skip if we're in a nested context - don't override the parent's role!
    if self._context_depth > 1:
        logger.info(f"🔍 post_begin_session_hook: SKIPPING (nested context depth={self._context_depth})")
        return

    # ... rest of existing code unchanged ...
```

**Also in same file** (earlier fix):
```python
async def _begin_new_session(self):
    self.session = self._session_factory()
    # ✅ REMOVED: await self.post_begin_session_hook()  ← Don't call here!
    # Note: post_begin_session_hook is called in with_organization after organization_id is set
    return self.session
```

### 2. `fury_api/src/fury_api/lib/db/migrations/versions/2025-01-29_genesis_5_rls_d0cbcbb4b236.py`

**Location:** `schema_upgrades()` function, in role creation blocks

**Change:**
```python
# In tenant_user role creation
EXECUTE 'GRANT USAGE ON SCHEMA ' || current_schema || ' TO tenant_user';
EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ' || current_schema || ' TO tenant_user';
EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || current_schema || ' GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tenant_user';
EXECUTE 'GRANT USAGE ON ALL SEQUENCES IN SCHEMA ' || current_schema || ' TO tenant_user';
EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || current_schema || ' GRANT USAGE ON SEQUENCES TO tenant_user';

# ✅ ADD THIS LINE
EXECUTE 'GRANT tenant_user TO ' || current_user;

# In tenant_user_ro role creation
EXECUTE 'GRANT USAGE ON SCHEMA ' || current_schema || ' TO tenant_user_ro';
EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA ' || current_schema || ' TO tenant_user_ro';
EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || current_schema || ' GRANT SELECT ON TABLES TO tenant_user_ro';
EXECUTE 'GRANT USAGE ON ALL SEQUENCES IN SCHEMA ' || current_schema || ' TO tenant_user_ro';
EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA ' || current_schema || ' GRANT USAGE ON SEQUENCES TO tenant_user_ro';

# ✅ ADD THIS LINE
EXECUTE 'GRANT tenant_user_ro TO ' || current_user;
```

### 3. `fury_api/src/fury_api/lib/db/migrations/versions/2025-11-17_add_schemas_for_domains_documents_sources_conversations_7485721da8b9.py`

**Multiple Changes:**

#### A. Add Permission Grants at Start
```python
def schema_upgrades() -> None:
    """Schema upgrade migrations."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)

        # ✅ ADD THIS BLOCK BEFORE TABLE CREATION
        # Grant permissions to tenant roles on new tables
        op.execute(
            """
            DO $$
            BEGIN
                -- Grant permissions to tenant_user
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform TO tenant_user;
                GRANT USAGE ON ALL SEQUENCES IN SCHEMA platform TO tenant_user;

                -- Grant read-only permissions to tenant_user_ro
                GRANT SELECT ON ALL TABLES IN SCHEMA platform TO tenant_user_ro;
                GRANT USAGE ON ALL SEQUENCES IN SCHEMA platform TO tenant_user_ro;

                -- Set default privileges for future tables
                ALTER DEFAULT PRIVILEGES IN SCHEMA platform GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tenant_user;
                ALTER DEFAULT PRIVILEGES IN SCHEMA platform GRANT USAGE ON SEQUENCES TO tenant_user;
                ALTER DEFAULT PRIVILEGES IN SCHEMA platform GRANT SELECT ON TABLES TO tenant_user_ro;
                ALTER DEFAULT PRIVILEGES IN SCHEMA platform GRANT USAGE ON SEQUENCES TO tenant_user_ro;
            END;
            $$ LANGUAGE plpgsql;
            """
        )

        # ... rest of migration ...
```

#### B. Remove Explicit Schema References
```python
# ❌ BEFORE (wrong pattern)
op.create_table(
    "document",
    sa.Column("id", sa.BigInteger(), nullable=False),
    # ...
    schema="platform"  # ← REMOVE THIS
)

# ✅ AFTER (correct pattern - relies on search_path)
op.create_table(
    "document",
    sa.Column("id", sa.BigInteger(), nullable=False),
    # ...
    # No schema parameter
)
```

#### C. Remove Schema Prefixes from Foreign Keys
```python
# ❌ BEFORE (wrong)
sa.ForeignKeyConstraint(
    ["organization_id"],
    ["platform.organization.id"],  # ← REMOVE platform. prefix
)

# ✅ AFTER (correct)
sa.ForeignKeyConstraint(
    ["organization_id"],
    ["organization.id"],  # ← Just table name
)
```

#### D. Add WITH CHECK to RLS Policies
```python
# ❌ BEFORE (incomplete)
CREATE POLICY tenant_policy ON citation TO tenant_user
    USING (organization_id = current_setting('app.current_organization_id')::bigint);

# ✅ AFTER (complete)
CREATE POLICY tenant_policy ON citation TO tenant_user
    USING (organization_id = current_setting('app.current_organization_id')::bigint)
    WITH CHECK (organization_id = current_setting('app.current_organization_id')::bigint);
```

### 4. `fury_api/src/fury_api/lib/repository/generic_sql.py`

**Temporary Debug Logging** (can be removed after verification):
```python
async def add(self, session: AsyncSession, record: T) -> T:
    import logging
    logger = logging.getLogger(__name__)

    session.add(record)

    # ⚠️ TEMPORARY: Debug logging (remove after fix verified)
    result = await session.exec(text("SELECT current_role, pg_backend_pid()"))
    role_before_flush, pid = result.one()
    logger.info(f"🚨 RIGHT BEFORE FLUSH: role={role_before_flush}, pid={pid}, table={self._model_cls.__tablename__}")

    await session.flush()
    await session.refresh(record)
    return record
```

---

## How to Replicate the Fix (Step-by-Step for AI Agent)

### Prerequisites
- PostgreSQL database with RLS enabled
- Alembic migrations setup
- SQLAlchemy async sessions with connection pooling
- Multi-tenant architecture using `SET ROLE` for tenant isolation

### Step 1: Update Genesis RLS Migration

**File:** `lib/db/migrations/versions/*_genesis_5_rls_*.py`

Find the blocks that create `tenant_user` and `tenant_user_ro` roles and add role membership grants:

```python
# After creating tenant_user role and granting permissions
EXECUTE 'GRANT tenant_user TO ' || current_user;

# After creating tenant_user_ro role and granting permissions
EXECUTE 'GRANT tenant_user_ro TO ' || current_user;
```

### Step 2: Fix UnitOfWork Session Initialization

**File:** `lib/unit_of_work.py`

In the `_begin_new_session` method, remove any call to `post_begin_session_hook()`:

```python
async def _begin_new_session(self):
    self.session = self._session_factory()
    # DO NOT call post_begin_session_hook() here!
    # It will be called in with_organization() after organization_id is set
    return self.session
```

### Step 3: Add Nested Context Check

**File:** `lib/unit_of_work.py`

At the **very start** of `post_begin_session_hook()`, add this check:

```python
async def post_begin_session_hook(self) -> None:
    """This method is called after creating a new session."""
    import logging
    logger = logging.getLogger(__name__)

    # CRITICAL: Skip if we're in a nested context
    if self._context_depth > 1:
        logger.info(f"🔍 post_begin_session_hook: SKIPPING (nested context depth={self._context_depth})")
        return

    # ... rest of your existing role setup code ...
```

### Step 4: Fix New Domain Migrations

**File:** Any migration creating tables with RLS

**A. Add permission grants at the start:**
```python
def schema_upgrades() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)

        # Grant permissions to tenant roles
        op.execute(
            """
            DO $$
            BEGIN
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {your_schema} TO tenant_user;
                GRANT USAGE ON ALL SEQUENCES IN SCHEMA {your_schema} TO tenant_user;
                GRANT SELECT ON ALL TABLES IN SCHEMA {your_schema} TO tenant_user_ro;
                GRANT USAGE ON ALL SEQUENCES IN SCHEMA {your_schema} TO tenant_user_ro;

                ALTER DEFAULT PRIVILEGES IN SCHEMA {your_schema} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tenant_user;
                ALTER DEFAULT PRIVILEGES IN SCHEMA {your_schema} GRANT USAGE ON SEQUENCES TO tenant_user;
                ALTER DEFAULT PRIVILEGES IN SCHEMA {your_schema} GRANT SELECT ON TABLES TO tenant_user_ro;
                ALTER DEFAULT PRIVILEGES IN SCHEMA {your_schema} GRANT USAGE ON SEQUENCES TO tenant_user_ro;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
```

**B. Remove explicit schema parameters:**
```python
# DON'T do this:
op.create_table("my_table", ..., schema="my_schema")

# DO this instead (rely on search_path):
op.create_table("my_table", ...)
```

**C. Remove schema prefixes from foreign keys:**
```python
# DON'T do this:
sa.ForeignKeyConstraint(["org_id"], ["my_schema.organization.id"])

# DO this instead:
sa.ForeignKeyConstraint(["org_id"], ["organization.id"])
```

**D. Add WITH CHECK to RLS policies:**
```python
CREATE POLICY tenant_policy ON my_table TO tenant_user
    USING (organization_id = current_setting('app.current_organization_id')::bigint)
    WITH CHECK (organization_id = current_setting('app.current_organization_id')::bigint);

CREATE POLICY tenant_policy_ro ON my_table TO tenant_user_ro
    USING (organization_id = current_setting('app.current_organization_id')::bigint)
    WITH CHECK (organization_id = current_setting('app.current_organization_id')::bigint);
```

### Step 5: Testing

After applying fixes:

1. **Drop and recreate database:**
   ```bash
   dropdb your_database
   createdb your_database
   ```

2. **Run all migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Verify role membership:**
   ```sql
   SELECT r.rolname, m.rolname as member
   FROM pg_roles r
   JOIN pg_auth_members am ON r.oid = am.roleid
   JOIN pg_roles m ON am.member = m.oid
   WHERE r.rolname IN ('tenant_user', 'tenant_user_ro');
   ```

   Should show current database user as member of both roles.

4. **Test the endpoint** that was failing (e.g., create citation)

5. **Check logs** for nested context behavior:
   ```
   ✅ Setting role to: tenant_user (depth=1)
   🔍 SKIPPING (nested context depth=2)  ← Inner context skipped!
   🚨 RIGHT BEFORE FLUSH: role=tenant_user ← Correct role!
   ```

---

## Prevention and Lessons Learned

### Architectural Lessons

1. **Nested contexts are dangerous with stateful connections**
   - SQLAlchemy connection pooling means nested contexts share connections
   - Any connection-level state (like `SET ROLE`) affects ALL contexts on that connection
   - Solution: Guard state-changing operations in nested contexts

2. **Dependency injection patterns must consider context depth**
   - Multiple service dependencies in FastAPI endpoints can create nested contexts
   - Always check `_context_depth` or similar counters before modifying shared state

3. **Debug logging is invaluable for connection pooling issues**
   - Log backend PID to track which connection is being used
   - Log role changes with timestamps to see overwriting behavior
   - Add pre-operation logging (e.g., before `flush()`) to catch state issues

### Code Review Checklist

When adding new domains with RLS:

- [ ] Migration uses `search_path` instead of explicit `schema=` parameters
- [ ] Foreign keys don't have schema prefixes
- [ ] RLS policies include both `USING` and `WITH CHECK` clauses
- [ ] Permission grants added for both `tenant_user` and `tenant_user_ro`
- [ ] Default privileges set for future tables
- [ ] Test with endpoint that has multiple service dependencies
- [ ] Verify logs show only one role setting per request

### Testing Strategy

1. **Unit tests** should mock UnitOfWork to avoid connection sharing
2. **Integration tests** should explicitly test nested contexts:
   ```python
   async def test_nested_context_preserves_role():
       async with uow.with_organization(org_id, read_only=False) as outer:
           # Outer should set tenant_user
           async with uow.with_organization(org_id, read_only=True) as inner:
               # Inner should NOT change role
               pass
           # Role should still be tenant_user here
   ```
3. **E2E tests** should test endpoints with multiple service dependencies

---

## Diagnostic Queries for Future Debugging

### Check Current Role and Connection
```sql
SELECT current_role, pg_backend_pid();
```

### Check Role Membership
```sql
SELECT r.rolname, m.rolname as member
FROM pg_roles r
JOIN pg_auth_members am ON r.oid = am.roleid
JOIN pg_roles m ON am.member = m.oid
WHERE r.rolname IN ('tenant_user', 'tenant_user_ro');
```

### Check Table Permissions
```sql
SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_name = 'citation'
  AND grantee IN ('tenant_user', 'tenant_user_ro');
```

### Check RLS Policies
```sql
SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'citation';
```

### Check Active Connections and Roles
```sql
SELECT pid, usename, application_name, current_setting('role', true) as role
FROM pg_stat_activity
WHERE application_name = 'your_app_name';
```

### Simulate Role Setting
```sql
-- Test if role switch works
SET ROLE tenant_user;
SET app.current_organization_id = 1;
INSERT INTO citation (...) VALUES (...);  -- Should succeed
RESET ROLE;
```

---

## Related Issues

- None (first occurrence of this pattern)

## Follow-Up Actions

- [ ] Remove debug logging from `unit_of_work.py` after verification
- [ ] Remove debug logging from `generic_sql.py` after verification
- [ ] Add integration test for nested context role preservation
- [ ] Document nested context anti-pattern in architecture docs
- [ ] Consider linting rule or static analysis to detect nested context issues
- [ ] Review all other endpoints for similar nested dependency patterns

---

## References

- PostgreSQL RLS Documentation: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- SQLAlchemy Connection Pooling: https://docs.sqlalchemy.org/en/latest/core/pooling.html
- FastAPI Dependency Injection: https://fastapi.tiangolo.com/tutorial/dependencies/

---

**Postmortem Status:** Complete
**Follow-Up Owner:** Engineering Team
**Next Review Date:** After verification in production
