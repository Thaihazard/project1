"""Add Google account identifiers to users."""

from alembic import op
import sqlalchemy as sa

revision = "0003_google_oauth"
down_revision = "0002_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("users")}
    indexes = {i["name"] for i in insp.get_indexes("users")}

    if "email" not in cols:
        op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    if "google_sub" not in cols and "firebase_uid" not in cols:
        op.add_column("users", sa.Column("google_sub", sa.String(length=255), nullable=True))

    # Re-check columns after potential add
    cols = {c["name"] for c in insp.get_columns("users")}
    if "ix_users_email" not in indexes and "email" in cols:
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    if "ix_users_google_sub" not in indexes and "google_sub" in cols:
        op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "google_sub")
    op.drop_column("users", "email")
