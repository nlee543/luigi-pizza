"""End-to-end HTTP tests for the team's API plus our UI adapter."""

from copy import deepcopy
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from integrated_app import app, api
from integration import Workspace
from models import Order, OrderPizza, Inventory


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CONNECTIONSTRING", "sqlite:///" + str(tmp_path / "integration.db")
    )
    with TestClient(app) as connection:
        yield connection


def login(client, email="alex@example.test", password="CustomerPizza!2026"):
    response = client.post(
        "/api/auth/login",
        headers={"X-CSRF-Protection": "1"},
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def command(client, headers, action, data):
    return client.post(
        "/api/bridge/command", headers=headers, json={"action": action, "data": data}
    )


def checkout_data(key="integration-order"):
    return {
        "submissionId": key,
        "customer": {
            "firstName": "Alex",
            "lastName": "Morgan",
            "email": "alex@example.test",
            "phone": "202-555-0142",
            "type": "pickup",
            "payment": "demo",
        },
        "items": [
            {
                "id": "a",
                "kind": "pizza",
                "size": "large",
                "quantity": 1,
                "toppings": ["pepperoni"],
                "instructions": "First pizza",
            },
            {
                "id": "b",
                "kind": "pizza",
                "size": "large",
                "quantity": 1,
                "toppings": ["mushrooms"],
                "instructions": "Second pizza",
            },
        ],
        "promotionId": None,
    }


def test_static_and_authenticated_bootstrap(client):
    assert client.get("/").status_code == 200
    assert "LUIGI_API = true" in client.get("/runtime.js").text
    assert client.get("/backend/models.py").status_code == 404
    assert client.get("/api/bridge/state").status_code == 401
    login(client)
    state = client.get("/api/bridge/state").json()["state"]
    assert [c["id"] for c in state["customers"]] == ["c1"]
    assert all(o["customerId"] == "c1" for o in state["orders"])
    assert (
        state["employees"] == []
        and state["shifts"] == []
        and state["ingredients"] == []
    )
    assert "mapping" not in state


def test_checkout_commits_to_team_tables_and_preserves_distinct_same_size_pizzas(
    client,
):
    headers = login(client)
    response = command(client, headers, "checkout", checkout_data())
    assert response.status_code == 200, response.text
    order = response.json()["result"]
    assert order["subtotal"] == 2400 and order["tax"] == 198 and order["total"] == 2598
    assert order["pointsEarned"] == 25
    with api.state.sessions() as session:
        saved = session.get(Order, order["apiOrderId"])
        assert saved.user_id == 1 and saved.status == "order_received"
        assert len(saved.order_pizzas) == 2
        assert (
            saved.order_pizzas[0].order_toppings[0].topping_id
            != saved.order_pizzas[1].order_toppings[0].topping_id
        )
        state = json.loads(session.get(Workspace, 1).document)
        assert (
            next(i["quantity"] for i in state["ingredients"] if i["id"] == "marinara")
            == 46
        )
        assert state["rewards"]["c1"] == 185
    retry = command(client, headers, "checkout", checkout_data()).json()["result"]
    assert retry["id"] == order["id"]
    with api.state.sessions() as session:
        state = json.loads(session.get(Workspace, 1).document)
        assert (
            next(i["quantity"] for i in state["ingredients"] if i["id"] == "marinara")
            == 46
        )


def test_stock_failure_rolls_back_and_server_ignores_client_prices(client):
    headers = login(client)
    data = checkout_data("bad-stock")
    data["items"][0]["toppings"] = ["jalapenos"]
    before = client.get("/api/bridge/state").json()["state"]
    response = command(client, headers, "checkout", data)
    assert response.status_code == 409
    assert client.get("/api/bridge/state").json()["state"] == before
    data = checkout_data("price-tamper")
    data["items"][0]["price"] = 0
    data["total"] = 1
    response = command(client, headers, "checkout", data)
    assert response.status_code == 200
    assert response.json()["result"]["total"] == 2598


def test_server_enforces_branch_scope_and_own_shifts(client):
    headers = login(client, "sam@example.test", "EmployeePizza!2026")
    state = client.get("/api/bridge/state").json()["state"]
    assert all(s["employeeId"] == "e2" for s in state["shifts"])
    assert len(state["employees"]) == 1
    assert all(o["branchId"] == "downtown" for o in state["orders"])
    assert command(client, headers, "verify", {"id": "sh2"}).status_code == 403
    assert (
        command(
            client,
            headers,
            "promotion",
            {"id": "WELCOME5", "changes": {"active": False}},
        ).status_code
        == 403
    )
    assert (
        command(
            client,
            headers,
            "stock",
            {"id": "cheese", "branchId": "riverside", "quantity": 10},
        ).status_code
        == 403
    )
    assert command(client, headers, "advance", {"id": "LP-1056"}).status_code == 403
    assert command(client, headers, "clock", {}).json()["result"] == "Clocked out."


def test_admin_mutations_persist_and_mirror_inventory_and_status(client):
    headers = login(client, "luigi@example.test", "Pizza")
    result = command(client, headers, "verify", {"id": "sh2"})
    assert result.status_code == 200 and result.json()["result"]["verifiedBy"] == "e1"
    result = command(
        client,
        headers,
        "stock",
        {"id": "cheese", "branchId": "downtown", "quantity": 0.125, "restock": True},
    )
    assert result.status_code == 200, result.text
    with api.state.sessions() as session:
        state = json.loads(session.get(Workspace, 1).document)
        inv_id = state["mapping"]["inventory"]["downtown:cheese"]
        assert float(session.get(Inventory, inv_id).quantity) == 497
    result = command(client, headers, "advance", {"id": "LP-1043"})
    assert result.status_code == 200
    with api.state.sessions() as session:
        assert (
            session.get(Order, result.json()["result"]["apiOrderId"]).status
            == "preparing"
        )
    assert (
        command(
            client,
            headers,
            "promotion",
            {"id": "WELCOME5", "changes": {"active": False}},
        ).status_code
        == 200
    )
    state = client.get("/api/bridge/state").json()["state"]
    assert not state["promotions"][0]["active"]


def test_support_profile_and_csrf(client):
    headers = login(client)
    assert command(client, {}, "checkout", checkout_data()).status_code == 403
    ticket = command(
        client,
        headers,
        "ticket",
        {
            "category": "Order issue",
            "description": "Missing topping",
            "orderId": "LP-1041",
            "summary": "Escalated from assistant",
            "messages": [],
        },
    )
    assert ticket.status_code == 200, ticket.text
    assert ticket.json()["result"]["status"] == "Escalated"
    assert (
        command(
            client,
            headers,
            "ticket",
            {"description": "Wrong order", "orderId": "LP-1042"},
        ).status_code
        == 404
    )
    response = command(
        client,
        headers,
        "profile",
        {
            "firstName": "Alex",
            "lastName": "Updated",
            "email": "alex@example.test",
            "phone": "202-555-0100",
            "address": None,
        },
    )
    assert response.status_code == 200
    assert client.get("/api/auth/me").json()["user"]["name"] == "Alex Updated"
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/bridge/state").status_code == 401


def test_new_customer_registration_can_order(client):
    account = {
        "name": "Test Customer",
        "email": "new@example.test",
        "password": "FreshPizza!2026",
        "address": "123 Example Lane",
        "phone_number": "202-555-0123",
        "dine_in_name": "Test",
    }
    response = client.post(
        "/api/auth/register", json=account, headers={"X-CSRF-Protection": "1"}
    )
    assert response.status_code == 201, response.text
    headers = login(client, account["email"], account["password"])
    response = command(client, headers, "checkout", checkout_data("new-customer"))
    assert response.status_code == 200, response.text
    assert response.json()["result"]["customerId"].startswith("u")


def test_legacy_writes_cannot_bypass_integrated_business_transactions(client):
    headers = login(client, "luigi@example.test", "Pizza")
    response = client.post(
        "/api/orders",
        headers=headers,
        json={"pizzas": [{"pizza_id": 1, "quantity": 1}]},
    )
    assert response.status_code == 409
    assert client.get("/api/pizzas").status_code == 200


def test_server_rules_match_javascript_configuration():
    import subprocess
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    output = subprocess.check_output(
        [
            "node",
            "--input-type=module",
            "-e",
            "import {SIZES,TOPPINGS,DRINKS} from './js/config.js'; console.log(JSON.stringify({sizes:SIZES,toppings:TOPPINGS,drinks:DRINKS}));",
        ],
        cwd=root,
        encoding="utf-8",
    )
    from integration import FIXTURE

    config = json.loads(output)
    for key in ["sizes", "toppings", "drinks"]:
        assert config[key] == FIXTURE[key]


def test_saved_workspace_survives_application_restart(client):
    headers = login(client, "luigi@example.test", "Pizza")
    command(client, headers, "verify", {"id": "sh2"})
    # A second lifespan reuses the same database, not the fixture again.
    with TestClient(app) as second:
        login(second, "luigi@example.test", "Pizza")
        state = second.get("/api/bridge/state").json()["state"]
        assert (
            next(s for s in state["shifts"] if s["id"] == "sh2")["verifiedBy"] == "e1"
        )
