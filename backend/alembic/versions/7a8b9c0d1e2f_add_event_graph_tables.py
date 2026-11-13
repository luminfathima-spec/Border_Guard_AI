"""add_event_graph_tables

Revision ID: 7a8b9c0d1e2f
Revises: 68a1f2e4b890
Create Date: 2026-09-28 20:30:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, None] = '68a1f2e4b890'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = insp.get_table_names()

    # 1. Create evidence_observations table
    if 'evidence_observations' not in existing_tables:
        op.create_table(
            'evidence_observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('observation_type', sa.String(length=50), nullable=False, server_default='DIRECT_FACT'),
        sa.Column('provenance_type', sa.String(length=50), nullable=False, server_default='DIRECT_OBSERVATION'),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source_system', sa.String(length=100), nullable=False, server_default='CCTV_CV'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('camera_id', sa.Integer(), nullable=True),
        sa.Column('video_id', sa.Integer(), nullable=True),
        sa.Column('frame_number', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('superseded_by_id', sa.Integer(), nullable=True),
        sa.Column('details_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['superseded_by_id'], ['evidence_observations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_evidence_observations_id'), 'evidence_observations', ['id'], unique=False)
        op.create_index(op.f('ix_evidence_observations_incident_id'), 'evidence_observations', ['incident_id'], unique=False)
        op.create_index(op.f('ix_evidence_observations_observation_type'), 'evidence_observations', ['observation_type'], unique=False)
        op.create_index(op.f('ix_evidence_observations_provenance_type'), 'evidence_observations', ['provenance_type'], unique=False)
        op.create_index(op.f('ix_evidence_observations_timestamp'), 'evidence_observations', ['timestamp'], unique=False)
        op.create_index(op.f('ix_evidence_observations_camera_id'), 'evidence_observations', ['camera_id'], unique=False)
        op.create_index(op.f('ix_evidence_observations_video_id'), 'evidence_observations', ['video_id'], unique=False)
        op.create_index(op.f('ix_evidence_observations_status'), 'evidence_observations', ['status'], unique=False)

    # 2. Create event_links table
    if 'event_links' not in existing_tables:
        op.create_table(
            'event_links',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('incident_id', sa.Integer(), nullable=False),
            sa.Column('source_node_type', sa.String(length=50), nullable=False),
            sa.Column('source_node_id', sa.Integer(), nullable=False),
            sa.Column('source_ref', sa.String(length=255), nullable=True),
            sa.Column('target_node_type', sa.String(length=50), nullable=False),
            sa.Column('target_node_id', sa.Integer(), nullable=False),
            sa.Column('target_ref', sa.String(length=255), nullable=True),
            sa.Column('relationship_type', sa.String(length=50), nullable=False),
            sa.Column('provenance_type', sa.String(length=50), nullable=False, server_default='DIRECT_OBSERVATION'),
            sa.Column('creation_reason', sa.Text(), nullable=False),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('source_timestamp', sa.DateTime(), nullable=True),
            sa.Column('target_timestamp', sa.DateTime(), nullable=True),
            sa.Column('valid_from', sa.DateTime(), nullable=False),
            sa.Column('valid_to', sa.DateTime(), nullable=True),
            sa.Column('is_conflict', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('conflict_details', sa.JSON(), nullable=False),
            sa.Column('is_missing_evidence', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('metadata_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_event_links_id'), 'event_links', ['id'], unique=False)
        op.create_index(op.f('ix_event_links_incident_id'), 'event_links', ['incident_id'], unique=False)
        op.create_index(op.f('ix_event_links_source_node_type'), 'event_links', ['source_node_type'], unique=False)
        op.create_index(op.f('ix_event_links_source_node_id'), 'event_links', ['source_node_id'], unique=False)
        op.create_index(op.f('ix_event_links_target_node_type'), 'event_links', ['target_node_type'], unique=False)
        op.create_index(op.f('ix_event_links_target_node_id'), 'event_links', ['target_node_id'], unique=False)
        op.create_index(op.f('ix_event_links_relationship_type'), 'event_links', ['relationship_type'], unique=False)
        op.create_index(op.f('ix_event_links_provenance_type'), 'event_links', ['provenance_type'], unique=False)
        op.create_index('ix_event_links_incident_source', 'event_links', ['incident_id', 'source_node_type', 'source_node_id'], unique=False)
        op.create_index('ix_event_links_incident_target', 'event_links', ['incident_id', 'target_node_type', 'target_node_id'], unique=False)
        op.create_index('ix_event_links_incident_rel', 'event_links', ['incident_id', 'relationship_type'], unique=False)



def downgrade() -> None:
    op.drop_index('ix_event_links_incident_rel', table_name='event_links')
    op.drop_index('ix_event_links_incident_target', table_name='event_links')
    op.drop_index('ix_event_links_incident_source', table_name='event_links')
    op.drop_index(op.f('ix_event_links_provenance_type'), table_name='event_links')
    op.drop_index(op.f('ix_event_links_relationship_type'), table_name='event_links')
    op.drop_index(op.f('ix_event_links_target_node_id'), table_name='event_links')
    op.drop_index(op.f('ix_event_links_target_node_type'), table_name='event_links')
    op.drop_index(op.f('ix_event_links_source_node_id'), table_name='event_links')
    op.drop_index(op.f('ix_event_links_source_node_type'), table_name='event_links')
    op.drop_index(op.f('ix_event_links_incident_id'), table_name='event_links')
    op.drop_index(op.f('ix_event_links_id'), table_name='event_links')
    op.drop_table('event_links')

    op.drop_index(op.f('ix_evidence_observations_status'), table_name='evidence_observations')
    op.drop_index(op.f('ix_evidence_observations_video_id'), table_name='evidence_observations')
    op.drop_index(op.f('ix_evidence_observations_camera_id'), table_name='evidence_observations')
    op.drop_index(op.f('ix_evidence_observations_timestamp'), table_name='evidence_observations')
    op.drop_index(op.f('ix_evidence_observations_provenance_type'), table_name='evidence_observations')
    op.drop_index(op.f('ix_evidence_observations_observation_type'), table_name='evidence_observations')
    op.drop_index(op.f('ix_evidence_observations_incident_id'), table_name='evidence_observations')
    op.drop_index(op.f('ix_evidence_observations_id'), table_name='evidence_observations')
    op.drop_table('evidence_observations')
