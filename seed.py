"""Populate an empty database with sample data: python seed.py.

Existing data is never deleted. Random choices are reproducible.
"""

from decimal import Decimal
import random

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from database import DATABASE_PATH, engine
from models import (
    Base, Drink, Inventory, Order, OrderDrink, OrderPizza, OrderTopping,
    Pizza, Topping, User,
)


CUSTOMER_NAMES = (
    "Alex Morgan", "Jordan Lee", "Taylor Brooks", "Casey Rivera",
    "Morgan Patel", "Riley Chen", "Jamie Wilson", "Avery Garcia",
    "Cameron Davis", "Quinn Robinson", "Dakota Clark", "Reese Lewis",
    "Parker Walker", "Skyler Hall", "Rowan Allen", "Emerson Young",
    "Finley King", "Sage Wright", "Charlie Scott", "Drew Adams",
)
TOPPING_NAMES = (
    "Mozzarella", "Pepperoni", "Sausage", "Mushrooms",
    "Onions", "Green peppers", "Black olives", "Basil",
)


def seed_database(bind: Engine = engine) -> dict[str, int]:
    """Seed all tables in one transaction; reject databases containing data."""
    Base.metadata.create_all(bind)
    rng = random.Random(42)
    with bind.begin() as connection:
        for table in Base.metadata.sorted_tables:
            # Select only the ID, so older orders schemas can be checked too.
            if connection.execute(select(table.c.id).limit(1)).first():
                raise ValueError(
                    f"Database already contains data in {table.name}; "
                    "seeding requires an empty database. No sample data was added."
                )

        # create_all does not update tables created before the customer link.
        columns = {column["name"] for column in inspect(connection).get_columns("orders")}
        if "user_id" not in columns:
            connection.execute(text(
                "ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES users(id)"
            ))

        with Session(bind=connection) as session:
            customers = [
                User(
                    name=name,
                    address=f"{100 + i} Maple Street, Springfield, IL 62701",
                    phone_number=f"217-555-{100 + i:04d}",
                    email=f"{name.lower().replace(' ', '.')}@example.com",
                    dine_in_name=name.split()[0],
                    admin=False,
                )
                for i, name in enumerate(CUSTOMER_NAMES)
            ]
            toppings = [Topping(name=name) for name in TOPPING_NAMES]
            drinks = [
                Drink(name=name, size=size, price=Decimal(price))
                for name in ("Cola", "Lemonade", "Iced tea", "Sparkling water")
                for size, price in (("small", "1.50"), ("medium", "2.00"), ("large", "2.50"))
            ]
            inventory = [
                Inventory(name=name, quantity=Decimal(quantity), unit=unit)
                for name, quantity, unit in (
                    ("Flour", "100.0", "kg"), ("Tomato sauce", "60.0", "liters"),
                    ("Mozzarella", "45.0", "kg"), ("Pepperoni", "25.0", "kg"),
                    ("Sausage", "20.0", "kg"), ("Mushrooms", "15.0", "kg"),
                    ("Onions", "18.0", "kg"), ("Green peppers", "12.0", "kg"),
                    ("Black olives", "10.0", "kg"), ("Basil", "2.5", "kg"),
                    ("Pizza boxes", "500.0", "pieces"),
                    ("Drink cups", "600.0", "pieces"),
                )
            ]
            # Guarantee every customer has an order, then vary the remaining 80.
            owners = customers + rng.choices(customers, k=80)
            rng.shuffle(owners)
            orders = []
            for index, customer in enumerate(owners):
                order = Order(user=customer)
                for _ in range(rng.randint(1, 3)):
                    size, price = rng.choice((
                        ("small", "8.00"), ("medium", "11.00"), ("large", "14.00"),
                    ))
                    order.order_pizzas.append(OrderPizza(
                        pizza=Pizza(size=size, price=Decimal(price)),
                        order_toppings=[
                            OrderTopping(topping=topping)
                            for topping in rng.sample(toppings, rng.randint(1, 4))
                        ],
                    ))
                # Cycle the first drink to guarantee every drink has an order.
                first_drink = drinks[index % len(drinks)]
                selected = [first_drink] + rng.sample(
                    [drink for drink in drinks if drink is not first_drink],
                    rng.randint(0, 2),
                )
                order.order_drinks = [
                    OrderDrink(drink=drink, quantity=rng.randint(1, 4))
                    for drink in selected
                ]
                orders.append(order)

            session.add_all(customers + toppings + drinks + inventory + orders)
            session.flush()
            counts = {
                table.name: len(session.execute(select(table.c.id)).all())
                for table in Base.metadata.sorted_tables
            }
    return counts


if __name__ == "__main__":
    try:
        counts = seed_database()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Seeded {DATABASE_PATH}")
    for table_name, count in counts.items():
        print(f"  {table_name}: {count}")
