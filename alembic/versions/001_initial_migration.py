from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = '001_initial_migration'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('employees', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False), sa.Column('name', sa.String(length=100), nullable=False), sa.Column('email', sa.String(length=150), nullable=False), sa.Column('department', sa.String(length=100), nullable=True), sa.Column('created_at', sa.DateTime(), nullable=True), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_employees_id'), 'employees', ['id'], unique=False)
    op.create_index(op.f('ix_employees_email'), 'employees', ['email'], unique=True)
    op.create_table('attendance_records', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False), sa.Column('employee_id', sa.Integer(), nullable=False), sa.Column('date', sa.Date(), nullable=False), sa.Column('check_in', sa.DateTime(), nullable=False), sa.Column('check_out', sa.DateTime(), nullable=True), sa.Column('status', sa.String(length=20), nullable=False), sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_attendance_records_id'), 'attendance_records', ['id'], unique=False)
    op.create_index(op.f('ix_attendance_records_employee_id'), 'attendance_records', ['employee_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_attendance_records_employee_id'), table_name='attendance_records')
    op.drop_index(op.f('ix_attendance_records_id'), table_name='attendance_records')
    op.drop_table('attendance_records')
    op.drop_index(op.f('ix_employees_email'), table_name='employees')
    op.drop_index(op.f('ix_employees_id'), table_name='employees')
    op.drop_table('employees')
