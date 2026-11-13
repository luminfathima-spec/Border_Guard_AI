"""add_phase8_edge_and_sync_fields

Revision ID: 9d0e1f2a3b4c
Revises: 8c9d0e1f2a3b
Create Date: 2026-09-28 21:45:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '9d0e1f2a3b4c'
down_revision: Union[str, None] = '8c9d0e1f2a3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = insp.get_table_names()

    if 'security_events' in existing_tables:
        existing_cols = [c['name'] for c in insp.get_columns('security_events')]

        if 'client_event_id' not in existing_cols:
            op.add_column('security_events', sa.Column('client_event_id', sa.String(length=100), nullable=True))
            op.create_index(op.f('ix_security_events_client_event_id'), 'security_events', ['client_event_id'], unique=True)

        if 'sync_status' not in existing_cols:
            op.add_column('security_events', sa.Column('sync_status', sa.String(length=50), nullable=False, server_default='SYNCED'))
            op.create_index(op.f('ix_security_events_sync_status'), 'security_events', ['sync_status'], unique=False)

        if 'synced_at' not in existing_cols:
            op.add_column('security_events', sa.Column('synced_at', sa.DateTime(), nullable=True))

        if 'edge_node_id' not in existing_cols:
            op.add_column('security_events', sa.Column('edge_node_id', sa.String(length=100), nullable=True))
            op.create_index(op.f('ix_security_events_edge_node_id'), 'security_events', ['edge_node_id'], unique=False)

    if 'evidence' in existing_tables:
        existing_evidence_cols = [c['name'] for c in insp.get_columns('evidence')]

        if 'client_evidence_id' not in existing_evidence_cols:
            op.add_column('evidence', sa.Column('client_evidence_id', sa.String(length=100), nullable=True))
            op.create_index(op.f('ix_evidence_client_evidence_id'), 'evidence', ['client_evidence_id'], unique=True)

        if 'sync_status' not in existing_evidence_cols:
            op.add_column('evidence', sa.Column('sync_status', sa.String(length=50), nullable=False, server_default='SYNCED'))
            op.create_index(op.f('ix_evidence_sync_status'), 'evidence', ['sync_status'], unique=False)

        if 'synced_at' not in existing_evidence_cols:
            op.add_column('evidence', sa.Column('synced_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = insp.get_table_names()

    if 'evidence' in existing_tables:
        existing_evidence_cols = [c['name'] for c in insp.get_columns('evidence')]
        if 'synced_at' in existing_evidence_cols:
            op.drop_column('evidence', 'synced_at')
        if 'sync_status' in existing_evidence_cols:
            op.drop_index(op.f('ix_evidence_sync_status'), table_name='evidence')
            op.drop_column('evidence', 'sync_status')
        if 'client_evidence_id' in existing_evidence_cols:
            op.drop_index(op.f('ix_evidence_client_evidence_id'), table_name='evidence')
            op.drop_column('evidence', 'client_evidence_id')

    if 'security_events' in existing_tables:
        existing_cols = [c['name'] for c in insp.get_columns('security_events')]
        if 'edge_node_id' in existing_cols:
            op.drop_index(op.f('ix_security_events_edge_node_id'), table_name='security_events')
            op.drop_column('security_events', 'edge_node_id')
        if 'synced_at' in existing_cols:
            op.drop_column('security_events', 'synced_at')
        if 'sync_status' in existing_cols:
            op.drop_index(op.f('ix_security_events_sync_status'), table_name='security_events')
            op.drop_column('security_events', 'sync_status')
        if 'client_event_id' in existing_cols:
            op.drop_index(op.f('ix_security_events_client_event_id'), table_name='security_events')
            op.drop_column('security_events', 'client_event_id')
