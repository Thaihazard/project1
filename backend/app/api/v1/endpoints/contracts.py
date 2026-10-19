from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.user import User
from app.schemas.contract import ContractCreate, ContractOut

router = APIRouter(prefix="/contracts", tags=["contracts"])


def to_out(contract: Contract, employee: Employee) -> ContractOut:
    return ContractOut(id=contract.id, employee_id=employee.id, employee_name=employee.full_name,
        contract_type=contract.contract_type, start_date=contract.start_date, end_date=contract.end_date,
        base_salary=int(contract.base_salary), status=contract.status)


@router.get("/me", response_model=list[ContractOut])
async def my_contracts(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> list[ContractOut]:
    if not user.employee_id:
        return []
    rows = await db.execute(select(Contract, Employee).join(Employee).where(
        Contract.employee_id == user.employee_id
    ).order_by(Contract.start_date.desc()))
    return [to_out(contract, employee) for contract, employee in rows]


@router.get("", response_model=list[ContractOut])
async def contracts(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("manager", "hr"))) -> list[ContractOut]:
    statement = select(Contract, Employee).join(Employee)
    if user.role == "manager":
        statement = statement.where(Employee.manager_id == user.employee_id)
    rows = await db.execute(statement.order_by(Contract.start_date.desc()))
    return [to_out(contract, employee) for contract, employee in rows]


@router.post("", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
async def create_contract(payload: ContractCreate, db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("hr"))) -> ContractOut:
    employee = await db.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    item = Contract(id=str(uuid4()), employee_id=employee.id, contract_type=payload.contract_type,
        start_date=payload.start_date, end_date=payload.end_date, base_salary=payload.base_salary, status="active")
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return to_out(item, employee)
