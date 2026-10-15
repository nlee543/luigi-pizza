PRAGMA foreign_keys = ON;

BEGIN;
CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
INSERT INTO schema_version(version) VALUES (1);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
    phone TEXT,
    address TEXT,
    email TEXT,
    reward_number TEXT UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Credentials are separate from customer contact details; guests need no account.
CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL UNIQUE REFERENCES customers(customer_id),
    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('manager','staff')),
    hourly_rate_cents INTEGER NOT NULL CHECK(typeof(hourly_rate_cents)='integer' AND hourly_rate_cents >= 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE shifts (
    shift_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(employee_id),
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL CHECK(ends_at > starts_at),
    hourly_rate_cents INTEGER NOT NULL CHECK(typeof(hourly_rate_cents)='integer' AND hourly_rate_cents >= 0),
    worked_minutes INTEGER CHECK(typeof(worked_minutes)='integer' AND worked_minutes >= 0)
);
CREATE TABLE store_hours (
    weekday INTEGER PRIMARY KEY CHECK(weekday BETWEEN 0 AND 6),
    opens_at TEXT NOT NULL,
    closes_at TEXT NOT NULL CHECK(closes_at > opens_at)
);
CREATE TABLE kitchen_settings (
    settings_id INTEGER PRIMARY KEY CHECK(settings_id=1),
    large_pizza_capacity INTEGER NOT NULL CHECK(large_pizza_capacity > 0),
    bake_minutes INTEGER NOT NULL CHECK(bake_minutes > 0)
);
CREATE TABLE menu_items (
    menu_item_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK(kind IN ('pizza','beverage')),
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE menu_variants (
    variant_id INTEGER PRIMARY KEY,
    menu_item_id INTEGER NOT NULL REFERENCES menu_items(menu_item_id),
    size TEXT NOT NULL CHECK(size IN ('small','medium','large')),
    diameter_inches INTEGER CHECK(diameter_inches > 0),
    price_cents INTEGER NOT NULL CHECK(typeof(price_cents)='integer' AND price_cents >= 0),
    topping_price_cents INTEGER NOT NULL DEFAULT 0 CHECK(typeof(topping_price_cents)='integer' AND topping_price_cents >= 0),
    UNIQUE(menu_item_id,size)
);
CREATE TABLE toppings (
    topping_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
-- Each ingredient has one stock unit; recipe and movement quantities use that unit.
-- Integer subunits (e.g. milligrams) avoid floating-point quantity drift.
CREATE TABLE ingredients (
    ingredient_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    stock_unit TEXT NOT NULL,
    reorder_level INTEGER NOT NULL DEFAULT 0 CHECK(typeof(reorder_level)='integer' AND reorder_level >= 0)
);
CREATE TABLE base_recipes (
    variant_id INTEGER NOT NULL REFERENCES menu_variants(variant_id),
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(ingredient_id),
    quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity > 0),
    PRIMARY KEY(variant_id,ingredient_id)
);
CREATE TABLE topping_recipes (
    topping_id INTEGER NOT NULL REFERENCES toppings(topping_id),
    size TEXT NOT NULL CHECK(size IN ('small','medium','large')),
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(ingredient_id),
    quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity > 0),
    PRIMARY KEY(topping_id,size,ingredient_id)
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    entered_by INTEGER REFERENCES employees(employee_id),
    channel TEXT NOT NULL CHECK(channel IN ('phone','online','mobile')),
    fulfillment TEXT NOT NULL CHECK(fulfillment IN ('dine_in','pickup')),
    customer_name TEXT NOT NULL CHECK(length(trim(customer_name)) > 0),
    contact_phone TEXT,
    dine_in_name TEXT,
    status TEXT NOT NULL DEFAULT 'received' CHECK(status IN ('received','preparing','baking','ready','completed','cancelled')),
    tax_basis_points INTEGER NOT NULL DEFAULT 925 CHECK(typeof(tax_basis_points)='integer' AND tax_basis_points BETWEEN 0 AND 10000),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estimated_ready_at TEXT,
    CHECK(fulfillment <> 'dine_in' OR length(trim(coalesce(dine_in_name,''))) > 0)
);
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    variant_id INTEGER NOT NULL REFERENCES menu_variants(variant_id),
    item_name TEXT NOT NULL,
    size TEXT NOT NULL CHECK(size IN ('small','medium','large')),
    quantity INTEGER NOT NULL CHECK(typeof(quantity)='integer' AND quantity > 0),
    unit_base_price_cents INTEGER NOT NULL CHECK(typeof(unit_base_price_cents)='integer' AND unit_base_price_cents >= 0)
);
CREATE TABLE order_item_toppings (
    order_item_id INTEGER NOT NULL REFERENCES order_items(order_item_id),
    topping_id INTEGER NOT NULL REFERENCES toppings(topping_id),
    topping_name TEXT NOT NULL,
    unit_price_cents INTEGER NOT NULL CHECK(typeof(unit_price_cents)='integer' AND unit_price_cents >= 0),
    PRIMARY KEY(order_item_id,topping_id)
);
CREATE TRIGGER pizza_toppings_insert BEFORE INSERT ON order_item_toppings
WHEN (SELECT m.kind FROM order_items oi JOIN menu_variants v ON v.variant_id=oi.variant_id
      JOIN menu_items m ON m.menu_item_id=v.menu_item_id WHERE oi.order_item_id=NEW.order_item_id) <> 'pizza'
