"""add_video_ingestion_fields

Revision ID: 68a1f2e4b890
Revises: 4529bc7d8e58
Create Date: 2026-09-28 19:40:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '68a1f2e4b890'
down_revision: Union[str, None] = '4529bc7d8e58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('videos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('checksum_sha256', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('source_timestamp', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('mime_type', sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('videos', schema=None) as batch_op:
        batch_op.drop_column('mime_type')
        batch_op.drop_column('source_timestamp')
        batch_op.drop_column('checksum_sha256')
