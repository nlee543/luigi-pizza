from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String,
    UniqueConstraint, event, false, inspect,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


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

    order: Mapped["Order"] = relationship(back_populates="order_pizzas")
    pizza: Mapped["Pizza"] = relationship(back_populates="order_pizzas")


# Keep the table available for Core queries.
orders_drinks = OrderDrink.__table__
orders_pizzas = OrderPizza.__table__


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
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


@event.listens_for(Session, "before_flush")
def validate_drink_orders(session, flush_context, instances):
    """Require an order for each drink saved through ORM relationships."""
    drinks = {
        obj for obj in session.new.union(session.dirty) if isinstance(obj, Drink)
    }
    for obj in session.new.union(session.dirty).union(session.deleted):
        if isinstance(obj, Order):
            links = list(obj.order_drinks)
            links.extend(inspect(obj).attrs.order_drinks.history.deleted)
        elif isinstance(obj, OrderDrink):
            links = [obj]
            drinks.update(inspect(obj).attrs.drink.history.deleted)
        else:
            continue
        drinks.update(link.drink for link in links if link.drink is not None)
    for drink in drinks:
        if drink not in session.deleted and not any(
            link not in session.deleted
            and link.order is not None
            and link.order not in session.deleted
            and link.drink is drink
            for link in drink.order_drinks
        ):
            raise ValueError("A drink must belong to at least one order.")


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
    order_pizzas: Mapped[list[OrderPizza]] = relationship(
        back_populates="pizza", cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(
        secondary=orders_pizzas, viewonly=True,
    )


@event.listens_for(Session, "before_flush")
def validate_pizza_orders(session, flush_context, instances):
    """Require an order for each pizza saved through ORM relationships."""
    pizzas = {
        obj for obj in session.new.union(session.dirty) if isinstance(obj, Pizza)
    }
    for obj in session.new.union(session.dirty).union(session.deleted):
        if isinstance(obj, Order):
            links = list(obj.order_pizzas)
            links.extend(inspect(obj).attrs.order_pizzas.history.deleted)
        elif isinstance(obj, OrderPizza):
            links = [obj]
            pizzas.update(inspect(obj).attrs.pizza.history.deleted)
        else:
            continue
        pizzas.update(link.pizza for link in links if link.pizza is not None)
    for pizza in pizzas:
        if pizza not in session.deleted and not any(
            link not in session.deleted
            and link.order is not None
            and link.order not in session.deleted
            and link.pizza is pizza
            for link in pizza.order_pizzas
        ):
            raise ValueError("A pizza must belong to at least one order.")


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