BEGIN SELECT RAISE(ABORT,'Toppings require a pizza'); END;
CREATE TRIGGER pizza_toppings_update BEFORE UPDATE ON order_item_toppings
WHEN (SELECT m.kind FROM order_items oi JOIN menu_variants v ON v.variant_id=oi.variant_id
      JOIN menu_items m ON m.menu_item_id=v.menu_item_id WHERE oi.order_item_id=NEW.order_item_id) <> 'pizza'
BEGIN SELECT RAISE(ABORT,'Toppings require a pizza'); END;
CREATE TRIGGER order_item_variant_update BEFORE UPDATE OF variant_id ON order_items
WHEN EXISTS(SELECT 1 FROM order_item_toppings WHERE order_item_id=OLD.order_item_id)
 AND (SELECT m.kind FROM menu_variants v JOIN menu_items m ON m.menu_item_id=v.menu_item_id WHERE v.variant_id=NEW.variant_id) <> 'pizza'
BEGIN SELECT RAISE(ABORT,'An item with toppings must remain a pizza'); END;
CREATE TABLE order_status_history (
    event_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    status TEXT NOT NULL CHECK(status IN ('received','preparing','baking','ready','completed','cancelled')),
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER order_created AFTER INSERT ON orders
BEGIN INSERT INTO order_status_history(order_id,status) VALUES(NEW.order_id,NEW.status); END;
CREATE TRIGGER order_status_changed AFTER UPDATE OF status ON orders WHEN OLD.status <> NEW.status
BEGIN INSERT INTO order_status_history(order_id,status) VALUES(NEW.order_id,NEW.status); END;
CREATE TABLE inventory_movements (
    movement_id INTEGER PRIMARY KEY,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(ingredient_id),
    order_item_id INTEGER REFERENCES order_items(order_item_id),
    reason TEXT NOT NULL CHECK(reason IN ('opening','purchase','consumption','waste','adjustment','return')),
    quantity_delta INTEGER NOT NULL CHECK(typeof(quantity_delta)='integer' AND quantity_delta <> 0),
    cost_cents INTEGER NOT NULL DEFAULT 0 CHECK(typeof(cost_cents)='integer' AND cost_cents >= 0),
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(reason NOT IN ('consumption','waste') OR quantity_delta < 0),
    CHECK(reason NOT IN ('opening','purchase','return') OR quantity_delta > 0),
    CHECK(reason <> 'consumption' OR order_item_id IS NOT NULL)
);
CREATE TABLE payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    kind TEXT NOT NULL CHECK(kind IN ('payment','refund')),
    method TEXT NOT NULL CHECK(method IN ('cash','card')),
    amount_cents INTEGER NOT NULL CHECK(typeof(amount_cents)='integer' AND amount_cents > 0),
    external_reference TEXT UNIQUE,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE expenses (
    expense_id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK(typeof(amount_cents)='integer' AND amount_cents >= 0),
    incurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX orders_customer_date ON orders(customer_id,created_at);
CREATE INDEX orders_status_date ON orders(status,created_at);
CREATE INDEX order_items_order ON order_items(order_id);
CREATE INDEX status_history_order ON order_status_history(order_id,event_id);
CREATE INDEX inventory_ingredient ON inventory_movements(ingredient_id);
CREATE INDEX inventory_order_item ON inventory_movements(order_item_id);
CREATE INDEX payments_order ON payments(order_id);
CREATE INDEX shifts_employee ON shifts(employee_id,starts_at);

CREATE VIEW order_line_totals AS
SELECT oi.*, oi.quantity * (oi.unit_base_price_cents + coalesce(
    (SELECT sum(t.unit_price_cents) FROM order_item_toppings t WHERE t.order_item_id=oi.order_item_id),0)) AS line_total_cents
FROM order_items oi;
-- Round once per order, half up, using integer arithmetic.
CREATE VIEW order_totals AS
WITH subtotals AS (
 SELECT o.order_id,o.tax_basis_points,coalesce(sum(l.line_total_cents),0) AS subtotal_cents
 FROM orders o LEFT JOIN order_line_totals l ON l.order_id=o.order_id GROUP BY o.order_id
), taxed AS (
 SELECT *, (subtotal_cents * tax_basis_points + 5000) / 10000 AS tax_cents FROM subtotals
)
SELECT order_id,subtotal_cents,tax_cents,subtotal_cents+tax_cents AS total_cents FROM taxed;
CREATE VIEW inventory_levels AS
SELECT i.*,coalesce(sum(m.quantity_delta),0) AS quantity_on_hand
FROM ingredients i LEFT JOIN inventory_movements m ON m.ingredient_id=i.ingredient_id GROUP BY i.ingredient_id;
CREATE VIEW payroll_summary AS
SELECT employee_id,sum(worked_minutes) AS worked_minutes,
       sum((worked_minutes * hourly_rate_cents + 30) / 60) AS gross_pay_cents
FROM shifts WHERE worked_minutes IS NOT NULL GROUP BY employee_id;
CREATE VIEW daily_sales AS
SELECT date(o.created_at) AS sales_date,count(*) AS order_count,sum(t.subtotal_cents) AS sales_cents,
       sum(t.tax_cents) AS tax_cents,sum(t.total_cents) AS total_cents
FROM orders o JOIN order_totals t ON t.order_id=o.order_id WHERE o.status='completed' GROUP BY date(o.created_at);
COMMIT;
