"""Provision an account locally; passwords are prompted, never passed on the CLI."""
import argparse
from getpass import getpass
import os

from sqlalchemy import URL, create_engine, delete, select
from sqlalchemy.orm import Session

from api.auth import EmailInput, PasswordChange, password_hasher
from database import DATABASE_PATH
from models import Base, LoginSession, User


def provision_account(session, email, password, role, name, *, existing=False):
    email = EmailInput(email=email).email
    PasswordChange(current_password=password, new_password=password)
    user = session.scalar(select(User).where(User.email == email))
    if existing and user is None:
        raise ValueError("No account with that email exists.")
    if not existing and user is not None:
        raise ValueError("Account already exists. Use --existing to explicitly reset its credentials.")
    if user is None:
        user = User(email=email, name=name, address="Not provided", phone_number="Not provided", dine_in_name=name)
        session.add(user)
    else:
        session.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    user.password_hash = password_hasher.hash(password)
    user.role = role
    user.must_change_password = True
    user.active = True
    session.commit()
    return user.id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=["customer", "staff", "admin"])
    parser.add_argument("--name", default="Restaurant staff")
    parser.add_argument("--existing", action="store_true", help="Reset credentials for an existing profile")
    args = parser.parse_args()
    password = getpass("Temporary password (12-128 characters): ")
    if password != getpass("Confirm temporary password: "):
        raise SystemExit("Passwords do not match.")
    engine = create_engine(os.getenv("CONNECTIONSTRING") or URL.create("sqlite", database=str(DATABASE_PATH)))
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            user_id = provision_account(session, args.email, password, args.role, args.name, existing=args.existing)
        print(f"Provisioned user {user_id}. Password change required at next login.")
    finally:
        engine.dispose()
