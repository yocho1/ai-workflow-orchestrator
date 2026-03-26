"""Add review flags to document_metadata

Revision ID: 20260326_0004
Revises: 20260326_0003
Create Date: 2026-03-26 00:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260326_0004"
down_revision = "20260326_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_metadata",
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "document_metadata",
        sa.Column("review_reason", sa.Text(), nullable=True),
    )
    op.create_index(
        op.f("ix_document_metadata_needs_review"),
        "document_metadata",
        ["needs_review"],
        unique=False,
    )
    op.alter_column("document_metadata", "needs_review", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_metadata_needs_review"), table_name="document_metadata")
    op.drop_column("document_metadata", "review_reason")
    op.drop_column("document_metadata", "needs_review")
