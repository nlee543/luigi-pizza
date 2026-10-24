import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from api.auth import password_hasher
from api.main import create_app
from models import User

PASSWORD = 'Student-password-123'
PASSWORD_HASH = password_hasher.hash(PASSWORD)
PROFILE = {'name': 'Alex', 'address': '123 Main', 'phone_number': '+0123', 'dine_in_name': 'Alex'}
PAYLOADS = {
    'drinks': {'name': 'Cola', 'size': 'small', 'price': '1.25'},
    'pizzas': {'size': 'large', 'price': '9.00'},
    'toppings': {'name': 'Olives'},
    'inventory': {'name': 'Flour', 'unit': 'kg', 'quantity': '12.3'},
}


def add_accounts(client):
    with client.app.state.sessions() as session:
        for role in ('admin', 'staff', 'customer'):
            session.add(User(**PROFILE, email=f'{role}@example.com', role=role, password_hash=PASSWORD_HASH))
        session.commit()


def login(client, email='admin@example.com', password=PASSWORD):
    response = client.post('/auth/login', json={'email': email, 'password': password},
                           headers={'X-CSRF-Protection': '1'})
    assert response.status_code == 200, response.text
    client.headers['X-CSRF-Token'] = response.json()['csrf_token']
    return response.json()['user']


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'test.db'}", cookie_secure=False,
                               allowed_origin='http://testserver')) as client:
        add_accounts(client)
        login(client)
        yield client


def post(client, resource, data=None):
    response = client.post(f'/{resource}', json=data or PAYLOADS[resource])
    assert response.status_code == 201, response.text
    return response.json()


def customer_id(client):
    return client.get('/staff/customers').json()[0]['id']


def test_order_status_and_readonly_fields(client):
    drink = post(client, 'drinks')
    body = {'drinks': [{'drink_id': drink['id']}]}
    order = post(client, 'staff/orders', {**body, 'user_id': customer_id(client)})
    url = f"/orders/{order['id']}"
    for status in ['preparing', 'out_for_delivery', 'ready_for_pickup', 'completed']:
        response = client.patch(url + '/status', json={'status': status})
        assert response.status_code == 200
        assert response.json()['status'] == status
        assert response.json()['order_time'] == order['order_time']
    assert client.put(url, json=body).json()['status'] == 'completed'
    for extra in [{'status': 'completed'}, {'user_id': 999}, {'order_time': order['order_time']}, {'created_by_user_id': 99}]:
        assert client.put(url, json={**body, **extra}).status_code == 422
    assert client.patch(url + '/status', json={'status': 'invalid'}).status_code == 422
    assert client.post('/staff/orders', json={**body, 'user_id': customer_id(client), 'status': 'completed'}).status_code == 422


@pytest.mark.parametrize('resource', PAYLOADS)
def test_resource_crud(client, resource):
    assert client.get(f'/{resource}').json() == []
    created = post(client, resource)
    url = f"/{resource}/{created['id']}"
    assert client.get(url).json() == created
    assert client.get(f'/{resource}').json() == [created]
    changed = dict(PAYLOADS[resource])
    field = 'size' if resource == 'pizzas' else 'name'
    changed[field] = 'medium' if field == 'size' else 'Updated'
    response = client.put(url, json=changed)
    assert response.status_code == 200, response.text
    assert response.json()[field] == changed[field]
    assert client.get(url).json() == response.json()
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404
    assert client.delete(url).status_code == 404
    assert client.put(url, json=changed).status_code == 404
    assert client.get(f'/{resource}').json() == []


@pytest.mark.parametrize('kind', ['drinks', 'pizzas', 'both'])
@pytest.mark.parametrize('topping_count', [0, 1, 3])
def test_order_crud(client, kind, topping_count):
    owner = customer_id(client)
    drink = post(client, 'drinks')
    pizza = post(client, 'pizzas')
    toppings = [post(client, 'toppings', {'name': f'Topping {i}'})['id'] for i in range(topping_count)]
    body = {'user_id': owner, 'drinks': [], 'pizzas': []}
    if kind in ('drinks', 'both'):
        body['drinks'] = [{'drink_id': drink['id'], 'quantity': 2}]
    if kind in ('pizzas', 'both'):
        body['pizzas'] = [{'pizza_id': pizza['id'], 'quantity': 1, 'topping_ids': toppings}]
    created = post(client, 'staff/orders', body)
    url = f"/orders/{created['id']}"
    assert created == {'id': created['id'], **body, 'status': 'order_received',
                       'order_time': created['order_time'], 'created_by_user_id': 1}
    assert created['order_time'].endswith('Z')
    assert client.get(url).json() == created
    assert client.get('/orders').json() == [created]
    updated = {'pizzas': [{'pizza_id': pizza['id'], 'quantity': 3, 'topping_ids': []}]}
    response = client.put(url, json=updated)
    assert response.status_code == 200, response.text
    assert response.json()['pizzas'] == updated['pizzas']
    assert response.json()['drinks'] == []
    assert response.json()['user_id'] == owner
    assert response.json()['created_by_user_id'] == 1
    assert client.get(url).json() == response.json()
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404
    assert client.put(url, json=updated).status_code == 404
    assert client.delete(url).status_code == 404
    with client.app.state.sessions() as session:
        for table in ['orders_drinks', 'orders_pizzas', 'orders_toppings']:
            assert session.scalar(text(f'SELECT count(*) FROM {table}')) == 0


