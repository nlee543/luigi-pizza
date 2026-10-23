from datetime import timedelta
import sqlite3

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from api.auth import COOKIE_NAME, now, token_hash, verify_password
from api.main import create_app
from manage_account import provision_account
from migrate_auth import migrate_auth
from models import LoginSession, User
from test_api import client, login, post, PROFILE, PASSWORD


def register(client, email='new@example.com', **extra):
    return client.post('/auth/register', json={**PROFILE, 'email': email, 'password': PASSWORD, **extra},
                       headers={'X-CSRF-Protection': '1'})


def test_registration_password_storage_and_privilege_injection(client):
    response = register(client, ' NEW@example.com ')
    assert response.status_code == 201
    user = response.json()
    assert user['email'] == 'new@example.com'
    assert user['role'] == 'customer'
    assert not user['must_change_password']
    assert 'password' not in user and 'password_hash' not in user
    with client.app.state.sessions() as session:
        record = session.get(User, user['id'])
        assert record.password_hash != PASSWORD
        assert verify_password(PASSWORD, record.password_hash)
    assert register(client, 'new@EXAMPLE.com').status_code == 409
    for extra in [{'role': 'admin'}, {'admin': True}, {'must_change_password': False}, {'active': True}, {'password_hash': 'fake'}]:
        assert register(client, **extra).status_code == 422
    assert client.post('/users', json=PROFILE).status_code == 404
    assert client.get('/users').status_code == 404


@pytest.mark.parametrize('extra', [{'password': 'short'}, {'email': 'not-email'}, {'name': ''}, {'address': ''}])
def test_registration_validation(client, extra):
    response = register(client, **extra)
    assert response.status_code == 422
    assert PASSWORD not in response.text
    assert all('input' not in error for error in response.json()['detail'])


def test_anonymous_access_and_public_menu(client):
    client.cookies.clear()
    for path in ['/auth/me', '/orders', '/orders/1', '/inventory', '/staff/customers', '/admin/users']:
        assert client.get(path).status_code == 401
    for path in ['/drinks', '/pizzas', '/toppings']:
        assert client.get(path).status_code == 200
    assert client.post('/orders', json={'drinks': [{'drink_id': 1}]}).status_code == 401
    assert client.post('/toppings', json={'name': 'Olives'}).status_code == 401


def test_customer_order_ownership_and_staff_permissions(client):
    pizza = post(client, 'pizzas')
    body = {'pizzas': [{'pizza_id': pizza['id']}]}
    customer = login(client, 'customer@example.com')
    order = post(client, 'orders', body)
    assert order['user_id'] == order['created_by_user_id'] == customer['id']
    assert client.get('/orders').json() == [order]
    for extra in [{'user_id': 1}, {'status': 'completed'}, {'created_by_user_id': 1}]:
        assert client.post('/orders', json={**body, **extra}).status_code == 422
    for path in ['/staff/customers', '/inventory', '/admin/users']:
        assert client.get(path).status_code == 403
    assert client.post('/staff/orders', json={**body, 'user_id': customer['id']}).status_code == 403
    assert client.post('/staff/customers', json={**PROFILE, 'email': 'x@example.com', 'password': PASSWORD}).status_code == 403
    assert client.post('/toppings', json={'name': 'Olives'}).status_code == 403
    assert client.put('/pizzas/1', json={'size': 'small', 'price': '0'}).status_code == 403
    assert client.delete('/pizzas/1').status_code == 403
    assert client.patch('/admin/users/1/access', json={'role': 'customer', 'active': False}).status_code == 403
    assert register(client).status_code == 201
    login(client, 'new@example.com')
    assert client.get('/orders').json() == []
    assert client.get(f"/orders/{order['id']}").status_code == 404
    assert client.put(f"/orders/{order['id']}", json=body).status_code == 403
    assert client.patch(f"/orders/{order['id']}/status", json={'status': 'completed'}).status_code == 403
    assert client.delete(f"/orders/{order['id']}").status_code == 403
    login(client, 'staff@example.com')
    assert client.get('/orders').json() == [order]
    assert client.patch(f"/orders/{order['id']}/status", json={'status': 'preparing'}).status_code == 200
    assert client.delete(f"/orders/{order['id']}").status_code == 403
    assert client.get('/admin/users').status_code == 403


