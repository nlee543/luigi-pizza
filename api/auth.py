"""Database-backed cookie authentication, shared by all protected routes."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from typing import Annotated, Literal

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import LoginSession, User


COOKIE_NAME = "luigi_session"
SESSION_SECONDS = 8 * 60 * 60
IDLE_SECONDS = 30 * 60
password_hasher = PasswordHasher()
_dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))
cookie_scheme = APIKeyCookie(name=COOKIE_NAME, auto_error=False)


def now():
    # SQLite stores naive datetimes. All application timestamps represent UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def token_hash(token):
    return sha256(token.encode()).hexdigest()


def verify_password(password, encoded):
    try:
        return password_hasher.verify(encoded or _dummy_hash, password) and bool(encoded)
    except (VerificationError, InvalidHashError):
        return False


def get_session(request: Request):
    with request.app.state.sessions() as session:
        yield session


DB = Annotated[Session, Depends(get_session)]


def commit(session):
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Operation conflicts with existing data or database constraints.") from None


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


Password = Annotated[str, Field(min_length=12, max_length=128)]
Role = Literal["customer", "staff", "admin"]


class EmailInput(Schema):
    email: Annotated[str, Field(min_length=3, max_length=254)]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        value = value.strip().lower()
        if value.count("@") != 1 or any(c.isspace() for c in value):
            raise ValueError("Provide a valid email address.")
        local, domain = value.split("@")
        if not local or not domain or "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("Provide a valid email address.")
        return value


class ProfileInput(Schema):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    address: Annotated[str, Field(min_length=1, max_length=500)]
    phone_number: Annotated[str, Field(min_length=1, max_length=40)]
    dine_in_name: Annotated[str, Field(min_length=1, max_length=100)]


class Registration(ProfileInput, EmailInput):
    password: Password


class UserOutput(ProfileInput):
    id: int
    email: str | None
    role: Role
    must_change_password: bool
    active: bool


class LoginInput(EmailInput):
    password: Annotated[str, Field(min_length=1, max_length=128)]


class PasswordChange(Schema):
    current_password: Annotated[str, Field(min_length=1, max_length=128)]
    new_password: Password


class AuthOutput(Schema):
    user: UserOutput
    csrf_token: str


def authenticated_user(
    request: Request, session: DB,
    cookie: Annotated[str | None, Depends(cookie_scheme)],
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
):
    login = session.scalar(select(LoginSession).where(LoginSession.token_hash == token_hash(cookie))) if cookie else None
    current_time = now()
    if login is None or login.expires_at <= current_time or (current_time - login.last_seen_at).total_seconds() >= IDLE_SECONDS:
        raise HTTPException(401, "Login required or session expired.")
    user = session.get(User, login.user_id)
    if user is None or not user.active:
        raise HTTPException(401, "Login required or session expired.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not csrf_token or not secrets.compare_digest(csrf_token, login.csrf_token):
            raise HTTPException(403, "A valid X-CSRF-Token header is required.")
    login.last_seen_at = current_time
    session.commit()
    request.state.login = login
    return user


Authenticated = Annotated[User, Depends(authenticated_user)]


def get_current_user(user: Authenticated):
    if user.must_change_password:
        raise HTTPException(403, "Change your temporary password before continuing.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_staff(user: CurrentUser):
    if user.role not in {"staff", "admin"}:
        raise HTTPException(403, "Staff access required.")
    return user


Staff = Annotated[User, Depends(require_staff)]


def require_admin(user: CurrentUser):
    if user.role != "admin":
        raise HTTPException(403, "Administrator access required.")
    return user


Admin = Annotated[User, Depends(require_admin)]


def public_auth_guard(
    protection: Annotated[str | None, Header(alias="X-CSRF-Protection")] = None,
):
    # A custom header prevents cross-origin forms from submitting login/registration.
    # No CORS origins are enabled. Origin checking also applies in main.py.
    if protection != "1":
        raise HTTPException(403, "Send X-CSRF-Protection: 1.")


def register_customer(data, session, temporary=False):
    user = User(**data.model_dump(exclude={"password"}), role="customer",
                password_hash=password_hasher.hash(data.password), must_change_password=temporary)
    session.add(user)
    commit(session)
    return user


def clear_cookie(response, request):
    response.delete_cookie(COOKIE_NAME, path="/", secure=request.app.state.cookie_secure,
                           httponly=True, samesite="lax")


router = APIRouter(tags=["authentication"])


@router.post("/auth/register", response_model=UserOutput, status_code=201,
             dependencies=[Depends(public_auth_guard)])
def register(data: Registration, session: DB):
    return register_customer(data, session)


@router.post("/auth/login", response_model=AuthOutput, dependencies=[Depends(public_auth_guard)])
def login(data: LoginInput, request: Request, response: Response, session: DB):
    user = session.scalar(select(User).where(User.email == data.email))
    valid = verify_password(data.password, user.password_hash if user else None)
    if user is None or not valid or not user.active:
        raise HTTPException(401, "Invalid email or password.")
    if password_hasher.check_needs_rehash(user.password_hash):
        user.password_hash = password_hasher.hash(data.password)
    # Rotate any previous session on this browser and discard expired sessions.
    old_cookie = request.cookies.get(COOKIE_NAME)
    if old_cookie:
        session.execute(delete(LoginSession).where(LoginSession.token_hash == token_hash(old_cookie)))
    current_time = now()
    session.execute(delete(LoginSession).where(LoginSession.expires_at <= current_time))
    token = secrets.token_urlsafe(32)
    login_session = LoginSession(token_hash=token_hash(token), user_id=user.id,
                                 csrf_token=secrets.token_urlsafe(32), created_at=current_time,
                                 last_seen_at=current_time, expires_at=current_time + timedelta(seconds=SESSION_SECONDS))
    session.add(login_session)
    commit(session)
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, path="/", httponly=True,
                        secure=request.app.state.cookie_secure, samesite="lax")
    return AuthOutput(user=UserOutput.model_validate(user), csrf_token=login_session.csrf_token)


@router.get("/auth/me", response_model=AuthOutput)
def me(request: Request, user: Authenticated):
    return AuthOutput(user=UserOutput.model_validate(user), csrf_token=request.state.login.csrf_token)


@router.post("/auth/logout", status_code=204)
def logout(request: Request, session: DB, user: Authenticated):
    session.delete(request.state.login)
    session.commit()
    response = Response(status_code=204)
    clear_cookie(response, request)
    return response


@router.post("/auth/change-password", status_code=204)
def change_password(data: PasswordChange, request: Request, session: DB, user: Authenticated):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect.")
    if data.current_password == data.new_password:
        raise HTTPException(400, "Choose a different password.")
    user.password_hash = password_hasher.hash(data.new_password)
    user.must_change_password = False
    session.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    commit(session)
    response = Response(status_code=204)
    clear_cookie(response, request)
    return response


@router.put("/auth/profile", response_model=UserOutput)
def update_profile(data: ProfileInput, session: DB, user: CurrentUser):
    for key, value in data.model_dump().items():
        setattr(user, key, value)
    commit(session)
    return user


@router.post("/staff/customers", response_model=UserOutput, status_code=201)
def staff_register(data: Registration, session: DB, staff: Staff):
    return register_customer(data, session, temporary=True)


class AccountAccess(Schema):
    role: Role
    active: bool


@router.patch("/admin/users/{user_id}/access", response_model=UserOutput)
def change_access(user_id: int, data: AccountAccess, session: DB, admin: Admin):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found.")
    if user.id == admin.id:
        raise HTTPException(409, "Use another administrator to change your own access.")
    user.role, user.active = data.role, data.active
    session.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    commit(session)
    return user
