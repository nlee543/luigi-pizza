from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, String, false
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity = round(quantity, 1)", name="inventory_quantity_scale"),
        CheckConstraint("length(unit) <= 10", name="inventory_unit_length"),
        CheckConstraint("length(name) <= 50", name="inventory_name_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 1), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class Drink(Base):
    __tablename__ = "drinks"
    __table_args__ = (
        CheckConstraint("size IN ('small', 'medium', 'large')", name="drinks_size"),
        CheckConstraint("length(name) <= 50", name="drinks_name_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    size: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class Topping(Base):
    __tablename__ = "toppings"
    __table_args__ = (
        CheckConstraint("length(name) <= 50", name="toppings_name_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class Pizza(Base):
    __tablename__ = "pizzas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    size: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    dine_in_name: Mapped[str] = mapped_column(String, nullable=False)
    admin: Mapped[bool] = mapped_column(
        Boolean(create_constraint=True, name="admin_boolean"),
        nullable=False,
        default=False,
        server_default=false(),
    )
