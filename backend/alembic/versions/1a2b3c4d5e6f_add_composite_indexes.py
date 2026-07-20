"""add_composite_indexes

Revision ID: 1a2b3c4d5e6f
Revises: 9b16fa110308
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '9b16fa110308'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Índices compuestos para optimizar consultas de informes y listados.
    op.create_index('ix_clock_tenant_emp_time', 'clock_ins', ['tenant_id', 'employee_id', 'timestamp'])
    op.create_index('ix_schedule_tenant_date', 'schedules', ['tenant_id', 'date'])
    op.create_index('ix_incident_tenant_type', 'incidents', ['tenant_id', 'incident_type'])
    op.create_index('ix_overtime_tenant_date', 'overtime', ['tenant_id', 'date'])
    op.create_index('ix_leave_tenant_emp', 'leaves', ['tenant_id', 'employee_id'])
    op.create_index('ix_vacation_tenant_status', 'vacation_requests', ['tenant_id', 'status'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_vacation_tenant_status', table_name='vacation_requests')
    op.drop_index('ix_leave_tenant_emp', table_name='leaves')
    op.drop_index('ix_overtime_tenant_date', table_name='overtime')
    op.drop_index('ix_incident_tenant_type', table_name='incidents')
    op.drop_index('ix_schedule_tenant_date', table_name='schedules')
    op.drop_index('ix_clock_tenant_emp_time', table_name='clock_ins')
