"""Add compensation history, performance snapshots and AI prediction audit."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa

from app.models import Base


revision = "0007_comp_ai_history"
down_revision = "0006_employee_active"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def upgrade() -> None:
    bind = op.get_bind()

    # create_all in the original initial migration uses current metadata on a fresh DB;
    # checkfirst also supports databases that were already on revision 0006.
    for table_name in (
        "ai_predictions",
        "employee_compensation_history",
        "employee_performance_assessments",
    ):
        Base.metadata.tables[table_name].create(bind=bind, checkfirst=True)

    inspector = _inspector()
    employee_columns = {column["name"] for column in inspector.get_columns("employees")}
    if "years_experience" not in employee_columns:
        op.add_column("employees", sa.Column("years_experience", sa.Float(), nullable=True))
    if "certification_count" not in employee_columns:
        op.add_column("employees", sa.Column("certification_count", sa.Integer(), nullable=True))

    proposal_columns = {column["name"] for column in inspector.get_columns("payroll_proposals")}
    if "prediction_id" not in proposal_columns:
        prediction_column = sa.Column(
            "prediction_id", sa.String(length=40), sa.ForeignKey("ai_predictions.id"), nullable=True,
        )
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("payroll_proposals") as batch_op:
                batch_op.add_column(prediction_column)
        else:
            op.add_column("payroll_proposals", prediction_column)
    if "current_salary" not in proposal_columns:
        op.add_column("payroll_proposals", sa.Column("current_salary", sa.BigInteger(), nullable=True))
    if "proposed_salary" not in proposal_columns:
        op.add_column("payroll_proposals", sa.Column("proposed_salary", sa.BigInteger(), nullable=True))
    if "decision_note" not in proposal_columns:
        op.add_column("payroll_proposals", sa.Column("decision_note", sa.Text(), nullable=True))
    inspector = _inspector()
    existing_indexes = {index["name"] for index in inspector.get_indexes("payroll_proposals")}
    if "ix_payroll_proposals_prediction_id" not in existing_indexes:
        op.create_index("ix_payroll_proposals_prediction_id", "payroll_proposals", ["prediction_id"])

    inspector = _inspector()
    slip_uniques = {tuple(item["column_names"]) for item in inspector.get_unique_constraints("pay_slips")}
    if ("employee_id", "pay_period_id") not in slip_uniques:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("pay_slips") as batch_op:
                batch_op.create_unique_constraint("uq_pay_slip_employee_period", ["employee_id", "pay_period_id"])
        else:
            op.create_unique_constraint("uq_pay_slip_employee_period", "pay_slips", ["employee_id", "pay_period_id"])

    inspector = _inspector()
    period_checks = {constraint.get("name") for constraint in inspector.get_check_constraints("pay_periods")}
    if "ck_pay_period_dates" not in period_checks:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("pay_periods") as batch_op:
                batch_op.create_check_constraint("ck_pay_period_dates", "start_date <= end_date")
        else:
            op.create_check_constraint("ck_pay_period_dates", "pay_periods", "start_date <= end_date")

    # Preserve the current salary as the first known compensation-history record.
    history = Base.metadata.tables["employee_compensation_history"]
    employees = sa.table(
        "employees",
        sa.column("id", sa.String),
        sa.column("base_salary", sa.BigInteger),
    )
    rows = bind.execute(sa.select(employees.c.id, employees.c.base_salary)).all()
    for employee_id, salary in rows:
        exists = bind.execute(
            sa.select(history.c.id).where(history.c.employee_id == employee_id).limit(1)
        ).first()
        if not exists:
            bind.execute(history.insert().values(
                id=f"CH-{uuid4().hex[:20].upper()}",
                employee_id=employee_id,
                base_salary=salary or 0,
                effective_from=sa.func.current_date(),
                change_reason="Initial salary snapshot during database upgrade",
            ))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = _inspector()
    proposal_columns = {column["name"] for column in inspector.get_columns("payroll_proposals")}
    for name in ("decision_note", "proposed_salary", "current_salary"):
        if name in proposal_columns:
            op.drop_column("payroll_proposals", name)
    if "prediction_id" in proposal_columns:
        existing_indexes = {index["name"] for index in _inspector().get_indexes("payroll_proposals")}
        if "ix_payroll_proposals_prediction_id" in existing_indexes:
            op.drop_index("ix_payroll_proposals_prediction_id", table_name="payroll_proposals")
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("payroll_proposals") as batch_op:
                batch_op.drop_column("prediction_id")
        else:
            op.drop_column("payroll_proposals", "prediction_id")

    inspector = _inspector()
    slip_uniques = {tuple(item["column_names"]): item["name"] for item in inspector.get_unique_constraints("pay_slips")}
    constraint_name = slip_uniques.get(("employee_id", "pay_period_id"))
    if constraint_name:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("pay_slips") as batch_op:
                batch_op.drop_constraint(constraint_name, type_="unique")
        else:
            op.drop_constraint(constraint_name, "pay_slips", type_="unique")

    period_checks = {constraint.get("name") for constraint in _inspector().get_check_constraints("pay_periods")}
    if "ck_pay_period_dates" in period_checks:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("pay_periods") as batch_op:
                batch_op.drop_constraint("ck_pay_period_dates", type_="check")
        else:
            op.drop_constraint("ck_pay_period_dates", "pay_periods", type_="check")

    inspector = _inspector()
    employee_columns = {column["name"] for column in inspector.get_columns("employees")}
    if "certification_count" in employee_columns:
        op.drop_column("employees", "certification_count")
    if "years_experience" in employee_columns:
        op.drop_column("employees", "years_experience")
    for table_name in (
        "employee_performance_assessments",
        "employee_compensation_history",
        "ai_predictions",
    ):
        if _inspector().has_table(table_name):
            op.drop_table(table_name)