def test_staff_phone_order_and_temporary_password_flow(client):
    drink = post(client, 'drinks')
    staff = login(client, 'staff@example.com')
    customer = post(client, 'staff/customers', {**PROFILE, 'email': 'phone@example.com', 'password': PASSWORD})
    assert customer['role'] == 'customer' and customer['must_change_password']
    assert client.get('/staff/customers?q=phone%40example.com').json() == [customer]
    assert client.get('/staff/customers?q=does-not-exist').json() == []
    body = {'user_id': customer['id'], 'drinks': [{'drink_id': drink['id']}]}
    order = post(client, 'staff/orders', body)
    assert order['user_id'] == customer['id']
    assert order['created_by_user_id'] == staff['id']
    assert client.post('/staff/orders', json={**body, 'user_id': staff['id']}).status_code == 409
    assert client.post('/staff/orders', json={'drinks': body['drinks']}).status_code == 422
    login(client, 'phone@example.com')
    old_cookie = client.cookies.get(COOKIE_NAME)
    assert client.get('/auth/me').json()['user']['must_change_password']
    assert client.get('/orders').status_code == 403
    assert client.post('/orders', json={'drinks': body['drinks']}).status_code == 403
    assert client.put('/auth/profile', json=PROFILE).status_code == 403
    assert client.post('/auth/change-password', json={'current_password': 'wrong', 'new_password': 'New-password-123'}).status_code == 400
    assert client.post('/auth/change-password', json={'current_password': PASSWORD, 'new_password': PASSWORD}).status_code == 400
    assert client.post('/auth/change-password', json={'current_password': PASSWORD, 'new_password': 'New-password-123'}).status_code == 204
    client.cookies.set(COOKIE_NAME, old_cookie)
    assert client.get('/auth/me').status_code == 401
    client.cookies.clear()
    assert client.post('/auth/login', json={'email': 'phone@example.com', 'password': PASSWORD}, headers={'X-CSRF-Protection': '1'}).status_code == 401
    login(client, 'phone@example.com', 'New-password-123')
    assert client.get('/orders').json() == [order]
    assert not client.get('/auth/me').json()['user']['must_change_password']


def test_csrf_and_origin_checks(client):
    for headers in [{}, {'X-CSRF-Token': 'wrong'}]:
        client.headers.pop('X-CSRF-Token', None)
        assert client.post('/toppings', json={'name': 'Olives'}, headers=headers).status_code == 403
    csrf = client.get('/auth/me').json()['csrf_token']
    client.headers['X-CSRF-Token'] = csrf
    assert client.post('/toppings', json={'name': 'Olives'}, headers={'Origin': 'https://evil.example'}).status_code == 403
    assert client.post('/toppings', json={'name': 'Olives'}, headers={'Origin': 'null'}).status_code == 403
    assert client.post('/toppings', json={'name': 'Olives'}, headers={'Origin': 'http://testserver'}).status_code == 201
    assert client.post('/auth/login', json={'email': 'admin@example.com', 'password': PASSWORD}).status_code == 403
    assert client.post('/auth/register', json={**PROFILE, 'email': 'x@example.com', 'password': PASSWORD}).status_code == 403
    assert client.post('/auth/login', json={'email': 'admin@example.com', 'password': PASSWORD},
                       headers={'X-CSRF-Protection': '1', 'Origin': 'https://evil.example'}).status_code == 403


def test_login_rotation_logout_and_hashed_sessions(client):
    old_cookie = client.cookies.get(COOKIE_NAME)
    login(client)
    cookie = client.cookies.get(COOKIE_NAME)
    assert cookie != old_cookie
    with client.app.state.sessions() as session:
        records = session.scalars(select(LoginSession)).all()
        assert len(records) == 1
        assert records[0].token_hash == token_hash(cookie)
        assert records[0].token_hash != cookie
    assert client.post('/auth/logout').status_code == 204
    assert client.cookies.get(COOKIE_NAME) is None
    client.cookies.set(COOKIE_NAME, cookie)
    assert client.get('/auth/me').status_code == 401


@pytest.mark.parametrize('expiry', ['absolute', 'idle'])
def test_expired_session_rejected(client, expiry):
    with client.app.state.sessions() as session:
        record = session.scalar(select(LoginSession))
        if expiry == 'absolute':
            record.expires_at = now() - timedelta(seconds=1)
        else:
            record.last_seen_at = now() - timedelta(minutes=31)
        session.commit()
    assert client.get('/auth/me').status_code == 401
    assert client.post('/toppings', json={'name': 'Olives'}).status_code == 401


def test_invalid_login_and_cookie(client):
    for email in ['admin@example.com', 'missing@example.com']:
        response = client.post('/auth/login', json={'email': email, 'password': 'wrong'}, headers={'X-CSRF-Protection': '1'})
        assert response.status_code == 401
        assert response.json()['detail'] == 'Invalid email or password.'
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, 'fake')
    assert client.get('/auth/me').status_code == 401


