# Data Model

The project uses a relational database (PostgreSQL) to manage core entities. Here's an overview of the key tables that are configure out-of-the-box:

## Tables

### `organization`
- **Purpose**: Represents organizations (tenant grouping for multi-tenant support)
- **Key Fields**:
  - `id` (PK, BigInt, auto-increment)
  - `name` (string)
- **Relationships**:
  - One-to-many with `user` table (cascade delete on all related users)
  - One-to-many with `plugin` table

### `user`
- **Purpose**: Represents system users, each belonging to an organization
- **Key Fields**:
  - `id` (PK, BigInt, auto-increment)
  - `firebase_id` (string, for Firebase authentication)
  - `name` (string, min length 1)
  - `email` (string, unique, min length 1)
  - `organization_id` (FK to `organization.id`, required)
  - `status` (int, default: 1 ACTIVE - values: 1=ACTIVE, 2=INACTIVE, 3=DELETED)
  - `is_system` (boolean, default: false - for system-level users)
  - `active_token_id` (string, nullable - tracks current JWT token)
  - `date_joined` (timestamp with timezone, server default: now())
  - `last_login` (timestamp with timezone, nullable)
- **Relationships**:
  - Many-to-one with `organization` table (foreign key: `organization_id`, lazy joined)

### `plugin`
- **Purpose**: Represents integration plugins/data sources configured per organization
- **Key Fields**:
  - `id` (PK, BigInt, auto-increment)
  - `organization_id` (FK to `organization.id`, required)
  - `data_source` (string, required - identifies the type of plugin/integration)
  - `title` (string, required - display name)
  - `credentials` (JSON, required - stores authentication credentials)
  - `properties` (JSON, required - stores configuration properties)
  - `created_at` (timestamp, default: utcnow)
- **Relationships**:
  - Many-to-one with `organization` table (foreign key: `organization_id`)

## Data Relationships

```
                    organization (1)
                          │
              ┌───────────┴───────────┐
              │                       │
           (many)                  (many)
            user                   plugin
```

- Each **organization** can have multiple **users** and multiple **plugins**
- **Users** are cascade deleted when their organization is deleted
- **Plugins** store integration configurations (credentials and properties) specific to each organization

## Schema Management

Database schema changes are managed through **Alembic migrations**. For detailed information about creating, applying, and rolling back migrations, see the [Database and Migrations](./DATABASE_AND_MIGRATIONS.md) documentation.
