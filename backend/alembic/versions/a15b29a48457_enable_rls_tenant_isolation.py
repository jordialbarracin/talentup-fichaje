"""enable_rls_tenant_isolation

Revision ID: a15b29a48457
Revises: 9b16fa110308
Create Date: 2026-07-20 20:03:42.469403

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a15b29a48457'
down_revision: Union[str, Sequence[str], None] = '9b16fa110308'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables with tenant_id column that must be isolated at the database level.
# These match the domain models that carry a non-null tenant_id.
RLS_TABLES = [
    "employees",
    "clock_ins",
    "shifts",
    "schedules",
    "vacation_requests",
    "leaves",
    "holidays",
    "overtime",
    "payroll",
    "notifications",
    "contracts",
    "incidents",
    "devices",
    "billing_records",
]


def _is_postgresql() -> bool:
    """Return True when the migration is running against PostgreSQL."""
    return "postgresql" in op.get_bind().dialect.name


def upgrade() -> None:
    """Enable RLS and create tenant isolation policies on PostgreSQL only."""
    if not _is_postgresql():
        return

    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING (tenant_id = current_setting('app.tenant_id')::text)"
        )


def downgrade() -> None:
    """Drop tenant isolation policies and disable RLS on PostgreSQL only."""
    if not _is_postgresql():
        return

    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