def test_role_change_and_disabling_revoke_sessions(client):
    staff = login(client, 'staff@example.com')
    staff_cookie = client.cookies.get(COOKIE_NAME)
    client.cookies.clear()  # Keep staff session active in a separate browser.
    login(client)
    response = client.patch(f"/admin/users/{staff['id']}/access", json={'role': 'customer', 'active': True})
    assert response.status_code == 200
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, staff_cookie)
    assert client.get('/auth/me').status_code == 401
    login(client, 'staff@example.com')
    assert client.get('/inventory').status_code == 403
    client.cookies.clear()
    login(client)
    assert client.patch(f"/admin/users/{staff['id']}/access", json={'role': 'customer', 'active': False}).status_code == 200
    assert client.post('/auth/login', json={'email': 'staff@example.com', 'password': PASSWORD}, headers={'X-CSRF-Protection': '1'}).status_code == 401
    assert client.patch('/admin/users/1/access', json={'role': 'customer', 'active': False}).status_code == 409


def test_password_change_revokes_all_sessions_and_profile_is_safe(client):
    login(client, 'customer@example.com')
    first_cookie = client.cookies.get(COOKIE_NAME)
    client.cookies.clear()
    login(client, 'customer@example.com')
    assert client.put('/auth/profile', json={**PROFILE, 'name': 'Changed'}).status_code == 200
    assert client.put('/auth/profile', json={**PROFILE, 'role': 'admin'}).status_code == 422
    assert client.post('/auth/change-password', json={'current_password': PASSWORD, 'new_password': 'New-password-123'}).status_code == 204
    client.cookies.set(COOKIE_NAME, first_cookie)
    assert client.get('/auth/me').status_code == 401


def test_secure_cookie_defaults_and_openapi(client):
    # Switch transport to HTTPS to exercise the secure default.
    app = create_app('sqlite:///:memory:')
    with TestClient(app, base_url='https://testserver') as secure_client:
        assert register(secure_client).status_code == 201
        response = secure_client.post('/auth/login', json={'email': 'new@example.com', 'password': PASSWORD}, headers={'X-CSRF-Protection': '1'})
        cookie = response.headers['set-cookie'].lower()
        assert 'httponly' in cookie and 'secure' in cookie and 'samesite=lax' in cookie
        assert 'domain=' not in cookie
        assert secure_client.get('/auth/me').status_code == 200
        assert response.headers['cache-control'] == 'no-store'
        schema = secure_client.get('/openapi.json').json()
        assert schema['components']['securitySchemes']['APIKeyCookie']['in'] == 'cookie'
        headers = schema['paths']['/orders']['post']['parameters']
        assert any(p['name'] == 'X-CSRF-Token' for p in headers)


def legacy_database(path):
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL, address VARCHAR NOT NULL,
          phone_number VARCHAR NOT NULL, email VARCHAR UNIQUE, dine_in_name VARCHAR NOT NULL,
          admin BOOLEAN NOT NULL DEFAULT 0 CONSTRAINT admin_boolean CHECK (admin IN (0, 1)));
        CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
          status VARCHAR NOT NULL DEFAULT 'order_received', order_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP);
        INSERT INTO users VALUES (1, 'Legacy', 'Main', '555', 'Legacy@Example.com', 'Legacy', 1);
        INSERT INTO orders (id, user_id) VALUES (1, 1);
        ''')


def test_migration_backup_preserves_history_and_requires_provisioning(tmp_path):
    path = tmp_path / 'legacy.db'
    legacy_database(path)
    with pytest.raises(RuntimeError, match='migrate_auth'):
        with TestClient(create_app(f'sqlite:///{path}')):
            pass
    backup = migrate_auth(path)
    assert backup.is_file()
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT admin FROM users').fetchone() == (1,)
    assert migrate_auth(path) is None
    with TestClient(create_app(f'sqlite:///{path}', cookie_secure=False)) as client:
        with client.app.state.sessions() as session:
            user = session.get(User, 1)
            assert user.role == 'admin' and user.email == 'legacy@example.com'
            assert user.password_hash is None
            assert user.orders[0].created_by_user_id is None
            assert user.orders[0].user_id == 1
            provision_account(session, user.email, PASSWORD, 'admin', 'Legacy', existing=True)
        user = login(client, 'legacy@example.com')
        assert user['must_change_password']
        assert client.get('/orders').status_code == 403


def test_migration_rejects_duplicate_normalized_emails_without_changes(tmp_path):
    path = tmp_path / 'legacy.db'
    legacy_database(path)
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO users VALUES (2, 'Other', 'Main', '555', 'legacy@example.com', 'Other', 0)")
    with pytest.raises(ValueError, match='duplicate emails'):
        migrate_auth(path)
    with sqlite3.connect(path) as db:
        assert 'role' not in {row[1] for row in db.execute('PRAGMA table_info(users)')}


def test_provision_account_requires_explicit_reset(client):
    with client.app.state.sessions() as session:
        with pytest.raises(ValueError, match='already exists'):
            provision_account(session, 'admin@example.com', PASSWORD, 'admin', 'Admin')
        provision_account(session, 'admin@example.com', PASSWORD, 'admin', 'Admin', existing=True)
    assert client.get('/auth/me').status_code == 401
