from decimal import Decimal

import pytest

from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Base, Drink, Inventory, Order, OrderDrink, OrderPizza, OrderTopping, Pizza, Topping, User


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


def test_order_database_defaults_and_stable_time(engine):
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO orders DEFAULT VALUES"))
        row = connection.execute(text("SELECT status, order_time FROM orders")).one()
        assert row.status == "order_received"
        assert row.order_time == connection.scalar(text("SELECT CURRENT_TIMESTAMP"))
        connection.execute(text("UPDATE orders SET status = 'preparing'"))
        assert connection.scalar(text("SELECT order_time FROM orders")) == row.order_time


@pytest.mark.parametrize("status", [
    "order_received", "preparing", "out_for_delivery", "ready_for_pickup", "completed",
])
def test_order_allowed_statuses(engine, status):
    with Session(engine) as session:
        order = Order(status=status)
        session.add(order)
        session.commit()
        assert order.status == status
        assert order.order_time is not None


@pytest.mark.parametrize("values", [
    "'unknown', CURRENT_TIMESTAMP", "NULL, CURRENT_TIMESTAMP", "'completed', NULL",
])
def test_order_invalid_status_or_time_rejected(engine, values):
    with engine.begin() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(text(f"INSERT INTO orders (status, order_time) VALUES ({values})"))


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
            return user.id, user.role, user.phone_number

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


def test_customer_orders_only_drinks(engine, add_user, drink):
    user_id, _, _ = add_user()
    with Session(engine) as session:
        order = Order(
            user=session.get(User, user_id),
            order_drinks=[OrderDrink(drink=drink, quantity=2)],
        )
        session.add(order)
        session.commit()
        order_id, drink_id = order.id, drink.id

    with Session(engine) as session:
        order = session.get(Order, order_id)
        customer = session.get(User, user_id)
        assert order.user is customer
        assert customer.orders == [order]
        assert len(order.order_drinks) == 1
        assert order.order_drinks[0].drink_id == drink_id
        assert order.order_drinks[0].quantity == 2
        assert order.drinks == [session.get(Drink, drink_id)]
        assert order.order_pizzas == []
        assert order.pizzas == []


def test_drink_allows_no_order(engine, drink):
    with Session(engine) as session:
        session.add(drink)
        session.commit()


@pytest.mark.parametrize("operation", ["remove", "delete_link", "delete_order"])
def test_can_remove_last_drink_order(engine, drink, operation):
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
        session.add(OrderPizza(quantity=1, order=Order(), pizza=pizza))
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
        session.add(OrderPizza(quantity=1, order=Order(), pizza=Pizza(**values)))
        with pytest.raises(IntegrityError):
            session.commit()


def test_generated_id_default_role_and_optional_email(add_user):
    first_id, role, phone = add_user()
    second_id, _, _ = add_user()
    assert isinstance(first_id, int)
    assert first_id != second_id
    assert role == "customer"
    assert phone == "+1 0123"


def test_unique_email(add_user):
    add_user(email="alex@example.com")
    with pytest.raises(IntegrityError):
        add_user(email="alex@example.com")


def test_admin_role(add_user):
    assert add_user(role="admin")[1] == "admin"


@pytest.mark.parametrize("invalid", ["owner", None])
def test_database_rejects_invalid_role(engine, add_user, invalid):
    user_id, _, _ = add_user()
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("UPDATE users SET role = :value WHERE id = :id"),
                               {"value": invalid, "id": user_id})


@pytest.fixture
def pizza():
    return Pizza(size="Small", price=Decimal("5.00"))


def test_order_allows_no_pizzas(engine):
    with Session(engine) as session:
        order = Order()
        session.add(order)
        session.commit()
        assert order.order_pizzas == []


def test_customer_orders_only_pizzas(engine, add_user, pizza):
    user_id, _, _ = add_user()
    with Session(engine) as session:
        order = Order(
            user=session.get(User, user_id),
            order_pizzas=[OrderPizza(quantity=1, pizza=pizza)],
        )
        session.add(order)
        session.commit()
        order_id, pizza_id = order.id, pizza.id

    with Session(engine) as session:
        order = session.get(Order, order_id)
        customer = session.get(User, user_id)
        assert order.user is customer
        assert customer.orders == [order]
        assert len(order.order_pizzas) == 1
        assert order.order_pizzas[0].pizza_id == pizza_id
        assert order.pizzas == [session.get(Pizza, pizza_id)]
        assert order.order_drinks == []
        assert order.drinks == []


def test_pizza_allows_no_order(engine, pizza):
    with Session(engine) as session:
        session.add(pizza)
        session.commit()


@pytest.mark.parametrize("operation", ["remove", "delete_link", "delete_order"])
def test_can_remove_last_pizza_order(engine, pizza, operation):
    with Session(engine) as session:
        link = OrderPizza(quantity=1, order=Order(), pizza=pizza)
        session.add(link)
        session.commit()
        if operation == "remove":
            link.order.order_pizzas.remove(link)
        elif operation == "delete_link":
            session.delete(link)
        else:
            session.delete(link.order)
        session.commit()


def test_removing_link_preserves_shared_pizza(engine, pizza):
    with Session(engine) as session:
        first = OrderPizza(quantity=1, order=Order(), pizza=pizza)
        second = OrderPizza(quantity=1, order=Order(), pizza=pizza)
        session.add_all([first, second])
        session.commit()
        first.order.order_pizzas.remove(first)
        session.commit()
        assert session.scalars(select(OrderPizza)).all() == [second]
        assert pizza.orders == [second.order]


