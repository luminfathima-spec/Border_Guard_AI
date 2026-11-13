"""add_phase7_report_fields

Revision ID: 8c9d0e1f2a3b
Revises: 7a8b9c0d1e2f
Create Date: 2026-09-28 21:15:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '8c9d0e1f2a3b'
down_revision: Union[str, None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = insp.get_table_names()

    if 'reports' in existing_tables:
        existing_cols = [c['name'] for c in insp.get_columns('reports')]

        if 'review_status' not in existing_cols:
            op.add_column('reports', sa.Column('review_status', sa.String(length=50), nullable=False, server_default='DRAFT'))
            op.create_index(op.f('ix_reports_review_status'), 'reports', ['review_status'], unique=False)

        if 'approved_by_user_id' not in existing_cols:
            op.add_column('reports', sa.Column('approved_by_user_id', sa.Integer(), nullable=True))
            op.create_foreign_key('fk_reports_approved_by_user_id_users', 'reports', 'users', ['approved_by_user_id'], ['id'], ondelete='SET NULL')
            op.create_index(op.f('ix_reports_approved_by_user_id'), 'reports', ['approved_by_user_id'], unique=False)

        if 'approved_at' not in existing_cols:
            op.add_column('reports', sa.Column('approved_at', sa.DateTime(), nullable=True))

        if 'model_name' not in existing_cols:
            op.add_column('reports', sa.Column('model_name', sa.String(length=100), nullable=False, server_default='gemini-2.5-flash'))

        if 'prompt_version' not in existing_cols:
            op.add_column('reports', sa.Column('prompt_version', sa.String(length=50), nullable=False, server_default='2026.04.1'))

        if 'sections_json' not in existing_cols:
            op.add_column('reports', sa.Column('sections_json', sa.JSON(), nullable=False, server_default='{}'))

        if 'human_corrections' not in existing_cols:
            op.add_column('reports', sa.Column('human_corrections', sa.JSON(), nullable=False, server_default='[]'))

        if 'audit_history' not in existing_cols:
            op.add_column('reports', sa.Column('audit_history', sa.JSON(), nullable=False, server_default='[]'))


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = insp.get_table_names()

    if 'reports' in existing_tables:
        existing_cols = [c['name'] for c in insp.get_columns('reports')]

        if 'audit_history' in existing_cols:
            op.drop_column('reports', 'audit_history')
        if 'human_corrections' in existing_cols:
            op.drop_column('reports', 'human_corrections')
        if 'sections_json' in existing_cols:
            op.drop_column('reports', 'sections_json')
        if 'prompt_version' in existing_cols:
            op.drop_column('reports', 'prompt_version')
        if 'model_name' in existing_cols:
            op.drop_column('reports', 'model_name')
        if 'approved_at' in existing_cols:
            op.drop_column('reports', 'approved_at')
        if 'approved_by_user_id' in existing_cols:
            op.drop_index(op.f('ix_reports_approved_by_user_id'), table_name='reports')
            op.drop_constraint('fk_reports_approved_by_user_id_users', 'reports', type_='foreignkey')
            op.drop_column('reports', 'approved_by_user_id')
        if 'review_status' in existing_cols:
            op.drop_index(op.f('ix_reports_review_status'), table_name='reports')
            op.drop_column('reports', 'review_status')
