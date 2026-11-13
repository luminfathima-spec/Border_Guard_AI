"""initial_schema

Revision ID: 4529bc7d8e58
Revises: 
Create Date: 2026-09-28 19:26:12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4529bc7d8e58'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. cameras
    op.create_table(
        'cameras',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('camera_identifier', sa.String(length=50), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('stream_url', sa.String(length=512), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('zone', sa.String(length=100), nullable=True),
        sa.Column('restricted_zones', sa.JSON(), nullable=False),
        sa.Column('virtual_lines', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cameras_camera_identifier'), 'cameras', ['camera_identifier'], unique=True)
    op.create_index(op.f('ix_cameras_id'), 'cameras', ['id'], unique=False)

    # 3. videos
    op.create_table(
        'videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=512), nullable=False),
        sa.Column('processed_path', sa.String(length=512), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('resolution', sa.String(length=50), nullable=True),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('total_frames', sa.Integer(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.String(length=512), nullable=True),
        sa.Column('total_detections_count', sa.Integer(), nullable=True),
        sa.Column('total_tracked_objects_count', sa.Integer(), nullable=True),
        sa.Column('total_incidents_count', sa.Integer(), nullable=True),
        sa.Column('camera_id', sa.Integer(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_videos_id'), 'videos', ['id'], unique=False)

    # 4. incidents
    op.create_table(
        'incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_number', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('ai_recommendations', sa.JSON(), nullable=False),
        sa.Column('ai_last_generated_at', sa.DateTime(), nullable=True),
        sa.Column('analyst_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incidents_created_at'), 'incidents', ['created_at'], unique=False)
    op.create_index(op.f('ix_incidents_id'), 'incidents', ['id'], unique=False)
    op.create_index(op.f('ix_incidents_incident_number'), 'incidents', ['incident_number'], unique=True)
    op.create_index(op.f('ix_incidents_severity'), 'incidents', ['severity'], unique=False)
    op.create_index(op.f('ix_incidents_status'), 'incidents', ['status'], unique=False)

    # 5. security_events
    op.create_table(
        'security_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('camera_id', sa.Integer(), nullable=True),
        sa.Column('video_id', sa.Integer(), nullable=True),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('description', sa.String(length=512), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('snapshot_path', sa.String(length=512), nullable=True),
        sa.Column('clip_path', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_events_camera_id'), 'security_events', ['camera_id'], unique=False)
    op.create_index(op.f('ix_security_events_event_type'), 'security_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_security_events_id'), 'security_events', ['id'], unique=False)
    op.create_index(op.f('ix_security_events_incident_id'), 'security_events', ['incident_id'], unique=False)
    op.create_index(op.f('ix_security_events_severity'), 'security_events', ['severity'], unique=False)
    op.create_index(op.f('ix_security_events_timestamp'), 'security_events', ['timestamp'], unique=False)
    op.create_index(op.f('ix_security_events_video_id'), 'security_events', ['video_id'], unique=False)

    # 6. alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('camera_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.String(length=512), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('acknowledged_by', sa.String(length=100), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['event_id'], ['security_events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_camera_id'), 'alerts', ['camera_id'], unique=False)
    op.create_index(op.f('ix_alerts_created_at'), 'alerts', ['created_at'], unique=False)
    op.create_index(op.f('ix_alerts_event_id'), 'alerts', ['event_id'], unique=False)
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)
    op.create_index(op.f('ix_alerts_incident_id'), 'alerts', ['incident_id'], unique=False)
    op.create_index(op.f('ix_alerts_severity'), 'alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_alerts_status'), 'alerts', ['status'], unique=False)

    # 7. detections
    op.create_table(
        'detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('camera_id', sa.Integer(), nullable=True),
        sa.Column('timestamp_offset', sa.Float(), nullable=False),
        sa.Column('frame_number', sa.Integer(), nullable=False),
        sa.Column('object_type', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('bbox_x1', sa.Float(), nullable=False),
        sa.Column('bbox_y1', sa.Float(), nullable=False),
        sa.Column('bbox_x2', sa.Float(), nullable=False),
        sa.Column('bbox_y2', sa.Float(), nullable=False),
        sa.Column('tracking_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_detections_camera_id'), 'detections', ['camera_id'], unique=False)
    op.create_index(op.f('ix_detections_frame_number'), 'detections', ['frame_number'], unique=False)
    op.create_index(op.f('ix_detections_id'), 'detections', ['id'], unique=False)
    op.create_index(op.f('ix_detections_object_type'), 'detections', ['object_type'], unique=False)
    op.create_index(op.f('ix_detections_tracking_id'), 'detections', ['tracking_id'], unique=False)
    op.create_index(op.f('ix_detections_video_id'), 'detections', ['video_id'], unique=False)
    op.create_index('ix_detections_video_frame', 'detections', ['video_id', 'frame_number'], unique=False)

    # 8. object_tracks
    op.create_table(
        'object_tracks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracking_id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=True),
        sa.Column('camera_id', sa.Integer(), nullable=True),
        sa.Column('object_type', sa.String(length=50), nullable=False),
        sa.Column('first_seen_frame', sa.Integer(), nullable=False),
        sa.Column('last_seen_frame', sa.Integer(), nullable=False),
        sa.Column('first_seen_timestamp', sa.Float(), nullable=False),
        sa.Column('last_seen_timestamp', sa.Float(), nullable=False),
        sa.Column('dwell_time_seconds', sa.Float(), nullable=False),
        sa.Column('max_confidence', sa.Float(), nullable=False),
        sa.Column('trajectory_json', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_object_tracks_camera_id'), 'object_tracks', ['camera_id'], unique=False)
    op.create_index(op.f('ix_object_tracks_id'), 'object_tracks', ['id'], unique=False)
    op.create_index(op.f('ix_object_tracks_is_active'), 'object_tracks', ['is_active'], unique=False)
    op.create_index(op.f('ix_object_tracks_object_type'), 'object_tracks', ['object_type'], unique=False)
    op.create_index(op.f('ix_object_tracks_tracking_id'), 'object_tracks', ['tracking_id'], unique=False)
    op.create_index(op.f('ix_object_tracks_video_id'), 'object_tracks', ['video_id'], unique=False)
    op.create_index('ix_object_tracks_video_tracking', 'object_tracks', ['video_id', 'tracking_id'], unique=False)

    # 9. evidence
    op.create_table(
        'evidence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['security_events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_event_id'), 'evidence', ['event_id'], unique=False)
    op.create_index(op.f('ix_evidence_evidence_type'), 'evidence', ['evidence_type'], unique=False)
    op.create_index(op.f('ix_evidence_id'), 'evidence', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_incident_id'), 'evidence', ['incident_id'], unique=False)

    # 10. ai_analyses
    op.create_table(
        'ai_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('prompt_type', sa.String(length=50), nullable=False),
        sa.Column('raw_prompt', sa.Text(), nullable=False),
        sa.Column('analysis_result', sa.Text(), nullable=False),
        sa.Column('structured_output', sa.JSON(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('grounded_citations', sa.JSON(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['security_events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_analyses_created_at'), 'ai_analyses', ['created_at'], unique=False)
    op.create_index(op.f('ix_ai_analyses_event_id'), 'ai_analyses', ['event_id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_id'), 'ai_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_incident_id'), 'ai_analyses', ['incident_id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_prompt_type'), 'ai_analyses', ['prompt_type'], unique=False)
    op.create_index(op.f('ix_ai_analyses_status'), 'ai_analyses', ['status'], unique=False)

    # 11. reports
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_number', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('generated_by_user_id', sa.Integer(), nullable=True),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=512), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=True),
        sa.Column('parameters_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['generated_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_created_at'), 'reports', ['created_at'], unique=False)
    op.create_index(op.f('ix_reports_generated_by_user_id'), 'reports', ['generated_by_user_id'], unique=False)
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)
    op.create_index(op.f('ix_reports_incident_id'), 'reports', ['incident_id'], unique=False)
    op.create_index(op.f('ix_reports_report_number'), 'reports', ['report_number'], unique=True)
    op.create_index(op.f('ix_reports_report_type'), 'reports', ['report_type'], unique=False)
    op.create_index(op.f('ix_reports_status'), 'reports', ['status'], unique=False)

    # 12. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=50), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('reports')
    op.drop_table('ai_analyses')
    op.drop_table('evidence')
    op.drop_table('object_tracks')
    op.drop_table('detections')
    op.drop_table('alerts')
    op.drop_table('security_events')
    op.drop_table('incidents')
    op.drop_table('videos')
    op.drop_table('cameras')
    op.drop_table('users')
