"""completed booking status + service description

Revision ID: 9f1c2d3e4b5a
Revises: b7c9d1e2f3a4
Create Date: 2026-11-25 01:40:00.000000

Добавляет:
- значение ``COMPLETED`` в PostgreSQL-enum ``booking_status`` (визит выполнен);
- необязательное поле ``description`` у услуги.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9f1c2d3e4b5a'
down_revision: Union[str, Sequence[str], None] = 'b7c9d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'COMPLETED'")
    op.add_column(
        'service',
        sa.Column('description', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('service', 'description')
    # PostgreSQL не позволяет удалить значение из enum без пересоздания типа.
    # Оставляем COMPLETED в типе: это безопасно для данных и отката колонки.
