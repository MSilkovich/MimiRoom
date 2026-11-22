"""recources_delete

Revision ID: 8477fe25dc4f
Revises: e70c8ed62b73
Create Date: 2026-11-22 22:11:40.668021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8477fe25dc4f'
down_revision: Union[str, Sequence[str], None] = 'e70c8ed62b73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Сначала снимаем все FK, которые ссылаются на resources,
    #    иначе drop_table('resources') упадёт.
    op.drop_constraint(op.f('bookings_resource_id_fkey'),
                       'bookings', type_='foreignkey')
    op.drop_constraint(op.f('slots_resource_id_fkey'),
                       'slots', type_='foreignkey')
    op.drop_constraint(op.f('work_schedules_resource_id_fkey'),
                       'work_schedules', type_='foreignkey')

    # 2. Удаляем resource_services (она ссылается на resources)
    op.drop_table('resource_services')

    # 3. Теперь можно удалить resources
    op.drop_table('resources')

    # 4. Создаём master_services
    op.create_table('master_services',
                    sa.Column('master_id', sa.Integer(), nullable=False),
                    sa.Column('service_id', sa.Integer(), nullable=False),
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
                    sa.PrimaryKeyConstraint('master_id', 'service_id')
                    )

    # 5. bookings: добавляем новые колонки
    op.add_column('bookings', sa.Column(
        'master_id', sa.Integer(), nullable=False))
    op.add_column('bookings', sa.Column(
        'client_id', sa.Integer(), nullable=True))
    op.add_column('bookings', sa.Column('pet_id', sa.Integer(), nullable=True))
    op.add_column('bookings', sa.Column(
        'options', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.alter_column('bookings', 'client_name',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=True)
    op.alter_column('bookings', 'client_phone',
                    existing_type=sa.VARCHAR(length=32),
                    nullable=True)
    op.drop_index(op.f('ix_bookings_resource_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_resource_status'), table_name='bookings')
    op.create_index(op.f('ix_bookings_client_id'),
                    'bookings', ['client_id'], unique=False)
    op.create_index(op.f('ix_bookings_master_id'),
                    'bookings', ['master_id'], unique=False)
    op.create_index('ix_bookings_master_status', 'bookings',
                    ['master_id', 'status'], unique=False)
    op.create_index(op.f('ix_bookings_pet_id'),
                    'bookings', ['pet_id'], unique=False)
    op.create_foreign_key('bookings_client_id_fkey', 'bookings', 'user', [
                          'client_id'], ['user_id'], ondelete='SET NULL')
    op.create_foreign_key('bookings_master_id_fkey', 'bookings', 'user', [
                          'master_id'], ['user_id'], ondelete='RESTRICT')
    op.create_foreign_key('bookings_pet_id_fkey', 'bookings', 'pet', [
                          'pet_id'], ['pet_id'], ondelete='SET NULL')
    op.drop_column('bookings', 'resource_id')

    # 6. service
    op.drop_column('service', 'is_active')

    # 7. slots
    op.add_column('slots', sa.Column(
        'master_id', sa.Integer(), nullable=False))
    op.drop_index(op.f('ix_slots_resource_id'), table_name='slots')
    op.drop_index(op.f('ix_slots_resource_start'), table_name='slots')
    op.drop_constraint(op.f('uq_slots_resource_service_start'),
                       'slots', type_='unique')
    op.create_index(op.f('ix_slots_master_id'), 'slots',
                    ['master_id'], unique=False)
    op.create_index('ix_slots_master_start', 'slots', [
                    'master_id', 'start_time'], unique=False)
    op.create_unique_constraint('uq_slots_master_service_start', 'slots', [
                                'master_id', 'service_id', 'start_time'])
    op.create_foreign_key('slots_master_id_fkey', 'slots', 'user', [
                          'master_id'], ['user_id'], ondelete='CASCADE')
    op.drop_column('slots', 'resource_id')

    # 8. work_schedules
    op.add_column('work_schedules', sa.Column(
        'master_id', sa.Integer(), nullable=False))
    op.drop_index(op.f('ix_work_schedules_resource_id'),
                  table_name='work_schedules')
    op.drop_constraint(op.f('uq_work_schedules_resource_weekday'),
                       'work_schedules', type_='unique')
    op.create_index(op.f('ix_work_schedules_master_id'),
                    'work_schedules', ['master_id'], unique=False)
    op.create_unique_constraint(
        'uq_work_schedules_master_weekday', 'work_schedules', ['master_id', 'weekday'])
    op.create_foreign_key('work_schedules_master_id_fkey', 'work_schedules', 'user', [
                          'master_id'], ['user_id'], ondelete='CASCADE')
    op.drop_column('work_schedules', 'resource_id')


def downgrade() -> None:
    """Downgrade schema."""
    # work_schedules
    op.add_column('work_schedules', sa.Column(
        'resource_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint('work_schedules_master_id_fkey',
                       'work_schedules', type_='foreignkey')
    op.create_foreign_key(op.f('work_schedules_resource_id_fkey'), 'work_schedules', 'resources', [
                          'resource_id'], ['resource_id'], ondelete='CASCADE')
    op.drop_constraint('uq_work_schedules_master_weekday',
                       'work_schedules', type_='unique')
    op.drop_index(op.f('ix_work_schedules_master_id'),
                  table_name='work_schedules')
    op.create_unique_constraint(op.f(
        'uq_work_schedules_resource_weekday'), 'work_schedules', ['resource_id', 'weekday'])
    op.create_index(op.f('ix_work_schedules_resource_id'),
                    'work_schedules', ['resource_id'], unique=False)
    op.drop_column('work_schedules', 'master_id')

    # slots
    op.add_column('slots', sa.Column('resource_id', sa.INTEGER(),
                  autoincrement=False, nullable=False))
    op.drop_constraint('slots_master_id_fkey', 'slots', type_='foreignkey')
    op.create_foreign_key(op.f('slots_resource_id_fkey'), 'slots', 'resources', [
                          'resource_id'], ['resource_id'], ondelete='CASCADE')
    op.drop_constraint('uq_slots_master_service_start',
                       'slots', type_='unique')
    op.drop_index('ix_slots_master_start', table_name='slots')
    op.drop_index(op.f('ix_slots_master_id'), table_name='slots')
    op.create_unique_constraint(op.f('uq_slots_resource_service_start'), 'slots', [
                                'resource_id', 'service_id', 'start_time'])
    op.create_index(op.f('ix_slots_resource_start'), 'slots', [
                    'resource_id', 'start_time'], unique=False)
    op.create_index(op.f('ix_slots_resource_id'), 'slots',
                    ['resource_id'], unique=False)
    op.drop_column('slots', 'master_id')

    # service
    op.add_column('service', sa.Column('is_active', sa.BOOLEAN(
    ), server_default=sa.text('true'), autoincrement=False, nullable=False))

    # bookings
    op.add_column('bookings', sa.Column(
        'resource_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint('bookings_client_id_fkey',
                       'bookings', type_='foreignkey')
    op.drop_constraint('bookings_master_id_fkey',
                       'bookings', type_='foreignkey')
    op.drop_constraint('bookings_pet_id_fkey', 'bookings', type_='foreignkey')
    op.create_foreign_key(op.f('bookings_resource_id_fkey'), 'bookings', 'resources', [
                          'resource_id'], ['resource_id'], ondelete='RESTRICT')
    op.drop_index(op.f('ix_bookings_pet_id'), table_name='bookings')
    op.drop_index('ix_bookings_master_status', table_name='bookings')
    op.drop_index(op.f('ix_bookings_master_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_client_id'), table_name='bookings')
    op.create_index(op.f('ix_bookings_resource_status'), 'bookings', [
                    'resource_id', 'status'], unique=False)
    op.create_index(op.f('ix_bookings_resource_id'),
                    'bookings', ['resource_id'], unique=False)
    op.alter_column('bookings', 'client_phone',
                    existing_type=sa.VARCHAR(length=32),
                    nullable=False)
    op.alter_column('bookings', 'client_name',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=False)
    op.drop_column('bookings', 'options')
    op.drop_column('bookings', 'pet_id')
    op.drop_column('bookings', 'client_id')
    op.drop_column('bookings', 'master_id')

    # resource_services, resources
    op.create_table('resource_services',
                    sa.Column('resource_id', sa.INTEGER(),
                              autoincrement=False, nullable=False),
                    sa.Column('service_id', sa.INTEGER(),
                              autoincrement=False, nullable=False),
                    sa.ForeignKeyConstraint(['resource_id'], ['resources.resource_id'], name=op.f(
                        'resource_services_resource_id_fkey'), ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['service_id'], ['service.service_id'], name=op.f(
                        'resource_services_service_id_fkey'), ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint(
                        'resource_id', 'service_id', name=op.f('resource_services_pkey'))
                    )
    op.create_table('resources',
                    sa.Column('resource_id', sa.INTEGER(),
                              autoincrement=True, nullable=False),
                    sa.Column('title', sa.VARCHAR(length=255),
                              autoincrement=False, nullable=False),
                    sa.Column('description', sa.TEXT(),
                              autoincrement=False, nullable=True),
                    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text(
                        'true'), autoincrement=False, nullable=False),
                    sa.Column('organization_id', sa.INTEGER(),
                              autoincrement=False, nullable=True),
                    sa.Column('is_deleted', sa.BOOLEAN(), server_default=sa.text(
                        'false'), autoincrement=False, nullable=False),
                    sa.Column('created_at', postgresql.TIMESTAMP(),
                              autoincrement=False, nullable=False),
                    sa.Column('updated_at', postgresql.TIMESTAMP(),
                              autoincrement=False, nullable=False),
                    sa.Column('who_create', sa.INTEGER(),
                              autoincrement=False, nullable=False),
                    sa.Column('who_update', sa.INTEGER(),
                              autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint(
                        'resource_id', name=op.f('resources_pkey'))
                    )

    # master_services
    op.drop_table('master_services')
