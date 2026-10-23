"""Pizza ordering HTTP API. Run with: uvicorn api.main:app."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal
import os
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import URL, create_engine, event, inspect, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth import (Admin, CurrentUser, DB, Staff, UserOutput, commit, require_staff, router as auth_router)
from starlette.responses import JSONResponse

from models import Base, Drink, Inventory, Order, OrderDrink, OrderPizza, OrderTopping, Pizza, Topping, User


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


Text = Annotated[str, Field(min_length=1)]
Name = Annotated[str, Field(min_length=1, max_length=50)]
Money = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
ID = Annotated[int, Field(gt=0, strict=True)]
Quantity = Annotated[int, Field(gt=0, strict=True)]


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


OrderStatus = Literal["order_received", "preparing", "out_for_delivery", "ready_for_pickup", "completed"]


class OrderInput(Schema):
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


class StaffOrderInput(OrderInput):
    user_id: ID


class StatusInput(Schema):
    status: OrderStatus


class OrderOutput(OrderInput):
    id: int
    user_id: int | None
    created_by_user_id: int | None
    status: OrderStatus
    order_time: datetime


def get_record(session, model, record_id):
    record = session.get(model, record_id)
    if record is None:
        raise HTTPException(404, f"{model.__name__} {record_id} not found")
    return record


def order_output(order):
    return OrderOutput(
        id=order.id, user_id=order.user_id, created_by_user_id=order.created_by_user_id,
        status=order.status, order_time=order.order_time.replace(tzinfo=timezone.utc),
        drinks=[DrinkLine(drink_id=line.drink_id, quantity=line.quantity) for line in order.order_drinks],
        pizzas=[PizzaLine(pizza_id=line.pizza_id, quantity=line.quantity,
                          topping_ids=[t.topping_id for t in line.order_toppings])
                for line in order.order_pizzas],
    )


def set_order(session, order, data):
    # Resolve every reference before changing anything; the request is atomic.
    drinks = [(line, get_record(session, Drink, line.drink_id)) for line in data.drinks]
    pizzas = [(line, get_record(session, Pizza, line.pizza_id),
               [get_record(session, Topping, tid) for tid in line.topping_ids]) for line in data.pizzas]
    session.add(order)
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
                          dependencies=[Depends(require_staff)] if method != "GET" or path == "inventory" else [],
                          name=f"{method.lower()}_{path}{'_item' if suffix else ''}")


def create_app(connection_string=None, *, cookie_secure=None, allowed_origin=None):
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
            schema = inspect(engine)
            tables = schema.get_table_names()
            if "users" in tables:
                columns = {c["name"] for c in schema.get_columns("users")}
                if not {"role", "password_hash", "must_change_password", "active"} <= columns:
                    raise RuntimeError("Run migrate_auth.py on this database before starting the API.")
            if "orders" in tables and "created_by_user_id" not in {c["name"] for c in schema.get_columns("orders")}:
                raise RuntimeError("Run migrate_auth.py on this database before starting the API.")
            Base.metadata.create_all(engine)
            app.state.sessions = sessionmaker(bind=engine)
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Luigi's Pizza API", lifespan=lifespan)
    app.state.cookie_secure = cookie_secure if cookie_secure is not None else os.getenv("COOKIE_SECURE", "true").lower() == "true"
    app.state.allowed_origin = (allowed_origin or os.getenv("APP_ORIGIN", "http://127.0.0.1:8000")).rstrip("/")

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Never echo passwords or whole registration bodies in validation errors.
        errors = [{key: error[key] for key in ("type", "loc", "msg")} for error in exc.errors()]
        return JSONResponse({"detail": errors}, status_code=422)

    @app.middleware("http")
    async def browser_security(request: Request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin and origin != app.state.allowed_origin:
                return JSONResponse({"detail": "Request origin is not allowed."}, status_code=403)
        response = await call_next(request)
        # Authenticated responses contain private customer/order data.
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    app.include_router(auth_router)
    for args in (
        ("drinks", Drink, DrinkInput, DrinkOutput),
        ("pizzas", Pizza, PizzaInput, PizzaOutput),
        ("toppings", Topping, ToppingInput, ToppingOutput),
        ("inventory", Inventory, InventoryInput, InventoryOutput),
    ):
        register_crud(app, *args)

    @app.get("/staff/customers", response_model=list[UserOutput], tags=["customers"])
    def find_customers(session: DB, staff: Staff, q: str = Query("", max_length=254),
                       offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
        statement = select(User).where(User.role == "customer")
        if q:
            statement = statement.where(User.email.contains(q.strip().lower(), autoescape=True) |
                                        User.phone_number.contains(q, autoescape=True) |
                                        User.name.contains(q, autoescape=True))
        return session.scalars(statement.order_by(User.id).offset(offset).limit(limit)).all()

    @app.get("/admin/users", response_model=list[UserOutput], tags=["users"])
    def list_users(session: DB, admin: Admin, offset: int = Query(0, ge=0),
                   limit: int = Query(100, ge=1, le=1000)):
        return session.scalars(select(User).order_by(User.id).offset(offset).limit(limit)).all()

    @app.post("/orders", response_model=OrderOutput, status_code=201, tags=["orders"])
    def create_order(data: OrderInput, session: DB, user: CurrentUser):
        if user.role != "customer":
            raise HTTPException(403, "Use /staff/orders to select a customer.")
        order = Order(user_id=user.id, created_by_user_id=user.id)
        set_order(session, order, data)
        commit(session)
        return order_output(order)

    @app.post("/staff/orders", response_model=OrderOutput, status_code=201, tags=["orders"])
    def staff_create_order(data: StaffOrderInput, session: DB, staff: Staff):
        customer = get_record(session, User, data.user_id)
        if customer.role != "customer" or not customer.active or not customer.password_hash:
            raise HTTPException(409, "Select an active, registered customer.")
        order = Order(user_id=customer.id, created_by_user_id=staff.id)
        set_order(session, order, data)
        commit(session)
        return order_output(order)

    @app.get("/orders", response_model=list[OrderOutput], tags=["orders"])
    def list_orders(session: DB, user: CurrentUser, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
        statement = select(Order)
        if user.role == "customer":
            statement = statement.where(Order.user_id == user.id)
        return [order_output(order) for order in session.scalars(statement.order_by(Order.id).offset(offset).limit(limit))]

    @app.get("/orders/{record_id}", response_model=OrderOutput, tags=["orders"])
    def read_order(record_id: int, session: DB, user: CurrentUser):
        order = get_record(session, Order, record_id)
        if user.role == "customer" and order.user_id != user.id:
            raise HTTPException(404, "Order not found.")
        return order_output(order)

    @app.put("/orders/{record_id}", response_model=OrderOutput, tags=["orders"])
    def update_order(record_id: int, data: OrderInput, session: DB, staff: Staff):
        order = get_record(session, Order, record_id)
        set_order(session, order, data)
        commit(session)
        return order_output(order)

    @app.patch("/orders/{record_id}/status", response_model=OrderOutput, tags=["orders"])
    def update_status(record_id: int, data: StatusInput, session: DB, staff: Staff):
        order = get_record(session, Order, record_id)
        order.status = data.status
        commit(session)
        return order_output(order)

    @app.delete("/orders/{record_id}", status_code=204, tags=["orders"])
    def delete_order(record_id: int, session: DB, admin: Admin):
        session.delete(get_record(session, Order, record_id))
        commit(session)
        return Response(status_code=204)

    return app


app = create_app()