@pytest.mark.parametrize('resource,field,value', [
    ('drinks', 'size', 'huge'), ('drinks', 'price', '-1'),
    ('pizzas', 'price', '1.234'), ('pizzas', 'price', '100000000.00'),
    ('toppings', 'name', 'x' * 51), ('inventory', 'unit', 'x' * 11),
    ('inventory', 'quantity', '1.23'), ('inventory', 'quantity', '-1'),
])
def test_invalid_resources(client, resource, field, value):
    body = {**PAYLOADS[resource], field: value}
    assert client.post(f'/{resource}', json=body).status_code == 422
    item = post(client, resource)
    url = f"/{resource}/{item['id']}"
    assert client.put(url, json=body).status_code == 422
    assert client.get(url).json() == item


@pytest.mark.parametrize('body', [
    {}, {'drinks': [{'drink_id': 1, 'quantity': 0}]},
    {'pizzas': [{'pizza_id': 1, 'quantity': -1}]},
    {'drinks': [{'drink_id': 1, 'quantity': 1.5}]},
    {'drinks': [{'drink_id': 1}, {'drink_id': 1}]},
    {'pizzas': [{'pizza_id': 1}, {'pizza_id': 1}]},
    {'pizzas': [{'pizza_id': 1, 'topping_ids': [1, 1]}]},
])
def test_invalid_orders(client, body):
    assert client.post('/staff/orders', json={**body, 'user_id': customer_id(client)}).status_code == 422
    assert client.get('/orders').json() == []


@pytest.mark.parametrize('missing', ['user', 'drink', 'pizza', 'topping'])
def test_missing_references_are_atomic(client, missing):
    pizza = post(client, 'pizzas')
    original = post(client, 'staff/orders', {'user_id': customer_id(client), 'pizzas': [{'pizza_id': pizza['id']}]})
    body = {'user_id': customer_id(client), 'pizzas': [{'pizza_id': pizza['id']}]}
    if missing == 'user':
        body['user_id'] = 999
    elif missing == 'drink':
        body['drinks'] = [{'drink_id': 999}]
    elif missing == 'pizza':
        body['pizzas'][0]['pizza_id'] = 999
    else:
        body['pizzas'][0]['topping_ids'] = [999]
    assert client.post('/staff/orders', json=body).status_code == 404
    if missing != 'user':
        body.pop('user_id')
        assert client.put(f"/orders/{original['id']}", json=body).status_code == 404
    assert client.get('/orders').json() == [original]


def test_shared_items_and_delete_conflicts(client):
    pizza = post(client, 'pizzas')
    drink = post(client, 'drinks')
    topping = post(client, 'toppings')
    body = {'user_id': customer_id(client), 'drinks': [{'drink_id': drink['id']}],
            'pizzas': [{'pizza_id': pizza['id'], 'topping_ids': [topping['id']]}]}
    first = post(client, 'staff/orders', body)
    second = post(client, 'staff/orders', body)
    for resource, item in [('pizzas', pizza), ('drinks', drink), ('toppings', topping)]:
        assert client.delete(f"/{resource}/{item['id']}").status_code == 409
    assert client.delete(f"/orders/{first['id']}").status_code == 204
    assert client.get(f"/orders/{second['id']}").json() == second
    assert client.delete(f"/orders/{second['id']}").status_code == 204
    for resource, item in [('pizzas', pizza), ('drinks', drink), ('toppings', topping)]:
        assert client.delete(f"/{resource}/{item['id']}").status_code == 204


def test_environment_database_creation_and_persistence(tmp_path, monkeypatch):
    db = tmp_path / 'configured.db'
    monkeypatch.setenv('CONNECTIONSTRING', f'sqlite:///{db}')
    with TestClient(create_app(cookie_secure=False)) as client:
        add_accounts(client)
        login(client)
        saved = post(client, 'toppings')
        cookie = client.cookies.get('luigi_session')
        with client.app.state.sessions() as session:
            assert len(inspect(session.bind).get_table_names()) == 10
            assert session.scalar(text('PRAGMA foreign_keys')) == 1
    with TestClient(create_app(cookie_secure=False)) as client:
        client.cookies.set('luigi_session', cookie)
        assert client.get('/auth/me').status_code == 200
        assert client.get('/toppings').json() == [saved]


def test_memory_database_and_pagination():
    with TestClient(create_app('sqlite:///:memory:', cookie_secure=False)) as client:
        add_accounts(client)
        login(client)
        first = post(client, 'toppings')
        second = post(client, 'toppings')
        assert client.get('/toppings?limit=1').json() == [first]
        assert client.get('/toppings?offset=1&limit=1').json() == [second]
        assert client.get('/toppings?limit=0').status_code == 422
        assert client.get('/openapi.json').status_code == 200
