"""Rename Google subject identifier to Firebase UID."""

from alembic import op
import sqlalchemy as sa

revision = "0004_firebase_auth"
down_revision = "0003_google_oauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_users_google_sub", table_name="users")
    op.alter_column("users", "google_sub", new_column_name="firebase_uid", existing_type=sa.String(length=255), existing_nullable=True)
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_firebase_uid", table_name="users")
    op.alter_column("users", "firebase_uid", new_column_name="google_sub", existing_type=sa.String(length=255), existing_nullable=True)
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
