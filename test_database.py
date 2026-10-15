from decimal import Decimal

import pytest

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Base, Drink, Pizza, Topping, User


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


@pytest.mark.parametrize("size", ["small", "medium", "large"])
def test_drink_generated_id_and_values(engine, size):
    with Session(engine) as session:
        drink = Drink(size=size, price=Decimal("1.25"), name="x" * 50)
        session.add(drink)
        session.commit()
        session.refresh(drink)
        assert isinstance(drink.id, int)
        assert drink.size == size
        assert drink.price == Decimal("1.25")
        assert drink.name == "x" * 50


@pytest.mark.parametrize("column, value", [
    ("size", "extra-large"),
    ("size", "Small"),
    ("size", ""),
    ("size", None),
    ("price", None),
    ("name", None),
    ("name", "x" * 51),
])
def test_drink_rejects_invalid_values(engine, column, value):
    values = {"size": "small", "price": Decimal("1.25"), "name": "Cola"}
    values[column] = value
    with Session(engine) as session:
        session.add(Drink(**values))
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("name", ["Pepperoni", "x" * 50])
def test_topping_generated_id_and_name(engine, name):
    with Session(engine) as session:
        topping = Topping(name=name)
        session.add(topping)
        session.commit()
        session.refresh(topping)
        assert isinstance(topping.id, int)
        assert topping.name == name


@pytest.mark.parametrize("name", ["x" * 51, None])
def test_topping_rejects_invalid_name(engine, name):
    with Session(engine) as session:
        session.add(Topping(name=name))
        with pytest.raises(IntegrityError):
            session.commit()


def test_pizza_generated_id_and_values(engine):
    with Session(engine) as session:
        pizza = Pizza(size="Small", price=Decimal("5.00"))
        session.add(pizza)
        session.commit()
        session.refresh(pizza)
        assert isinstance(pizza.id, int)
        assert pizza.size == "Small"
        assert pizza.price == Decimal("5.00")


@pytest.mark.parametrize("missing_column", ["size", "price"])
def test_pizza_requires_size_and_price(engine, missing_column):
    values = {"size": "Small", "price": Decimal("5.00")}
    values.pop(missing_column)
    with Session(engine) as session:
        session.add(Pizza(**values))
        with pytest.raises(IntegrityError):
            session.commit()


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
