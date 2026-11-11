"""Add JWT revocation storage.

Revision ID: 0002_revoked_tokens
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_revoked_tokens"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("token_id", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.Text(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("token_id"),
    )


def downgrade() -> None:
    op.drop_table("revoked_tokens")
