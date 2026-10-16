# Luigi's Pizza database

Create the environment and initialize SQLite from PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe database.py
```

The database is saved as `luigi_pizza.db` beside `database.py`.

Run the tests with `.venv/Scripts/python.exe -m pytest -v`.

Running initialization again preserves existing tables and data; it does not
migrate existing schemas.

The `users` table has an automatically assigned integer primary key (`id`),
required text fields (`name`, `address`, `phone_number`, `dine_in_name`),
an optional unique `email`, and a required boolean `admin` defaulting to false.
Phone numbers are text to preserve leading zeros, plus signs, and formatting.
Use `None` for missing emails; multiple users may omit email.
SQLite stores booleans as 0/1; a CHECK constraint rejects other values.

The `pizzas` table has an automatically assigned integer primary key (`id`),
a required text `size`, and a required `price` mapped as `Numeric(10, 2)`.
Use Python `Decimal` values for prices, for example `Decimal("5.00")`.

`OrderPizza` maps `orders_pizzas` with an automatically assigned integer `id`
and required `order_id` and `pizza_id` foreign keys. Each order/pizza pair is
unique. Create entries with `OrderPizza(order=order, pizza=pizza)` or append
them to `order.order_pizzas`. Both `Order.order_pizzas` and
`Pizza.order_pizzas` expose the association objects. `Order.pizzas` and
`Pizza.orders` are read-only convenience relationships that reload after
expiration or commit.

An order may have no pizzas or many pizzas. ORM relationship validation
requires every surviving pizza to belong to at least one order, including
when removing links or deleting orders. Direct SQL and bulk operations bypass
this validation.

The `toppings` table has an automatically assigned integer primary key (`id`)
and a required `name` of up to 50 characters. A CHECK constraint enforces the
length limit because SQLite does not enforce `String(50)` by itself.

`OrderTopping` maps `orders_toppings` with an automatically assigned integer
primary key `id`, a required `order_pizza_id` referencing `orders_pizzas.id`,
and a required `topping_id` referencing `toppings.id`. Each pair is unique.
An order's pizza entry can have zero or many toppings, and a topping can be
reused across entries. Toppings are specific to the order's pizza entry.

Add a topping with
`order_pizza.order_toppings.append(OrderTopping(topping=topping))`.
Use `OrderPizza.order_toppings` and `Topping.order_toppings` to edit links;
`OrderPizza.toppings` and `Topping.order_pizzas` are read-only convenience
relationships that reload after expiration or commit. Removing links keeps
the toppings themselves; ORM deletion of either endpoint cleans up its links.

The `drinks` table has an automatically assigned integer primary key (`id`),
a required `size` restricted to lowercase `small`, `medium`, or `large`,
a required `price` mapped as `Numeric(10, 2)`, and a required `name` of up to
50 characters. CHECK constraints enforce the size and name length limits.

`OrderDrink` maps the `orders_drinks` table with an integer primary key `id`,
required `order_id` and `drink_id` foreign keys, and a required integer `quantity`.
Each order/drink pair is unique. Add and update entries through `order_drinks`:

```python
from decimal import Decimal
from models import Drink, Order, OrderDrink

with SessionLocal.begin() as session:
    order = Order(order_drinks=[
        OrderDrink(
            drink=Drink(size="small", price=Decimal("1.25"), name="Cola"),
            quantity=2,
        ),
    ])
    session.add(order)
```

`Order.drinks` and `Drink.orders` are read-only convenience relationships;
after editing association entries, expire or refresh these collections to
reload them (committing expires them by default). Orders may have no drinks.
ORM relationship validation requires each surviving drink to have at least
one order; direct SQL and bulk operations bypass this validation.

The `inventory` table has an automatically assigned integer primary key (`id`),
a required `quantity` mapped as `Numeric(10, 1)`, a required `unit` of up to
10 characters, and a required `name` of up to 50 characters. CHECK constraints
enforce both text limits and reject quantities with more than one decimal place.
Use `Decimal` for quantities, for example `Decimal("12.3")`.

Example:

```python
from database import SessionLocal, init_db
from models import User

init_db()
with SessionLocal.begin() as session:
    session.add(User(
        name="Alex Smith",
        address="123 Main Street",
        phone_number="555-0100",
        email="alex@example.com",
        dine_in_name="Alex",
    ))
```
