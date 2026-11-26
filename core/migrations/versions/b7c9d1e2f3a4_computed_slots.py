"""computed slots: booking start/end + booking_settings, drop slots

Revision ID: b7c9d1e2f3a4
Revises: 8477fe25dc4f
Create Date: 2026-11-23 18:00:00.000000

Переводит модель бронирования на «расчётные слоты»:
- удаляет материализованную таблицу ``slots``;
- переносит конкретное время в ``bookings`` (``start_time``/``end_time``);
- добавляет singleton-таблицу ``booking_settings`` с шагом сетки слотов.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7c9d1e2f3a4'
down_revision: Union[str, Sequence[str], None] = '8477fe25dc4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- 1. Таблица настроек (singleton) ------------------------------
    op.create_table(
        'booking_settings',
        sa.Column('booking_settings_id', sa.Integer(), nullable=False),
        sa.Column(
            'slot_interval_minutes', sa.Integer(),
            server_default='30', nullable=False,
        ),
        sa.Column('is_deleted', sa.Boolean(),
                  server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('who_create', sa.Integer(), nullable=False),
        sa.Column('who_update', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('booking_settings_id'),
    )
    op.execute(
        "INSERT INTO booking_settings "
        "(booking_settings_id, slot_interval_minutes, is_deleted, "
        " created_at, updated_at, who_create, who_update) "
        "VALUES (1, 30, false, now(), now(), 0, 0)"
    )

    # --- 2. bookings: время вместо slot_id ----------------------------
    op.add_column(
        'bookings',
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'bookings',
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    )
    # Переносим время из существующих слотов (если таблица ещё есть и там есть
    # данные). Для «сиротских» броней без слота подставляем now().
    op.execute(
        """
        UPDATE bookings b
        SET start_time = s.start_time,
            end_time = s.end_time
        FROM slots s
        WHERE b.slot_id = s.slot_id
        """
    )
    op.execute(
        "UPDATE bookings SET start_time = now(), end_time = now() "
        "WHERE start_time IS NULL"
    )
    op.alter_column('bookings', 'start_time', nullable=False)
    op.alter_column('bookings', 'end_time', nullable=False)

    op.drop_index('uq_bookings_active_slot', table_name='bookings')
    op.drop_index(op.f('ix_bookings_slot_id'), table_name='bookings')
    op.drop_column('bookings', 'slot_id')

    op.create_index(
        'ix_bookings_master_start',
        'bookings',
        ['master_id', 'start_time'],
        unique=False,
    )

    # --- 3. Удаляем материализованную таблицу слотов ------------------
    op.drop_table('slots')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Возвращаем таблицу slots (enum slot_status оставляем в БД).
    slot_status = postgresql.ENUM(
        'FREE', 'BOOKED', 'BLOCKED',
        name='slot_status', create_type=False,
    )
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'slot_status') "
        "THEN CREATE TYPE slot_status AS ENUM ('FREE','BOOKED','BLOCKED'); "
        "END IF; END $$;"
    )
    op.create_table(
        'slots',
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', slot_status, server_default='FREE', nullable=False),
        sa.Column('is_deleted', sa.Boolean(),
                  server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('who_create', sa.Integer(), nullable=False),
        sa.Column('who_update', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['master_id'], ['user.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['service_id'], ['service.service_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('slot_id'),
        sa.UniqueConstraint(
            'master_id', 'service_id', 'start_time',
            name='uq_slots_master_service_start'),
    )
    op.create_index(op.f('ix_slots_master_id'), 'slots',
                    ['master_id'], unique=False)
    op.create_index('ix_slots_master_start', 'slots',
                    ['master_id', 'start_time'], unique=False)
    op.create_index(op.f('ix_slots_service_id'), 'slots',
                    ['service_id'], unique=False)
    op.create_index(op.f('ix_slots_status'), 'slots',
                    ['status'], unique=False)

    # 2. Возвращаем slot_id в bookings, восстанавливая слоты из броней.
    op.add_column(
        'bookings',
        sa.Column('slot_id', sa.Integer(), nullable=True),
    )
    op.execute(
        """
        INSERT INTO slots
            (master_id, service_id, start_time, end_time, status,
             is_deleted, created_at, updated_at, who_create, who_update)
        SELECT master_id, service_id, start_time, end_time, 'BOOKED',
               false, now(), now(), 0, 0
        FROM bookings
        """
    )
    op.execute(
        """
        UPDATE bookings b
        SET slot_id = s.slot_id
        FROM slots s
        WHERE s.master_id = b.master_id
          AND s.service_id = b.service_id
          AND s.start_time = b.start_time
        """
    )
    op.alter_column('bookings', 'slot_id', nullable=False)
    op.create_foreign_key(
        'bookings_slot_id_fkey', 'bookings', 'slots',
        ['slot_id'], ['slot_id'], ondelete='RESTRICT',
    )
    op.create_index(op.f('ix_bookings_slot_id'), 'bookings',
                    ['slot_id'], unique=False)
    op.create_index(
        'uq_bookings_active_slot', 'bookings', ['slot_id'], unique=True,
        postgresql_where=sa.text("status <> 'CANCELLED'"),
    )
    op.drop_index('ix_bookings_master_start', table_name='bookings')
    op.drop_column('bookings', 'end_time')
    op.drop_column('bookings', 'start_time')

    # 3. Убираем настройки.
    op.drop_table('booking_settings')
