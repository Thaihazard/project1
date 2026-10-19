from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token, hash_password, verify_password
from app.models.user import User
from app.models.employee import Employee
from app.schemas.auth import ChangePasswordRequest, FirebaseLoginRequest, LoginRequest, RefreshRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
ROLE_PERMISSIONS = {
    "employee": ["payslip:read:self", "attendance:write:self", "leave:write:self", "overtime:write:self", "contracts:read:self", "benefits:read:self", "ai:predict:self"],
    "manager": ["employees:read:team", "attendance:read:team", "leave:review:team", "overtime:review:team", "contracts:read:team", "payroll:read", "ai:predict", "performance:write:team"],
    "hr": ["employees:read:all", "attendance:read:all", "leave:review:all", "overtime:review:all", "contracts:manage", "benefits:manage", "payroll:read", "payroll:calculate", "payroll:export", "ai:predict", "ai:budget", "payroll:approve"],
}


def user_out(user: User) -> UserOut:
    return UserOut(id=user.id, username=user.username, role=user.role, employee_id=user.employee_id,
                   permissions=ROLE_PERMISSIONS.get(user.role, []))


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenOut:
    login_id = payload.username.strip()
    user = await db.scalar(
        select(User).where(
            or_(User.username == login_id, func.lower(User.email) == login_id.lower())
        )
    )
    if user is None or user.role == "disabled" or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")
    return TokenOut(access_token=create_access_token(user.id, user.role), refresh_token=create_refresh_token(user.id, user.role), user=user_out(user))


def _firebase_admin_app():
    try:
        import firebase_admin
        from firebase_admin import credentials

        try:
            return firebase_admin.get_app()
        except ValueError:
            if not settings.firebase_project_id:
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "FIREBASE_PROJECT_ID is not configured")
            if settings.firebase_service_account_path:
                if not settings.firebase_service_account_path.is_file():
                    raise HTTPException(
                        status.HTTP_503_SERVICE_UNAVAILABLE,
                        "Firebase service account JSON file is missing. Check FIREBASE_SERVICE_ACCOUNT_PATH.",
                    )
                credential = credentials.Certificate(str(settings.firebase_service_account_path))
            else:
                credential = credentials.ApplicationDefault()
            return firebase_admin.initialize_app(credential, {"projectId": settings.firebase_project_id})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Firebase Admin credentials are not configured") from exc


@router.post("/firebase", response_model=TokenOut)
async def firebase_login(payload: FirebaseLoginRequest, db: AsyncSession = Depends(get_db)) -> TokenOut:
    """Verify a Firebase ID token and link its verified email to an existing user."""
    try:
        from firebase_admin import auth as firebase_auth

        claims = firebase_auth.verify_id_token(payload.credential, app=_firebase_admin_app(), check_revoked=True)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firebase credential is invalid, expired, or revoked") from exc

    email = str(claims.get("email", "")).strip().lower()
    firebase_uid = str(claims.get("uid", ""))
    if not email or not firebase_uid or claims.get("email_verified") is not True:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firebase must provide a verified email address")

    user = await db.scalar(select(User).where(User.firebase_uid == firebase_uid))
    if user is None:
        employee = await db.scalar(select(Employee).where(func.lower(Employee.email) == email))
        if employee is not None:
            if not employee.is_active:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Employee access has been deactivated")
            user = await db.scalar(
                select(User).where(User.employee_id == employee.id, User.role.in_(["employee", "manager"]))
            )
            if user is None:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "This employee has no AI CompHub account")
            if employee.role not in {"employee", "manager"}:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "This employee has an unsupported application role")
            user.role = employee.role
        else:
            mapped_username = next(
                (username for allowed_email, username in settings.firebase_auth_email_map.items()
                 if allowed_email.strip().lower() == email),
                None,
            )
            if mapped_username is not None:
                user = await db.scalar(select(User).where(User.username == mapped_username))
        if user is None:
            user = await db.scalar(select(User).where(User.username == email))
        if user is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Email chưa được liên kết với tài khoản nhân sự nào trong doanh nghiệp")
        if user.role == "disabled":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated")
        if user.firebase_uid and user.firebase_uid != firebase_uid:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is already linked to a different Firebase identity")
        if user.email and user.email.lower() != email:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This AI CompHub user is linked to a different email")
        user.email = email
        user.firebase_uid = firebase_uid
        await db.commit()
        await db.refresh(user)

    if user.role == "disabled":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated")
    return TokenOut(access_token=create_access_token(user.id, user.role), refresh_token=create_refresh_token(user.id, user.role), user=user_out(user))


@router.post("/token", include_in_schema=False)
async def swagger_login(
    form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """OAuth2 form endpoint used by Swagger's Authorize dialog."""
    login_id = form.username.strip()
    user = await db.scalar(
        select(User).where(
            or_(User.username == login_id, func.lower(User.email) == login_id.lower())
        )
    )
    if user is None or user.role == "disabled" or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")
    return {
        "access_token": create_access_token(user.id, user.role),
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenOut)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenOut:
    claims = decode_refresh_token(payload.refresh_token)
    if not claims or not claims.get("sub"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    user = await db.get(User, claims["sub"])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return TokenOut(access_token=create_access_token(user.id, user.role), refresh_token=create_refresh_token(user.id, user.role), user=user_out(user))


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(payload: ChangePasswordRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    if len(payload.new_password) < 12:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "New password must be at least 12 characters")
    user.password_hash = hash_password(payload.new_password)
    await db.commit()


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)) -> UserOut:
    return user_out(user)
