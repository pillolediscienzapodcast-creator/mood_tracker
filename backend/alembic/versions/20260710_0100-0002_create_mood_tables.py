"""create mood tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-10 01:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "emotional_model_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(length=20), nullable=False),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("n_turns_trained", sa.Integer(), nullable=False),
        sa.Column("feedback_count", sa.Integer(), nullable=False),
        sa.Column("row_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_emotional_model_states_user_id",
        "emotional_model_states",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "emotional_turns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("response_latency_s", sa.Float(), nullable=False),
        sa.Column("backspace_count", sa.Integer(), nullable=False),
        sa.Column("is_followup", sa.Boolean(), nullable=False),
        sa.Column("followup_depth", sa.Integer(), nullable=False),
        sa.Column("hour_of_day", sa.Integer(), nullable=False),
        sa.Column(
            "feature_vector", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("emotions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "dominant_emotions", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("valence", sa.Float(), nullable=False),
        sa.Column("arousal", sa.Float(), nullable=False),
        sa.Column("dominance", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("no_lexicon_match", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emotional_turns_user_id", "emotional_turns", ["user_id"])

    op.create_table(
        "emotional_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("turn_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("corretto", sa.Boolean(), nullable=False),
        sa.Column("emozione_corretta", sa.String(length=20), nullable=True),
        sa.Column("consolidated", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["turn_id"], ["emotional_turns.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emotional_feedback_turn_id", "emotional_feedback", ["turn_id"])
    op.create_index("ix_emotional_feedback_user_id", "emotional_feedback", ["user_id"])
    op.create_index(
        "ix_emotional_feedback_consolidated", "emotional_feedback", ["consolidated"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_emotional_feedback_consolidated", table_name="emotional_feedback")
    op.drop_index("ix_emotional_feedback_user_id", table_name="emotional_feedback")
    op.drop_index("ix_emotional_feedback_turn_id", table_name="emotional_feedback")
    op.drop_table("emotional_feedback")

    op.drop_index("ix_emotional_turns_user_id", table_name="emotional_turns")
    op.drop_table("emotional_turns")

    op.drop_index(
        "ix_emotional_model_states_user_id", table_name="emotional_model_states"
    )
    op.drop_table("emotional_model_states")
