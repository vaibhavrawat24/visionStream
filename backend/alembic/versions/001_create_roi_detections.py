"""create roi_detections table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roi_detections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("frame_width", sa.Integer(), nullable=False),
        sa.Column("frame_height", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roi_detections_id", "roi_detections", ["id"])
    op.create_index("ix_roi_detections_session_id", "roi_detections", ["session_id"])
    op.create_index("ix_roi_detections_detected_at", "roi_detections", ["detected_at"])


def downgrade() -> None:
    op.drop_index("ix_roi_detections_detected_at", table_name="roi_detections")
    op.drop_index("ix_roi_detections_session_id", table_name="roi_detections")
    op.drop_index("ix_roi_detections_id", table_name="roi_detections")
    op.drop_table("roi_detections")