def test_duplicate_order_pizza_rejected(engine, pizza):
    with Session(engine) as session:
        order = Order(order_pizzas=[
            OrderPizza(quantity=1, pizza=pizza),
            OrderPizza(quantity=1, pizza=pizza),
        ])
        session.add(order)
        with pytest.raises(IntegrityError, match="UNIQUE"):
            session.commit()



def test_orders_pizzas_many_to_many(engine, pizza):
    with Session(engine) as session:
        other_pizza = Pizza(size="Large", price=Decimal("10.00"))
        first_order = Order(order_pizzas=[
            OrderPizza(quantity=1, pizza=pizza), OrderPizza(quantity=1, pizza=other_pizza),
        ])
        second_order = Order(order_pizzas=[OrderPizza(quantity=1, pizza=pizza)])
        session.add_all([first_order, second_order])
        session.commit()
        ids = first_order.id, second_order.id, pizza.id
    with Session(engine) as session:
        first = session.get(Order, ids[0])
        second = session.get(Order, ids[1])
        shared = session.get(Pizza, ids[2])
        assert len(first.pizzas) == 2
        assert second.pizzas == [shared]
        assert set(shared.orders) == {first, second}
        links = session.scalars(select(OrderPizza)).all()
        assert len(links) == 3
        assert len({link.id for link in links}) == 3
        for link in links:
            assert isinstance(link.id, int)
            assert link.order_id == link.order.id
            assert link.pizza_id == link.pizza.id


@pytest.mark.parametrize("missing_column", ["order_id", "pizza_id"])
def test_order_pizza_requires_both_foreign_keys(engine, missing_column):
    values = {"order_id": 1, "pizza_id": 1}
    values.pop(missing_column)
    with engine.begin() as connection:
        with pytest.raises(IntegrityError, match="NOT NULL"):
            connection.execute(OrderPizza.__table__.insert().values(**values))


@pytest.mark.parametrize("count", [0, 1, 3])
def test_order_pizza_toppings(engine, pizza, count):
    with Session(engine) as session:
        item = OrderPizza(quantity=1, order=Order(), pizza=pizza, order_toppings=[
            OrderTopping(topping=Topping(name=f"Topping {i}")) for i in range(count)
        ])
        session.add(item)
        session.commit()
        item_id = item.id
    with Session(engine) as session:
        item = session.get(OrderPizza, item_id)
        assert len(item.toppings) == count
        assert len(item.order_toppings) == count
        assert len({link.id for link in item.order_toppings}) == count
        for link in item.order_toppings:
            assert isinstance(link.id, int)
            assert link.order_pizza_id == item.id
            assert link.topping_id == link.topping.id
            assert link.topping.order_pizzas == [item]


def test_toppings_are_specific_to_order_pizza(engine, pizza):
    with Session(engine) as session:
        shared = Topping(name="Cheese")
        extra = Topping(name="Olives")
        first = OrderPizza(quantity=1, order=Order(), pizza=pizza, order_toppings=[
            OrderTopping(topping=shared), OrderTopping(topping=extra),
        ])
        second = OrderPizza(quantity=1, order=Order(), pizza=pizza, order_toppings=[
            OrderTopping(topping=shared),
        ])
        session.add_all([first, second])
        session.commit()
        assert set(first.toppings) == {shared, extra}
        assert second.toppings == [shared]
        assert set(shared.order_pizzas) == {first, second}
        first.order_toppings.clear()
        session.commit()
        assert first.toppings == []
        assert second.toppings == [shared]
        assert set(session.scalars(select(Topping))) == {shared, extra}


@pytest.mark.parametrize("target", ["order_pizza", "topping"])
def test_order_topping_cleanup(engine, pizza, target):
    with Session(engine) as session:
        topping = Topping(name="Cheese")
        first = OrderPizza(quantity=1, order=Order(), pizza=pizza, order_toppings=[
            OrderTopping(topping=topping),
        ])
        second = OrderPizza(quantity=1, order=Order(), pizza=pizza)
        session.add_all([first, second])
        session.commit()
        session.delete(first if target == "order_pizza" else topping)
        session.commit()
        assert session.scalars(select(OrderTopping)).all() == []
        assert session.get(Pizza, pizza.id) is pizza
        if target == "order_pizza":
            assert session.get(Topping, topping.id) is topping
        else:
            assert session.get(OrderPizza, first.id) is first


def test_duplicate_order_topping_rejected(engine, pizza):
    with Session(engine) as session:
        topping = Topping(name="Cheese")
        session.add(OrderPizza(quantity=1, order=Order(), pizza=pizza, order_toppings=[
            OrderTopping(topping=topping), OrderTopping(topping=topping),
        ]))
        with pytest.raises(IntegrityError, match="UNIQUE"):
            session.commit()


@pytest.mark.parametrize("missing_column", ["order_pizza_id", "topping_id"])
def test_order_topping_requires_both_foreign_keys(engine, missing_column):
    values = {"order_pizza_id": 1, "topping_id": 1}
    values.pop(missing_column)
    with engine.begin() as connection:
        with pytest.raises(IntegrityError, match="NOT NULL"):
            connection.execute(OrderTopping.__table__.insert().values(**values))
