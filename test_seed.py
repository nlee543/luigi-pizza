from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from models import Order, Pizza, User
from seed import seed_database


@pytest.mark.parametrize("legacy", [False, True])
def test_seed_populates_all_tables_and_assigns_customers(legacy):
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys = ON"))
        if legacy:
            connection.execute(text("CREATE TABLE orders (id INTEGER PRIMARY KEY NOT NULL)"))
    try:
        counts = seed_database(engine)
        assert counts["users"] == 20
        assert counts["orders"] == 100
        assert counts["pizzas"] == 3
        assert all(count > 0 for count in counts.values())
        with Session(engine) as session:
            pizzas = session.scalars(select(Pizza)).all()
            assert {(pizza.size, pizza.price) for pizza in pizzas} == {
                ("small", Decimal("5.00")),
                ("medium", Decimal("7.00")),
                ("large", Decimal("9.00")),
            }
            pizza_ids = {pizza.id for pizza in pizzas}
            assert all(pizza.order_pizzas for pizza in pizzas)
            assert all(user.orders for user in session.scalars(select(User)))
            for order in session.scalars(select(Order)):
                assert order.user is not None
                assert order.order_pizzas
                assert all(link.pizza_id in pizza_ids for link in order.order_pizzas)
                assert order.order_drinks
                assert all(link.quantity > 0 for link in order.order_drinks)
            assert session.execute(text("PRAGMA foreign_key_check")).all() == []
        with pytest.raises(ValueError, match="already contains data"):
            seed_database(engine)
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(Order)) == 100
            assert session.scalar(select(func.count()).select_from(User)) == 20
            assert session.scalar(select(func.count()).select_from(Pizza)) == 3
    finally:
        engine.dispose()
