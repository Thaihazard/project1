"""Add overtime and employee benefit tables."""

from alembic import op

from app.models import Base

revision = "0002_operations"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    op.drop_table("benefit_enrollments")
    op.drop_table("benefit_offerings")
    op.drop_table("overtime_requests")
