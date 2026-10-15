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

The `toppings` table has an automatically assigned integer primary key (`id`)
and a required `name` of up to 50 characters. A CHECK constraint enforces the
length limit because SQLite does not enforce `String(50)` by itself.

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
