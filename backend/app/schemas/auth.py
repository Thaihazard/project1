from app.schemas.common import APIModel


class LoginRequest(APIModel):
    username: str
    password: str


class FirebaseLoginRequest(APIModel):
    credential: str


class UserOut(APIModel):
    id: str
    username: str
    role: str
    employee_id: str | None = None
    permissions: list[str]


class TokenOut(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(APIModel):
    refresh_token: str


class ChangePasswordRequest(APIModel):
    current_password: str
    new_password: str
