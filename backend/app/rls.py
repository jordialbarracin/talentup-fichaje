"""TalentUP Fichaje — Row Level Security helpers for PostgreSQL.

These utilities are no-ops on SQLite. They are intended for use inside
Alembic migrations to enable RLS and create tenant-isolation policies.
"""
from alembic import op


def enable_rls(table_name: str) -> None:
    """Enable Row Level Security on the given table."""
    op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")


def create_tenant_policy(table_name: str) -> None:
    """Create a tenant isolation policy on the given table.

    The policy compares the row's tenant_id column with the PostgreSQL
    session configuration variable `app.tenant_id`, which must be set by
    the application before issuing queries.
    """
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table_name} "
        f"USING (tenant_id = current_setting('app.tenant_id')::text)"
    )
