"""Adapter between the team's SQLAlchemy entities and the existing UI vocabulary.

The team's tables retain numeric IDs, snake_case fields and cookie authentication.
The UI's branch/recipe/reward/shift metadata lives in an additive extension table.
All shared mutations are serialized in a SQLite transaction, never a browser save.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import json
import math
import re
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import Integer, Text, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from models import (
    Base,
    User,
    Pizza,
    Drink,
    Topping,
    Inventory,
    Order,
    OrderPizza,
    OrderDrink,
    OrderTopping,
)
from api.auth import CurrentUser, password_hasher

FIXTURE = json.loads(
    (Path(__file__).parent / "frontend-fixture.json").read_text(encoding="utf-8")
)
SIZES = FIXTURE["sizes"]
TOPPINGS = {row["id"]: row for row in FIXTURE["toppings"]}
DRINKS = {row["id"]: row for row in FIXTURE["drinks"]}
STATUS = ["Order Received", "Preparing", "Baking", "Quality Check"]
TEAM_STATUS = {
    "Order Received": "order_received",
    "Preparing": "preparing",
    "Baking": "preparing",
    "Quality Check": "preparing",
    "Ready for Pickup": "ready_for_pickup",
    "Out for Delivery": "out_for_delivery",
    "Completed": "completed",
}


class IntegrationBase(DeclarativeBase):
    pass


class Workspace(IntegrationBase):
    __tablename__ = "ui_workspace"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document: Mapped[str] = mapped_column(Text, nullable=False)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def identity(user):
    return "u" + str(user.id)


def profile(user):
    name = user.name.split(" ", 1)
    return {
        "id": identity(user),
        "firstName": name[0],
        "lastName": name[1] if len(name) > 1 else "",
        "email": user.email or "",
        "phone": user.phone_number,
        "address": None,
        "apiUserId": user.id,
    }


def money_round(number):
    return int(Decimal(str(number)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def prices(items):
    subtotal, usage = 0, {}

    def add(key, amount):
        usage[key] = usage.get(key, 0) + amount

    if not isinstance(items, list) or not items or len(items) > 100:
        raise HTTPException(422, "An order needs 1–100 item lines.")
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("size"), str):
            raise HTTPException(422, "Invalid order item.")
        size = SIZES.get(item.get("size"))
        qty = item.get("quantity")
        if not size or type(qty) is not int or not 1 <= qty <= 20:
            raise HTTPException(
                422, "Choose a valid size and whole quantity from 1 to 20."
            )
        if len(str(item.get("instructions", ""))) > 250:
            raise HTTPException(422, "Instructions cannot exceed 250 characters.")
        if item.get("kind") == "pizza":
            toppings = item.get("toppings", [])
            if (
                not isinstance(toppings, list)
                or any(not isinstance(t, str) for t in toppings)
                or len(set(toppings)) != len(toppings)
                or any(t not in TOPPINGS for t in toppings)
            ):
                raise HTTPException(422, "Invalid toppings.")
            subtotal += (size["baseCents"] + len(toppings) * size["toppingCents"]) * qty
            add("marinara", size["portionCups"] * qty)
            add("cheese", size["portionCups"] * qty)
            for key in toppings:
                topping = TOPPINGS[key]
                add(topping["ingredientId"], topping["portions"][item["size"]] * qty)
        elif item.get("kind") == "drink" and item.get("drinkId") in DRINKS:
            subtotal += size["drinkCents"] * qty
            add("drink-" + item["drinkId"], qty)
        else:
            raise HTTPException(422, "Unknown product.")
    return subtotal, usage


def provision(session):
    """Initialize a NEW integration database only; never seed over saved work."""
    if session.get(Workspace, 1):
        return
    if any(
        session.scalar(select(model.id).limit(1)) is not None
        for model in [User, Pizza, Drink, Topping, Inventory, Order]
    ):
        raise RuntimeError(
            "This legacy database contains data without integration metadata. Use a new database or a reviewed migration; nothing was overwritten."
        )
    state = deepcopy(FIXTURE["state"])
    # Shift timestamps are relative to first startup, rather than archive date.
    now = datetime.now(timezone.utc)
    for i, shift in enumerate(state["shifts"]):
        shift["clockIn"] = (now - timedelta(hours=3 + i)).isoformat()
        if shift["clockOut"]:
            shift["clockOut"] = (now - timedelta(hours=1)).isoformat()
    mapping = {
        "customers": {},
        "employees": {},
        "pizzas": {},
        "drinks": {},
        "toppings": {},
        "inventory": {},
    }
    for customer in state["customers"]:
        user = User(
            name=customer["firstName"] + " " + customer["lastName"],
            email=customer["email"],
            phone_number=customer["phone"],
            address=json.dumps(customer["address"]),
            dine_in_name=customer["firstName"],
            role="customer",
            password_hash=password_hasher.hash("CustomerPizza!2026"),
        )
        session.add(user)
        session.flush()
        mapping["customers"][customer["id"]] = user.id
        customer["apiUserId"] = user.id
    for employee in state["employees"]:
        user = User(
            name=employee["firstName"] + " " + employee["lastName"],
            email=employee["email"],
            phone_number=employee["phone"],
            address=employee["branchId"],
            dine_in_name=employee["firstName"],
            role="admin" if employee["role"] == "Administrator" else "staff",
            password_hash=password_hasher.hash(
                "Pizza" if employee["id"] == "e1" else "EmployeePizza!2026"
            ),
        )
        session.add(user)
        session.flush()
        mapping["employees"][employee["id"]] = user.id
        employee["apiUserId"] = user.id
    for key, size in SIZES.items():
        pizza = Pizza(size=key, price=Decimal(size["baseCents"]) / 100)
        session.add(pizza)
        session.flush()
        mapping["pizzas"][key] = pizza.id
        for drinkId, drink in DRINKS.items():
            product = Drink(
                name=drink["name"], size=key, price=Decimal(size["drinkCents"]) / 100
            )
            session.add(product)
            session.flush()
            mapping["drinks"][drinkId + ":" + key] = product.id
    for key, topping in TOPPINGS.items():
        row = Topping(name=topping["name"])
        session.add(row)
        session.flush()
        mapping["toppings"][key] = row.id
    for ingredient in state["ingredients"]:
        # The upstream inventory rounds to 0.1, which cannot represent 1/8 cup.
        # Store eighth-cup units in its quantity and keep exact UI cups in metadata.
        factor = 8 if ingredient["unit"] == "cups" else 1
        row = Inventory(
            name=ingredient["name"],
            quantity=Decimal(str(ingredient["quantity"] * factor)),
            unit="eighth-cup" if factor == 8 else "units",
        )
        session.add(row)
        session.flush()
        mapping["inventory"][ingredient["branchId"] + ":" + ingredient["id"]] = row.id
    state["mapping"] = mapping
    for order in state["orders"]:
        # Fix old fixture dates to this startup's dates while preserving relative offsets.
        old = datetime.fromisoformat(order["createdAt"].replace("Z", "+00:00"))
        reference = max(
            datetime.fromisoformat(o["createdAt"].replace("Z", "+00:00"))
            for o in FIXTURE["state"]["orders"]
        )
        delta = now - reference
        for key in ["createdAt", "updatedAt", "estimatedAt"]:
            order[key] = (
                datetime.fromisoformat(order[key].replace("Z", "+00:00")) + delta
            ).isoformat()
        mirror_order(session, state, order)
    session.add(Workspace(id=1, document=json.dumps(state)))
    session.commit()


def mirror_order(session, state, order, user_id=None):
    mapping = state["mapping"]
    row = Order(
        user_id=user_id or mapping["customers"].get(order["customerId"]),
        status=TEAM_STATUS[order["status"]],
        order_time=datetime.fromisoformat(
            order["createdAt"].replace("Z", "+00:00")
        ).replace(tzinfo=None),
    )
    session.add(row)
    session.flush()
    order["apiOrderId"] = row.id
    for item in order["items"]:
        if item["kind"] == "pizza":
            line = OrderPizza(
                order=row,
                pizza_id=mapping["pizzas"][item["size"]],
                quantity=item["quantity"],
            )
            session.add(line)
            session.flush()
            for topping in item["toppings"]:
                session.add(
                    OrderTopping(
                        order_pizza=line, topping_id=mapping["toppings"][topping]
                    )
                )
        else:
            # Upstream drink table only permits one row per product; consolidate.
            drinkId = mapping["drinks"][item["drinkId"] + ":" + item["size"]]
            existing = next(
                (line for line in row.order_drinks if line.drink_id == drinkId), None
            )
            if existing:
                existing.quantity += item["quantity"]
            else:
                session.add(
                    OrderDrink(order=row, drink_id=drinkId, quantity=item["quantity"])
                )
    session.flush()


def customer_id(state, user):
    return next(
        (
            key
            for key, value in state["mapping"]["customers"].items()
            if value == user.id
        ),
        identity(user),
    )


def employee_record(state, user):
    return next(
        (row for row in state["employees"] if row.get("apiUserId") == user.id), None
    )


def staff_scope(state, user, branch):
    if user.role == "admin":
        return
    employee = employee_record(state, user)
    if user.role != "staff" or not employee or employee["branchId"] != branch:
        raise HTTPException(
            403, "This operation requires access to the assigned branch."
        )


def sync_inventory(session, state):
    for item in state["ingredients"]:
        key = item["branchId"] + ":" + item["id"]
        row = session.get(Inventory, state["mapping"]["inventory"][key])
        row.quantity = Decimal(
            str(item["quantity"] * (8 if item["unit"] == "cups" else 1))
        )


def snapshot(state, user):
    result = deepcopy(state)
    result.pop("mapping", None)
    result.pop("salesHistory", None)
    cid = customer_id(state, user)
    current = next((c for c in result["customers"] if c["id"] == cid), profile(user))
    if not any(c["id"] == cid for c in result["customers"]):
        result["customers"].append(current)
    result["currentCustomerId"] = cid
    employee = employee_record(state, user)
    result["staffEmployeeId"] = employee["id"] if employee else "e1"
    result["branchId"] = employee["branchId"] if employee else "downtown"
    if user.role == "customer":
        result["customers"] = [current]
        result["orders"] = [o for o in result["orders"] if o["customerId"] == cid]
        result["employees"] = []
        result["shifts"] = []
        result["tickets"] = [t for t in result["tickets"] if t["customerId"] == cid]
        result["rewards"] = {cid: result["rewards"].get(cid, 0)}
        result["rewardTransactions"] = [
            t for t in result["rewardTransactions"] if t["customerId"] == cid
        ]
        result["ingredients"] = []
    elif user.role == "staff":
        branch = employee["branchId"] if employee else ""
        result["employees"] = [employee] if employee else []
        result["shifts"] = [
            s
            for s in result["shifts"]
            if employee and s["employeeId"] == employee["id"]
        ]
        result["orders"] = [o for o in result["orders"] if o["branchId"] == branch]
        result["ingredients"] = [
            i for i in result["ingredients"] if i["branchId"] == branch
        ]
        result["tickets"] = [
            t
            for t in result["tickets"]
            if any(o["id"] == t.get("orderId") for o in result["orders"])
        ]
        # Do not send reward balances/history for other accounts to branch staff.
        result["rewards"] = {}
        result["rewardTransactions"] = []
        result["customers"] = []
    for key in ["cart", "chat", "selectedPromotion", "lastOrderId"]:
        result.pop(key, None)
    return result


router = APIRouter(prefix="/bridge", tags=["frontend integration"])


@router.get("/state")
def read_state(request: Request, user: CurrentUser):
    with request.app.state.sessions() as session:
        row = session.get(Workspace, 1)
        return {"state": snapshot(json.loads(row.document), user)}


class Command(BaseModel):
    action: str
    data: dict = Field(default_factory=dict)


@router.post("/command")
def command(body: Command, request: Request, user: CurrentUser):
    # Separate write session, serialized before reading the shared extension state.
    with request.app.state.sessions() as session:
        session.execute(text("BEGIN IMMEDIATE"))
        row = session.get(Workspace, 1)
        state = json.loads(row.document)
        result = execute(session, state, user, body.action, body.data)
        row.document = json.dumps(state)
        session.commit()
        return {"result": result, "state": snapshot(state, user)}


def execute(session, state, user, action, data):
    cid = customer_id(state, user)
    employee = employee_record(state, user)
    if action == "checkout":
        if user.role != "customer":
            raise HTTPException(403, "Sign in as a customer to check out.")
        key = str(data.get("submissionId", ""))
        if not key or len(key) > 150:
            raise HTTPException(422, "Missing order submission key.")
        existing = next(
            (
                o
                for o in state["orders"]
                if o.get("submissionId") == key and o["customerId"] == cid
            ),
            None,
        )
        if existing:
            return existing
        contact = data.get("customer", {})
        if not isinstance(contact, dict):
            raise HTTPException(422, "Customer details are required.")
        for keyName in ["firstName", "lastName", "email", "phone"]:
            if (
                not isinstance(contact.get(keyName), str)
                or not contact[keyName].strip()
                or len(contact[keyName]) > 150
            ):
                raise HTTPException(
                    422, "Name, email and phone are required (maximum 150 characters)."
                )
        if (
            not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", contact["email"])
            or len(re.sub(r"\D", "", contact["phone"])) < 10
        ):
            raise HTTPException(422, "Check your email and phone number.")
        kind = contact.get("type")
        if kind not in ["pickup", "delivery"] or contact.get("payment") not in [
            "demo",
            "store",
        ]:
            raise HTTPException(422, "Choose fulfillment and payment.")
        if kind == "delivery":
            if (
                any(
                    not str(contact.get(k, "")).strip()
                    for k in ["street", "city", "state", "zip"]
                )
                or not re.fullmatch("[A-Za-z]{2}", contact["state"])
                or not re.fullmatch(r"\d{5}(-\d{4})?", contact["zip"])
            ):
                raise HTTPException(422, "A valid delivery address is required.")
        items = deepcopy(data.get("items", []))
        subtotal, usage = prices(items)
        stock = {
            i["id"]: i for i in state["ingredients"] if i["branchId"] == "downtown"
        }
        for keyName, amount in usage.items():
            if keyName not in stock or stock[keyName]["quantity"] < amount:
                raise HTTPException(
                    409,
                    "Not enough "
                    + stock.get(keyName, {}).get("name", keyName)
                    + " available.",
                )
        discount, points = 0, 0
        promotion = data.get("promotionId")
        if promotion:
            offer = next((p for p in state["promotions"] if p["id"] == promotion), None)
            day = datetime.now(timezone.utc).date().isoformat()
            if (
                not offer
                or not offer["active"]
                or not offer["start"] <= day <= offer["end"]
                or subtotal < offer["minSubtotal"]
            ):
                raise HTTPException(
                    409, "This promotion is not eligible for this order."
                )
            points = offer["requiredPoints"]
            if state["rewards"].get(cid, 0) < points:
                raise HTTPException(409, "Not enough reward points.")
            discount = min(
                subtotal,
                (
                    offer["discountValue"]
                    if offer["discountType"] == "fixed"
                    else money_round(subtotal * offer["discountValue"] / 100)
                ),
            )
        tax = money_round((subtotal - discount) * 0.0825)
        delivery = 300 if kind == "delivery" else 0
        total = subtotal - discount + tax + delivery
        queue = sum(
            o["branchId"] == "downtown" and o["status"] != "Completed"
            for o in state["orders"]
        )
        minutes = (
            12
            + 3 * sum(i["quantity"] for i in items if i["kind"] == "pizza")
            + math.ceil(sum(i["quantity"] for i in items) / 3)
            + min(queue * 2, 20)
            + (15 if kind == "delivery" else 0)
        )
        order = {
            "id": "LP-"
            + str(
                max([1040] + [int(o["id"].split("-")[1]) for o in state["orders"]]) + 1
            ),
            "submissionId": data["submissionId"],
            "customerId": cid,
            "customer": {
                k: contact[k].strip()
                for k in ["firstName", "lastName", "email", "phone"]
            },
            "branchId": "downtown",
            "items": items,
            "type": kind,
            "payment": contact["payment"],
            "address": (
                {k: contact[k] for k in ["street", "city", "state", "zip"]}
                if kind == "delivery"
                else None
            ),
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "delivery": delivery,
            "total": total,
            "createdAt": stamp(),
            "updatedAt": stamp(),
            "estimatedAt": (
                datetime.now(timezone.utc) + timedelta(minutes=minutes)
            ).isoformat(),
            "status": "Order Received",
            "pointsEarned": total // 100,
            "promotionId": promotion,
            "inventoryDeducted": True,
        }
        for keyName, amount in usage.items():
            stock[keyName]["quantity"] -= amount
        state["rewards"][cid] = (
            state["rewards"].get(cid, 0) - points + order["pointsEarned"]
        )
        for value, kindName in [(-points, "redeem"), (order["pointsEarned"], "earn")]:
            if value:
                state["rewardTransactions"].append(
                    {
                        "id": str(uuid.uuid4()),
                        "customerId": cid,
                        "orderId": order["id"],
                        "points": value,
                        "type": kindName,
                        "createdAt": stamp(),
                    }
                )
        mirror_order(session, state, order, user.id)
        sync_inventory(session, state)
        state["orders"].insert(0, order)
        return order
    if action == "advance":
        order = next((o for o in state["orders"] if o["id"] == data.get("id")), None)
        if not order:
            raise HTTPException(404, "Order not found.")
        staff_scope(state, user, order["branchId"])
        steps = (
            STATUS
            + (
                ["Out for Delivery"]
                if order["type"] == "delivery"
                else ["Ready for Pickup"]
            )
            + ["Completed"]
        )
        order["status"] = steps[min(steps.index(order["status"]) + 1, len(steps) - 1)]
        order["updatedAt"] = stamp()
        session.get(Order, order["apiOrderId"]).status = TEAM_STATUS[order["status"]]
        return order
    if action == "stock":
        branch = data.get("branchId")
        staff_scope(state, user, branch)
        value = data.get("quantity")
        if (
            type(value) not in [int, float]
            or not math.isfinite(value)
            or not 0 <= value <= 100000
        ):
            raise HTTPException(422, "Stock must be between 0 and 100,000.")
        item = next(
            (
                i
                for i in state["ingredients"]
                if i["branchId"] == branch and i["id"] == data.get("id")
            ),
            None,
        )
        if not item:
            raise HTTPException(404, "Ingredient not found.")
        new = item["quantity"] + value if data.get("restock") else value
        factor = 8 if item["unit"] == "cups" else 1
        if abs(new * factor * 10 - round(new * factor * 10)) > 0.00001:
            raise HTTPException(
                422,
                "Use quantities in 0.0125-cup increments (0.1 upstream eighth-cup units).",
            )
        item["quantity"] = new
        if data.get("restock"):
            item["lastRestocked"] = stamp()
        sync_inventory(session, state)
        return item
    if action == "clock":
        if not employee:
            raise HTTPException(403, "Employee account required.")
        active = next(
            (
                s
                for s in state["shifts"]
                if s["employeeId"] == employee["id"] and not s["clockOut"]
            ),
            None,
        )
        if active:
            active["clockOut"] = stamp()
            return "Clocked out."
        state["shifts"].insert(
            0,
            {
                "id": str(uuid.uuid4()),
                "employeeId": employee["id"],
                "branchId": employee["branchId"],
                "clockIn": stamp(),
                "clockOut": None,
            },
        )
        return "Clocked in."
    if action == "verify":
        if user.role != "admin":
            raise HTTPException(403, "Administrator access required.")
        shift = next((s for s in state["shifts"] if s["id"] == data.get("id")), None)
        if not shift or not shift["clockOut"]:
            raise HTTPException(409, "Only a completed shift can be verified.")
        shift.update(verifiedBy=employee["id"], verifiedAt=stamp())
        return shift
    if action == "profile":
        if user.role != "customer":
            raise HTTPException(403, "Customer account required.")
        person = next((c for c in state["customers"] if c["id"] == cid), None)
        if not person:
            person = profile(user)
            state["customers"].append(person)
        for keyName in ["firstName", "lastName", "phone", "email", "address"]:
            if keyName in data:
                person[keyName] = data[keyName]
        record = session.get(User, user.id)
        # Email credentials remain immutable here; use account management to change login.
        if person["email"] != record.email:
            raise HTTPException(422, "Contact email must match your login email.")
        record.name = person["firstName"] + " " + person["lastName"]
        record.phone_number = person["phone"]
        record.address = json.dumps(person["address"])
        return person
    if action == "promotion":
        if user.role != "admin":
            raise HTTPException(403, "Administrator access required.")
        offer = next(
            (p for p in state["promotions"] if p["id"] == data.get("id")), None
        )
        if not offer:
            raise HTTPException(404, "Promotion not found.")
        changes = data.get("changes", {})
        candidate = {
            **offer,
            **{k: v for k, v in changes.items() if k in offer and k != "id"},
        }
        if (
            candidate["discountType"] not in ["fixed", "percent"]
            or any(
                type(candidate[k]) is not int or candidate[k] < 0
                for k in ["discountValue", "minSubtotal", "requiredPoints"]
            )
            or candidate["end"] < candidate["start"]
            or candidate["discountType"] == "percent"
            and candidate["discountValue"] > 100
        ):
            raise HTTPException(422, "Invalid promotion.")
        offer.update(candidate)
        return offer
    if action == "ticket":
        if user.role != "customer":
            raise HTTPException(403, "Customer account required.")
        description = str(data.get("description", "")).strip()
        if not description or len(description) > 1500:
            raise HTTPException(422, "Describe the issue (1–1500 characters).")
        reference = str(data.get("orderId", "")).strip().upper()
        if reference and not any(
            o["id"] == reference and o["customerId"] == cid for o in state["orders"]
        ):
            raise HTTPException(404, "Order not found for your account.")
        ticket = {
            "id": "TK-" + uuid.uuid4().hex[:10].upper(),
            "customerId": cid,
            "customerName": user.name,
            "orderId": reference or None,
            "category": str(data.get("category", "Other"))[:100],
            "description": description,
            "summary": str(data.get("summary", ""))[:5000],
            "messages": data.get("messages", [])[:20],
            "createdAt": stamp(),
            "status": "Escalated",
        }
        state["tickets"].insert(0, ticket)
        return ticket
    if action == "ticket-status":
        ticket = next((t for t in state["tickets"] if t["id"] == data.get("id")), None)
        if not ticket:
            raise HTTPException(404, "Ticket not found.")
        order = next(
            (o for o in state["orders"] if o["id"] == ticket.get("orderId")), None
        )
        staff_scope(state, user, order["branchId"] if order else None)
        if data.get("status") not in ["Escalated", "In Review", "Resolved"]:
            raise HTTPException(422, "Invalid ticket status.")
        ticket["status"] = data["status"]
        return ticket
    raise HTTPException(422, "Unknown integration command.")
