"""book -> book-service

Revision ID: 772d18a025a7
Revises: 3269d92ca432
Create Date: 2026-11-11 14:51:47.535356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '772d18a025a7'
down_revision: Union[str, Sequence[str], None] = '3269d92ca432'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


book_status_enum = postgresql.ENUM(
    'PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED',
    name='book_status',
    create_type=False,  # создадим вручную ниже
)

book_source_enum = postgresql.ENUM(
    'WEBSITE', 'PHONE', 'BOT', 'WALK_IN',
    name='book_source',
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Сначала типы
    book_status_enum.create(op.get_bind(), checkfirst=True)
    book_source_enum.create(op.get_bind(), checkfirst=True)

    # 2. Таблица book_service
    op.create_table(
        'book_service',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=True),
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('price_at_booking', sa.Numeric(
            precision=10, scale=2), nullable=False),
        sa.Column('is_deleted', sa.Boolean(),
                  server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('who_create', sa.Integer(), nullable=False),
        sa.Column('who_update', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['book_id'], ['book.book_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['master_id'], ['user.user_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(
            ['service_id'], ['service.service_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('book_id', 'service_id',
                            'master_id', name='uq_book_service'),
    )
    op.create_index(op.f('ix_book_service_book_id'),
                    'book_service', ['book_id'], unique=False)
    op.create_index(op.f('ix_book_service_service_id'),
                    'book_service', ['service_id'], unique=False)

    # 3. Новые колонки в book
    #    ВАЖНО: default — 'PENDING' (имя), т.к. Enum без values_callable хранит .name
    op.add_column(
        'book',
        sa.Column(
            'status',
            book_status_enum,
            server_default='PENDING',
            nullable=False,
        ),
    )
    op.add_column('book', sa.Column('source', book_source_enum, nullable=True))
    op.add_column('book', sa.Column('pet_id', sa.Integer(), nullable=True))
    op.add_column('book', sa.Column('master_id', sa.Integer(), nullable=True))
    op.add_column('book', sa.Column('client_id', sa.Integer(), nullable=True))
    op.add_column('book', sa.Column('options', postgresql.JSONB(
        astext_type=sa.Text()), nullable=True))
    op.add_column('book', sa.Column('confirmed_at',
                  sa.DateTime(timezone=True), nullable=True))
    op.add_column('book', sa.Column('completed_at',
                  sa.DateTime(timezone=True), nullable=True))
    op.add_column('book', sa.Column('cancelled_at',
                  sa.DateTime(timezone=True), nullable=True))
    op.add_column('book', sa.Column(
        'cancelled_reason', sa.Text(), nullable=True))

    # 4. date/time -> NOT NULL (если в таблице есть NULL, миграция упадёт — см. ниже)
    op.alter_column('book', 'date', existing_type=sa.DATE(), nullable=False)
    op.alter_column(
        'book', 'time', existing_type=postgresql.TIME(), nullable=False)

    # 5. Индексы
    op.create_index('ix_book_master_date_time', 'book', [
                    'master_id', 'date', 'time'], unique=False)
    op.create_index(op.f('ix_book_status'), 'book', ['status'], unique=False)
    op.create_index('ix_book_status_date', 'book', [
                    'status', 'date'], unique=False)

    # 6. Дропаем старые FK (по колонкам master/service/pet)
    op.drop_constraint('book_master_fkey', 'book', type_='foreignkey')
    op.drop_constraint('book_service_fkey', 'book', type_='foreignkey')
    op.drop_constraint('book_pet_fkey', 'book', type_='foreignkey')

    # 7. Создаём новые FK с именами (обязательно! иначе downgrade упадёт)
    op.create_foreign_key('book_pet_id_fkey', 'book',
                          'pet', ['pet_id'], ['pet_id'])
    op.create_foreign_key('book_master_id_fkey', 'book',
                          'user', ['master_id'], ['user_id'])
    op.create_foreign_key('book_client_id_fkey', 'book',
                          'user', ['client_id'], ['user_id'])

    # 8. Удаляем старые колонки (FK уже сняты)
    op.drop_column('book', 'service')
    op.drop_column('book', 'master')
    op.drop_column('book', 'pet')


def downgrade() -> None:
    """Downgrade schema."""

    # 1. Возвращаем старые колонки
    op.add_column('book', sa.Column('pet', sa.INTEGER(),
                  autoincrement=False, nullable=True))
    op.add_column('book', sa.Column('master', sa.INTEGER(),
                  autoincrement=False, nullable=True))
    op.add_column('book', sa.Column('service', sa.INTEGER(),
                  autoincrement=False, nullable=True))

    # 2. Дропаем новые FK (по именам)
    op.drop_constraint('book_client_id_fkey', 'book', type_='foreignkey')
    op.drop_constraint('book_master_id_fkey', 'book', type_='foreignkey')
    op.drop_constraint('book_pet_id_fkey', 'book', type_='foreignkey')

    # 3. Восстанавливаем старые FK
    op.create_foreign_key('book_pet_fkey', 'book', 'pet', ['pet'], ['pet_id'])
    op.create_foreign_key('book_service_fkey', 'book',
                          'service', ['service'], ['service_id'])
    op.create_foreign_key('book_master_fkey', 'book',
                          'user', ['master'], ['user_id'])

    # 4. Индексы
    op.drop_index('ix_book_status_date', table_name='book')
    op.drop_index(op.f('ix_book_status'), table_name='book')
    op.drop_index('ix_book_master_date_time', table_name='book')

    # 5. date/time обратно в nullable
    op.alter_column(
        'book', 'time', existing_type=postgresql.TIME(), nullable=True)
    op.alter_column('book', 'date', existing_type=sa.DATE(), nullable=True)

    # 6. Дропаем новые колонки
    op.drop_column('book', 'cancelled_reason')
    op.drop_column('book', 'cancelled_at')
    op.drop_column('book', 'completed_at')
    op.drop_column('book', 'confirmed_at')
    op.drop_column('book', 'options')
    op.drop_column('book', 'client_id')
    op.drop_column('book', 'master_id')
    op.drop_column('book', 'pet_id')
    op.drop_column('book', 'source')
    op.drop_column('book', 'status')

    # 7. book_service
    op.drop_index(op.f('ix_book_service_service_id'),
                  table_name='book_service')
    op.drop_index(op.f('ix_book_service_book_id'), table_name='book_service')
    op.drop_table('book_service')

    # 8. Типы — в конце
    book_source_enum.drop(op.get_bind(), checkfirst=True)
    book_status_enum.drop(op.get_bind(), checkfirst=True)
