"""merge heads

Revision ID: 4af19aaef1cc
Revises: 1a2b3c4d5e6f, a15b29a48457
Create Date: 2026-07-20 22:49:49.345496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4af19aaef1cc'
down_revision: Union[str, Sequence[str], None] = ('1a2b3c4d5e6f', 'a15b29a48457')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
