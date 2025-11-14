# Database & Migrations

Fury API has a tightly integrated data model using **SQLAlchemy**, which serves as both the **Object Relational Mapper (ORM)** and schema definition tool. This ensures that business logic and database interactions remain structured and scalable.

Database schema changes are managed using **Alembic**, which generates versioned migration scripts to evolve the database structure over time. Alembic tracks schema changes and allows for both **forward** and **rollback** operations, ensuring safe database modifications.

When modifying the data model (e.g., adding new tables or fields), generate a new migration script:
```bash
make m='describe your migration' db-create-migration
```
This will create a new migration file inside `src/fury_api/lib/db/migrations/versions/`, where you can customize the database changes if necessary.

Apply all pending migrations to bring the database schema up to date:
```bash
make db-migrate
```
This command ensures the schema reflects the latest changes defined in the migration scripts.

If a migration introduces an issue, you can revert the last migration:
```bash
make rollback
```
This will undo the most recent migration, restoring the previous state of the schema. Rollbacks are critical for avoiding disruptions when deploying database changes to production environments so when developing a new migration make sure the rollback logic is also sound.

## Understanding Alembic Under the Hood

Alembic operates through its **configuration file** (`alembic.ini`) and an **environment script** (`env.py`). When you run a `make db-...` command, it effectively invokes Alembic under the hood, applying migrations using the configured **FURY_DB_URL** as the database connection.
