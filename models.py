from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String,
    UniqueConstraint, false, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class OrderDrink(Base):
    __tablename__ = "orders_drinks"
    __table_args__ = (
        UniqueConstraint("order_id", "drink_id", name="orders_drinks_unique_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    drink_id: Mapped[int] = mapped_column(ForeignKey("drinks.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="order_drinks")
    drink: Mapped["Drink"] = relationship(back_populates="order_drinks")


class OrderPizza(Base):
    __tablename__ = "orders_pizzas"
    __table_args__ = (
        UniqueConstraint("order_id", "pizza_id", name="orders_pizzas_unique_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    pizza_id: Mapped[int] = mapped_column(ForeignKey("pizzas.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="order_pizzas")
    pizza: Mapped["Pizza"] = relationship(back_populates="order_pizzas")
    order_toppings: Mapped[list["OrderTopping"]] = relationship(
        back_populates="order_pizza", cascade="all, delete-orphan",
    )
    toppings: Mapped[list["Topping"]] = relationship(
        secondary="orders_toppings", viewonly=True,
    )


class OrderTopping(Base):
    __tablename__ = "orders_toppings"
    __table_args__ = (
        UniqueConstraint("order_pizza_id", "topping_id", name="orders_toppings_unique_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    order_pizza_id: Mapped[int] = mapped_column(ForeignKey("orders_pizzas.id"), nullable=False)
    topping_id: Mapped[int] = mapped_column(ForeignKey("toppings.id"), nullable=False)

    order_pizza: Mapped[OrderPizza] = relationship(back_populates="order_toppings")
    topping: Mapped["Topping"] = relationship(back_populates="order_toppings")


# Keep the table available for Core queries.
orders_drinks = OrderDrink.__table__
orders_pizzas = OrderPizza.__table__
orders_toppings = OrderTopping.__table__


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('order_received', 'preparing', 'out_for_delivery', "
            "'ready_for_pickup', 'completed')", name="orders_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default="order_received",
    )
    order_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped["User | None"] = relationship(back_populates="orders", foreign_keys=[user_id])
    order_drinks: Mapped[list[OrderDrink]] = relationship(
        back_populates="order", cascade="all, delete-orphan",
    )
    drinks: Mapped[list["Drink"]] = relationship(
        secondary=orders_drinks, viewonly=True,
    )
    order_pizzas: Mapped[list[OrderPizza]] = relationship(
        back_populates="order", cascade="all, delete-orphan",
    )
    pizzas: Mapped[list["Pizza"]] = relationship(
        secondary=orders_pizzas, viewonly=True,
    )


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
    order_drinks: Mapped[list[OrderDrink]] = relationship(
        back_populates="drink", cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(
        secondary=orders_drinks, viewonly=True,
    )


class Topping(Base):
    __tablename__ = "toppings"
    __table_args__ = (
        CheckConstraint("length(name) <= 50", name="toppings_name_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    order_toppings: Mapped[list[OrderTopping]] = relationship(
        back_populates="topping", cascade="all, delete-orphan",
    )
    order_pizzas: Mapped[list[OrderPizza]] = relationship(
        secondary=orders_toppings, viewonly=True,
    )


class Pizza(Base):
    __tablename__ = "pizzas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    size: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    order_pizzas: Mapped[list[OrderPizza]] = relationship(
        back_populates="pizza", cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(
        secondary=orders_pizzas, viewonly=True,
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('customer', 'staff', 'admin')", name="user_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    orders: Mapped[list[Order]] = relationship(back_populates="user", foreign_keys=[Order.user_id])
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    dine_in_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="customer", server_default="customer")
    # Legacy/seed profiles cannot log in until credentials are provisioned.
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")


class LoginSession(Base):
    __tablename__ = "login_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    csrf_token: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
