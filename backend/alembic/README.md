# Alembic Migrations — TalentUP Fichaje

This directory contains database migration scripts managed by [Alembic](https://alembic.sqlalchemy.org/).

## Quick Start

```bash
# Activate virtual environment
source venv/Scripts/activate

# Run all pending migrations
alembic upgrade head

# Or use the convenience script
python run_migrations.py
```

## Creating a New Migration

After modifying a model in `app/models/`, generate a new migration:

```bash
# Autogenerate from model changes
alembic revision --autogenerate -m 'description_of_change'
```

This compares your current database schema against the SQLAlchemy model definitions
and generates a migration script in `alembic/versions/`.

**Always review the generated script** before applying it — autogenerate may miss
some changes (e.g., column renames, complex constraints).

## Applying Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to a specific revision
alembic upgrade <revision_id>

# Downgrade one step
alembic downgrade -1

# Downgrade to a specific revision
alembic downgrade <revision_id>

# View current revision and history
alembic current
alembic history
```

## Migration Strategy

- **Development (SQLite)**: `app/database.py` uses `create_all()` directly.
  Alembic migrations are still available for testing but not required.

- **Production (PostgreSQL)**: On startup, `init_db()` runs
  `alembic upgrade head` via subprocess. Always create a migration for
  production schema changes.

## File Structure

```
backend/
├── alembic/
│   ├── env.py              # Alembic environment config (imports all models)
│   ├── script.py.mako      # Migration script template
│   ├── README.md           # This file
│   └── versions/           # Generated migration scripts
│       └── 9b16fa110308_initial.py  # Initial migration (18 tables)
├── alembic.ini             # Alembic configuration
└── run_migrations.py       # Convenience script
```

## Notes

- The `env.py` automatically strips async driver prefixes (`sqlite+aiosqlite` → `sqlite`,
  `postgresql+asyncpg` → `postgresql`) so Alembic's sync engine works correctly.
- The `DATABASE_URL` environment variable overrides the URL in `alembic.ini`.
- Always run migrations from the `backend/` directory.
