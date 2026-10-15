from decimal import Decimal

import pytest

from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Base, Drink, Inventory, Order, OrderDrink, Pizza, Topping, User


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.mark.parametrize("quantity", [Decimal("0"), Decimal("12"), Decimal("12.3")])
def test_inventory_generated_id_and_values(engine, quantity):
    with Session(engine) as session:
        item = Inventory(quantity=quantity, unit="u" * 10, name="n" * 50)
        session.add(item)
        session.commit()
        session.refresh(item)
        assert isinstance(item.id, int)
        assert item.quantity == quantity
        assert item.unit == "u" * 10
        assert item.name == "n" * 50


@pytest.mark.parametrize("column, value", [
    ("quantity", Decimal("12.34")),
    ("quantity", None),
    ("unit", "u" * 11),
    ("unit", None),
    ("name", "n" * 51),
    ("name", None),
])
def test_inventory_rejects_invalid_values(engine, column, value):
    values = {"quantity": Decimal("12.3"), "unit": "lbs", "name": "Flour"}
    values[column] = value
    with Session(engine) as session:
        session.add(Inventory(**values))
        with pytest.raises(IntegrityError):
            session.commit()


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
        order = Order(order_drinks=[OrderDrink(drink=drink, quantity=1)])
        session.add(order)
        session.commit()
        assert isinstance(drink.id, int)
        assert drink.size == size
        assert drink.price == Decimal("1.25")
        assert drink.name == "x" * 50
        assert drink.orders == [order]


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
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(Drink.__table__.insert().values(**values))


@pytest.fixture
def drink():
    return Drink(size="small", price=Decimal("1.25"), name="Cola")


@pytest.mark.parametrize("quantity", [1, 2, 10])
def test_orders_drinks_generated_id_and_quantity(engine, drink, quantity):
    with Session(engine) as session:
        link = OrderDrink(order=Order(), drink=drink, quantity=quantity)
        session.add(link)
        session.commit()
        link_id = link.id
    with Session(engine) as session:
        link = session.get(OrderDrink, link_id)
        assert isinstance(link.id, int)
        assert link.quantity == quantity
        assert link.order_id == link.order.id
        assert link.drink_id == link.drink.id
        assert link.order.order_drinks == [link]
        assert link.drink.order_drinks == [link]
        assert link.order.drinks == [link.drink]
        assert link.drink.orders == [link.order]


@pytest.mark.parametrize("quantity_values", [{}, {"quantity": None}], ids=["missing", "null"])
def test_orders_drinks_requires_quantity(engine, drink, quantity_values):
    with Session(engine) as session:
        session.add(OrderDrink(order=Order(), drink=drink, **quantity_values))
        with pytest.raises(IntegrityError, match="orders_drinks.quantity"):
            session.commit()


def test_orders_drinks_quantity_is_per_order(engine, drink):
    with Session(engine) as session:
        first = OrderDrink(order=Order(), drink=drink, quantity=2)
        second = OrderDrink(order=Order(), drink=drink, quantity=5)
        session.add_all([first, second])
        session.commit()
        first.quantity = 3
        session.commit()
        assert first.quantity == 3
        assert second.quantity == 5
        assert len(drink.orders) == 2


def test_order_allows_no_drinks(engine):
    with Session(engine) as session:
        order = Order()
        session.add(order)
        session.commit()
        assert order.order_drinks == []


def test_drink_requires_order(engine, drink):
    with Session(engine) as session:
        session.add(drink)
        with pytest.raises(ValueError, match="at least one order"):
            session.commit()


@pytest.mark.parametrize("operation", ["remove", "delete_link", "delete_order"])
def test_cannot_remove_last_drink_order(engine, drink, operation):
    with Session(engine) as session:
        link = OrderDrink(order=Order(), drink=drink, quantity=1)
        session.add(link)
        session.commit()
        if operation == "remove":
            link.order.order_drinks.remove(link)
        elif operation == "delete_link":
            session.delete(link)
        else:
            session.delete(link.order)
        with pytest.raises(ValueError, match="at least one order"):
            session.commit()


def test_removing_link_preserves_shared_drink(engine, drink):
    with Session(engine) as session:
        first = OrderDrink(order=Order(), drink=drink, quantity=2)
        second = OrderDrink(order=Order(), drink=drink, quantity=5)
        session.add_all([first, second])
        session.commit()
        first.order.order_drinks.remove(first)
        session.commit()
        assert session.scalars(select(OrderDrink)).all() == [second]
        assert drink.orders == [second.order]


def test_duplicate_order_drink_rejected(engine, drink):
    with Session(engine) as session:
        order = Order(order_drinks=[
            OrderDrink(drink=drink, quantity=1),
            OrderDrink(drink=drink, quantity=2),
        ])
        session.add(order)
        with pytest.raises(IntegrityError, match="UNIQUE"):
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
