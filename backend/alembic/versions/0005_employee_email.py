"""Add email address for employee identity matching."""

from alembic import op
import sqlalchemy as sa

revision = "0005_employee_email"
down_revision = "0004_firebase_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("employees")}
    indexes = {i["name"] for i in insp.get_indexes("employees")}

    if "email" not in cols:
        op.add_column("employees", sa.Column("email", sa.String(length=255), nullable=True))
    if "ix_employees_email" not in indexes:
        op.create_index("ix_employees_email", "employees", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_employees_email", table_name="employees")
    op.drop_column("employees", "email")
