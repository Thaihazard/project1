import argparse
import asyncio
from getpass import getpass
from uuid import uuid4

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.employee import Employee


async def create_user(username: str, role: str, employee_id: str | None) -> None:
    password = getpass("Password (at least 12 characters): ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")
    if role != "hr" and not employee_id:
        raise SystemExit("Manager and employee accounts require --employee-id.")
    async with SessionLocal() as db:
        existing = await db.scalar(select(User.id).where(User.username == username))
        if existing:
            raise SystemExit(f"User '{username}' already exists.")
        if employee_id and await db.get(Employee, employee_id) is None:
            raise SystemExit(f"Employee '{employee_id}' does not exist.")
        db.add(User(id=str(uuid4()), username=username, password_hash=hash_password(password), role=role, employee_id=employee_id))
        await db.commit()
    print(f"Created {role} account '{username}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a CompHub API account")
    parser.add_argument("--username", required=True)
    parser.add_argument("--role", choices=["employee", "manager", "hr"], required=True)
    parser.add_argument("--employee-id")
    args = parser.parse_args()
    asyncio.run(create_user(args.username, args.role, args.employee_id))


if __name__ == "__main__":
    main()
