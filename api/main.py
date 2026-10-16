"""Pizza ordering HTTP API. Run with: uvicorn api.main:app."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal
import os
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import URL, create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, Drink, Inventory, Order, OrderDrink, OrderPizza, OrderTopping, Pizza, Topping, User


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


Text = Annotated[str, Field(min_length=1)]
Name = Annotated[str, Field(min_length=1, max_length=50)]
Money = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
ID = Annotated[int, Field(gt=0, strict=True)]
Quantity = Annotated[int, Field(gt=0, strict=True)]


class UserInput(Schema):
    name: Text
    address: Text
    phone_number: Text
    email: str | None = None
    dine_in_name: Text
    admin: bool = False


class UserOutput(UserInput):
    id: int


class PizzaInput(Schema):
    size: Text
    price: Money


class PizzaOutput(PizzaInput):
    id: int


class DrinkInput(Schema):
    name: Name
    size: Literal["small", "medium", "large"]
    price: Money


class DrinkOutput(DrinkInput):
    id: int


class ToppingInput(Schema):
    name: Name


class ToppingOutput(ToppingInput):
    id: int


class InventoryInput(Schema):
    name: Name
    unit: Annotated[str, Field(min_length=1, max_length=10)]
    quantity: Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=1)]


class InventoryOutput(InventoryInput):
    id: int


class DrinkLine(Schema):
    drink_id: ID
    quantity: Quantity = 1


class PizzaLine(Schema):
    pizza_id: ID
    quantity: Quantity = 1
    topping_ids: list[ID] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_toppings(self):
        if len(set(self.topping_ids)) != len(self.topping_ids):
            raise ValueError("Topping IDs must be unique within a pizza.")
        return self


class OrderInput(Schema):
    status: Literal["order_received", "preparing", "out_for_delivery", "ready_for_pickup", "completed"] = "order_received"
    user_id: ID | None = None
    drinks: list[DrinkLine] = Field(default_factory=list)
    pizzas: list[PizzaLine] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lines(self):
        if not self.drinks and not self.pizzas:
            raise ValueError("An order must contain at least one drink or pizza.")
        for lines, key in ((self.drinks, "drink_id"), (self.pizzas, "pizza_id")):
            ids = [getattr(line, key) for line in lines]
            if len(set(ids)) != len(ids):
                raise ValueError(f"Duplicate {key}; use quantity instead.")
        return self


class OrderOutput(OrderInput):
    id: int
    order_time: datetime


def get_session(request: Request):
    with request.app.state.sessions() as session:
        yield session


DB = Annotated[Session, Depends(get_session)]


def get_record(session, model, record_id):
    record = session.get(model, record_id)
    if record is None:
        raise HTTPException(404, f"{model.__name__} {record_id} not found")
    return record


def commit(session):
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Operation conflicts with existing data or database constraints.") from None


def order_output(order):
    return OrderOutput(
        id=order.id, user_id=order.user_id,
        status=order.status, order_time=order.order_time.replace(tzinfo=timezone.utc),
        drinks=[DrinkLine(drink_id=line.drink_id, quantity=line.quantity) for line in order.order_drinks],
        pizzas=[PizzaLine(pizza_id=line.pizza_id, quantity=line.quantity,
                          topping_ids=[t.topping_id for t in line.order_toppings])
                for line in order.order_pizzas],
    )


def set_order(session, order, data):
    # Resolve every reference before changing anything; the request is atomic.
    user = get_record(session, User, data.user_id) if data.user_id is not None else None
    drinks = [(line, get_record(session, Drink, line.drink_id)) for line in data.drinks]
    pizzas = [(line, get_record(session, Pizza, line.pizza_id),
               [get_record(session, Topping, tid) for tid in line.topping_ids]) for line in data.pizzas]
    session.add(order)
    order.user = user
    if "status" in data.model_fields_set:
        order.status = data.status
    # Flush deletions before recreating links to avoid unique-pair conflicts.
    order.order_drinks.clear()
    order.order_pizzas.clear()
    session.flush()
    with session.no_autoflush:
        order.order_drinks = [OrderDrink(drink=drink, quantity=line.quantity) for line, drink in drinks]
        order.order_pizzas = [OrderPizza(pizza=pizza, quantity=line.quantity,
                                        order_toppings=[OrderTopping(topping=t) for t in toppings])
                              for line, pizza, toppings in pizzas]


def register_crud(app, path, model, input_schema, output_schema):
    def create(data: input_schema, session: DB):
        record = model(**data.model_dump())
        session.add(record)
        commit(session)
        return record

    def list_records(session: DB, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
        return session.scalars(select(model).order_by(model.id).offset(offset).limit(limit)).all()

    def read(record_id: int, session: DB):
        return get_record(session, model, record_id)

    def update(record_id: int, data: input_schema, session: DB):
        record = get_record(session, model, record_id)
        for key, value in data.model_dump().items():
            setattr(record, key, value)
        commit(session)
        return record

    def delete(record_id: int, session: DB):
        record = get_record(session, model, record_id)
        # Preserve order history instead of silently removing ordered products.
        links = {Drink: "order_drinks", Pizza: "order_pizzas", Topping: "order_toppings"}
        if model in links and getattr(record, links[model]):
            raise HTTPException(409, "Item is referenced by an order; remove the order reference first.")
        session.delete(record)
        commit(session)
        return Response(status_code=204)

    for endpoint, method, suffix, response, status in (
        (create, "POST", "", output_schema, 201),
        (list_records, "GET", "", list[output_schema], 200),
        (read, "GET", "/{record_id}", output_schema, 200),
        (update, "PUT", "/{record_id}", output_schema, 200),
        (delete, "DELETE", "/{record_id}", None, 204),
    ):
        app.add_api_route(f"/{path}{suffix}", endpoint, methods=[method],
                          response_model=response, status_code=status, tags=[path],
                          name=f"{method.lower()}_{path}{'_item' if suffix else ''}")


def create_app(connection_string=None):
    @asynccontextmanager
    async def lifespan(app):
        url = connection_string or os.getenv("CONNECTIONSTRING") or URL.create(
            "sqlite", database=str(Path(__file__).resolve().parents[1] / "luigi_pizza.db"))
        options = {"connect_args": {"check_same_thread": False}}
        if str(url) in ("sqlite://", "sqlite:///:memory:"):
            options["poolclass"] = StaticPool
        engine = create_engine(url, **options)
        if engine.dialect.name != "sqlite":
            engine.dispose()
            raise ValueError("CONNECTIONSTRING must be a SQLite SQLAlchemy URL.")

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        try:
            Base.metadata.create_all(engine)
            app.state.sessions = sessionmaker(bind=engine)
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Luigi's Pizza API", lifespan=lifespan)
    for args in (
        ("users", User, UserInput, UserOutput),
        ("drinks", Drink, DrinkInput, DrinkOutput),
        ("pizzas", Pizza, PizzaInput, PizzaOutput),
        ("toppings", Topping, ToppingInput, ToppingOutput),
        ("inventory", Inventory, InventoryInput, InventoryOutput),
    ):
        register_crud(app, *args)

    @app.post("/orders", response_model=OrderOutput, status_code=201, tags=["orders"])
    def create_order(data: OrderInput, session: DB):
        order = Order()
        set_order(session, order, data)
        commit(session)
        return order_output(order)

    @app.get("/orders", response_model=list[OrderOutput], tags=["orders"])
    def list_orders(session: DB, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
        return [order_output(order) for order in session.scalars(select(Order).order_by(Order.id).offset(offset).limit(limit))]

    @app.get("/orders/{record_id}", response_model=OrderOutput, tags=["orders"])
    def read_order(record_id: int, session: DB):
        return order_output(get_record(session, Order, record_id))

    @app.put("/orders/{record_id}", response_model=OrderOutput, tags=["orders"])
    def update_order(record_id: int, data: OrderInput, session: DB):
        order = get_record(session, Order, record_id)
        set_order(session, order, data)
        commit(session)
        return order_output(order)

    @app.delete("/orders/{record_id}", status_code=204, tags=["orders"])
    def delete_order(record_id: int, session: DB):
        session.delete(get_record(session, Order, record_id))
        commit(session)
        return Response(status_code=204)

    return app


app = create_app()
