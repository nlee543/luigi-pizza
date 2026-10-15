import pytest

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Base, User


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def add_user(engine):
    def create_user(**overrides):
        values = dict(name="Alex", address="123 Main St", phone_number="+1 0123",
                      dine_in_name="Alex")
        values.update(overrides)
        with Session(engine) as session:
            user = User(**values)
            session.add(user)
            session.commit()
            return user.id, user.admin, user.phone_number

    return create_user


def test_generated_id_default_admin_and_optional_email(add_user):
    first_id, admin, phone = add_user()
    second_id, _, _ = add_user()
    assert isinstance(first_id, int)
    assert first_id != second_id
    assert admin is False
    assert phone == "+1 0123"


def test_unique_email(add_user):
    add_user(email="alex@example.com")
    with pytest.raises(IntegrityError):
        add_user(email="alex@example.com")


def test_admin_true(add_user):
    assert add_user(admin=True)[1] is True


@pytest.mark.parametrize("invalid", [2, None])
def test_database_rejects_invalid_admin(engine, add_user, invalid):
    user_id, _, _ = add_user()
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("UPDATE users SET admin = :value WHERE id = :id"),
                               {"value": invalid, "id": user_id})
