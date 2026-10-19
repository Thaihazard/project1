"""Add employee active status for safe offboarding."""

from alembic import op
import sqlalchemy as sa


revision = "0006_employee_active"
down_revision = "0005_employee_email"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("employees", "is_active")
