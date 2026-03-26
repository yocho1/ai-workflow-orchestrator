"""Add document metadata table for extracted structured data

Revision ID: 20260326_0003
Revises: 20260325_0002
Create Date: 2026-03-26 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260326_0003"
down_revision = "20260325_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("extracted_data", sa.JSON(), nullable=False),
        sa.Column("extraction_model", sa.String(length=100), nullable=False),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index(
        op.f("ix_document_metadata_document_id"),
        "document_metadata",
        ["document_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_document_metadata_document_id"),
        table_name="document_metadata",
    )
    op.drop_table("document_metadata")
