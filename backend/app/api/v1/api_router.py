from fastapi import APIRouter

from app.api.v1.endpoints import ai_salary, attendance, auth, benefits, contracts, employees, leave, overtime, payroll

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(employees.router)
api_router.include_router(attendance.router)
api_router.include_router(overtime.router)
api_router.include_router(leave.router)
api_router.include_router(contracts.router)
api_router.include_router(benefits.router)
api_router.include_router(payroll.router)
api_router.include_router(ai_salary.router)
