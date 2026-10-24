-- SQLite 3. Foreign keys must be enabled on EVERY application connection.
PRAGMA foreign_keys = ON;
BEGIN;
CREATE TABLE branches (
 branch_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, street TEXT NOT NULL,
 city TEXT NOT NULL, state TEXT NOT NULL CHECK(length(state)=2), zip TEXT NOT NULL,
 opens_at TEXT NOT NULL DEFAULT '10:00', closes_at TEXT NOT NULL DEFAULT '23:00', active INTEGER NOT NULL DEFAULT 1 CHECK(active IN(0,1))
);
CREATE TABLE customers (
 customer_id INTEGER PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
 email TEXT NOT NULL UNIQUE COLLATE NOCASE, phone TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE customer_addresses (
 address_id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
 street TEXT NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL CHECK(length(state)=2), zip TEXT NOT NULL, label TEXT NOT NULL DEFAULT 'Home'
);
CREATE TABLE employee_roles (role_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE CHECK(name IN('Administrator','Branch Employee')));
CREATE TABLE employees (
 employee_id INTEGER PRIMARY KEY, branch_id INTEGER NOT NULL REFERENCES branches(branch_id), role_id INTEGER NOT NULL REFERENCES employee_roles(role_id),
 first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, phone TEXT NOT NULL,
 position TEXT NOT NULL, hire_date TEXT NOT NULL, employment_status TEXT NOT NULL CHECK(employment_status IN('Active','Inactive'))
);
CREATE TABLE employee_shifts (
 shift_id INTEGER PRIMARY KEY, employee_id INTEGER NOT NULL REFERENCES employees(employee_id), branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
 clock_in TEXT NOT NULL, clock_out TEXT,
 verified_by INTEGER REFERENCES employees(employee_id), verified_at TEXT,
 CHECK(clock_out IS NULL OR clock_out>=clock_in),
 CHECK((verified_by IS NULL AND verified_at IS NULL) OR (verified_by IS NOT NULL AND verified_at IS NOT NULL AND clock_out IS NOT NULL))
);
CREATE UNIQUE INDEX idx_one_open_shift ON employee_shifts(employee_id) WHERE clock_out IS NULL;
-- Restricted tables: expose through payroll-authorized server endpoints only.
CREATE TABLE employee_pay (
 pay_id INTEGER PRIMARY KEY, employee_id INTEGER NOT NULL REFERENCES employees(employee_id), hourly_rate_cents INTEGER NOT NULL CHECK(hourly_rate_cents>=0),
 effective_from TEXT NOT NULL, effective_to TEXT, UNIQUE(employee_id,effective_from), CHECK(effective_to IS NULL OR effective_to>=effective_from)
);
CREATE TABLE employee_benefits (
 benefit_id INTEGER PRIMARY KEY, employee_id INTEGER NOT NULL REFERENCES employees(employee_id), benefit_type TEXT NOT NULL,
 enrollment_date TEXT NOT NULL, end_date TEXT, CHECK(end_date IS NULL OR end_date>=enrollment_date)
);
CREATE TABLE pizza_sizes (
 size_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE CHECK(name IN('Small','Medium','Large')), diameter_inches INTEGER NOT NULL CHECK(diameter_inches>0),
 base_price_cents INTEGER NOT NULL CHECK(base_price_cents>=0), topping_price_cents INTEGER NOT NULL CHECK(topping_price_cents>=0),
 drink_price_cents INTEGER NOT NULL CHECK(drink_price_cents>=0)
);
CREATE TABLE menu_items (
 menu_item_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, product_type TEXT NOT NULL CHECK(product_type IN('pizza','drink')), active INTEGER NOT NULL DEFAULT 1 CHECK(active IN(0,1))
);
CREATE TABLE toppings (topping_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1 CHECK(active IN(0,1)));
CREATE TABLE ingredients (ingredient_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL, unit TEXT NOT NULL CHECK(unit IN('cups','units')));
CREATE TABLE suppliers (supplier_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, contact_email TEXT);
CREATE TABLE inventory (
 branch_id INTEGER NOT NULL REFERENCES branches(branch_id), ingredient_id INTEGER NOT NULL REFERENCES ingredients(ingredient_id),
 quantity_on_hand REAL NOT NULL CHECK(quantity_on_hand>=0), reorder_level REAL NOT NULL CHECK(reorder_level>=0),
 last_restocked TEXT, supplier_id INTEGER REFERENCES suppliers(supplier_id), PRIMARY KEY(branch_id,ingredient_id)
);
-- One recipe per menu item/size OR topping/size. Component quantity uses ingredient.unit.
CREATE TABLE recipes (
 recipe_id INTEGER PRIMARY KEY, menu_item_id INTEGER REFERENCES menu_items(menu_item_id), topping_id INTEGER REFERENCES toppings(topping_id), size_id INTEGER NOT NULL REFERENCES pizza_sizes(size_id),
 CHECK((menu_item_id IS NOT NULL AND topping_id IS NULL) OR (menu_item_id IS NULL AND topping_id IS NOT NULL)),
 UNIQUE(menu_item_id,size_id), UNIQUE(topping_id,size_id)
);
CREATE TABLE recipe_components (
 recipe_id INTEGER NOT NULL REFERENCES recipes(recipe_id), ingredient_id INTEGER NOT NULL REFERENCES ingredients(ingredient_id), quantity REAL NOT NULL CHECK(quantity>0), PRIMARY KEY(recipe_id,ingredient_id)
);
CREATE TABLE promotions (
 promotion_id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE COLLATE NOCASE, name TEXT NOT NULL, description TEXT NOT NULL,
 discount_type TEXT NOT NULL CHECK(discount_type IN('fixed','percent')), discount_value INTEGER NOT NULL CHECK(discount_value>=0),
 minimum_subtotal_cents INTEGER NOT NULL DEFAULT 0 CHECK(minimum_subtotal_cents>=0), required_points INTEGER NOT NULL DEFAULT 0 CHECK(required_points>=0),
 starts_on TEXT NOT NULL, ends_on TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1 CHECK(active IN(0,1)), CHECK(ends_on>=starts_on), CHECK(discount_type!='percent' OR discount_value<=100)
);
CREATE TABLE orders (
 order_id INTEGER PRIMARY KEY, order_number TEXT NOT NULL UNIQUE, submission_key TEXT NOT NULL UNIQUE,
 customer_id INTEGER NOT NULL REFERENCES customers(customer_id), branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
 fulfillment_type TEXT NOT NULL CHECK(fulfillment_type IN('pickup','delivery')),
 status TEXT NOT NULL CHECK(status IN('Order Received','Preparing','Baking','Quality Check','Ready for Pickup','Out for Delivery','Completed')),
 placed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, estimated_ready_at TEXT NOT NULL, last_status_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 subtotal_cents INTEGER NOT NULL CHECK(subtotal_cents>=0), discount_cents INTEGER NOT NULL DEFAULT 0 CHECK(discount_cents>=0 AND discount_cents<=subtotal_cents),
 tax_cents INTEGER NOT NULL CHECK(tax_cents>=0), delivery_fee_cents INTEGER NOT NULL DEFAULT 0 CHECK(delivery_fee_cents>=0),
 total_cents INTEGER NOT NULL CHECK(total_cents=subtotal_cents-discount_cents+tax_cents+delivery_fee_cents),
 promotion_id INTEGER REFERENCES promotions(promotion_id), inventory_deducted INTEGER NOT NULL DEFAULT 0 CHECK(inventory_deducted IN(0,1)),
 CHECK((fulfillment_type='pickup' AND status!='Out for Delivery') OR (fulfillment_type='delivery' AND status!='Ready for Pickup'))
);
-- Immutable contact and address snapshots preserve an order when a profile changes.
CREATE TABLE order_contacts (
 order_id INTEGER PRIMARY KEY REFERENCES orders(order_id), first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL
);
CREATE TABLE order_delivery_addresses (
 order_id INTEGER PRIMARY KEY REFERENCES orders(order_id), street TEXT NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL CHECK(length(state)=2), zip TEXT NOT NULL
);
CREATE TABLE order_items (
 order_item_id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(order_id), menu_item_id INTEGER NOT NULL REFERENCES menu_items(menu_item_id),
 size_id INTEGER NOT NULL REFERENCES pizza_sizes(size_id), quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 20),
 unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents>=0), instructions TEXT NOT NULL DEFAULT '' CHECK(length(instructions)<=250)
);
CREATE TABLE order_item_toppings (
 order_item_id INTEGER NOT NULL REFERENCES order_items(order_item_id), topping_id INTEGER NOT NULL REFERENCES toppings(topping_id), charged_price_cents INTEGER NOT NULL CHECK(charged_price_cents>=0), PRIMARY KEY(order_item_id,topping_id)
);
CREATE TABLE order_status_events (event_id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(order_id), status TEXT NOT NULL, occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, employee_id INTEGER REFERENCES employees(employee_id));
CREATE TABLE inventory_movements (
 movement_id INTEGER PRIMARY KEY, branch_id INTEGER NOT NULL, ingredient_id INTEGER NOT NULL, order_id INTEGER REFERENCES orders(order_id),
 quantity_change REAL NOT NULL CHECK(quantity_change!=0), reason TEXT NOT NULL CHECK(reason IN('order','restock','adjustment','reversal')), occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(branch_id,ingredient_id) REFERENCES inventory(branch_id,ingredient_id)
);
CREATE UNIQUE INDEX idx_once_order_inventory ON inventory_movements(order_id,branch_id,ingredient_id) WHERE reason='order';
CREATE TABLE payments (
 payment_id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(order_id), payment_method TEXT NOT NULL CHECK(payment_method IN('demo_online','pay_at_store')),
 amount_cents INTEGER NOT NULL CHECK(amount_cents>=0), status TEXT NOT NULL CHECK(status IN('simulated','pending','paid','failed','refunded')), provider_reference TEXT UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE rewards_accounts (customer_id INTEGER PRIMARY KEY REFERENCES customers(customer_id), starting_points INTEGER NOT NULL DEFAULT 0 CHECK(starting_points>=0), joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE rewards_transactions (
 transaction_id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES rewards_accounts(customer_id), order_id INTEGER REFERENCES orders(order_id),
 points_change INTEGER NOT NULL CHECK(points_change!=0), transaction_type TEXT NOT NULL CHECK(transaction_type IN('earn','redeem','adjustment')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_once_reward_earn ON rewards_transactions(order_id) WHERE transaction_type='earn';
CREATE VIEW rewards_balances AS SELECT a.customer_id,a.starting_points+COALESCE(SUM(t.points_change),0) AS points_balance FROM rewards_accounts a LEFT JOIN rewards_transactions t ON a.customer_id=t.customer_id GROUP BY a.customer_id;
CREATE TABLE customer_promotions (
 customer_id INTEGER NOT NULL REFERENCES customers(customer_id), promotion_id INTEGER NOT NULL REFERENCES promotions(promotion_id), assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, redeemed_order_id INTEGER REFERENCES orders(order_id), PRIMARY KEY(customer_id,promotion_id)
);
CREATE TABLE support_tickets (
 ticket_id INTEGER PRIMARY KEY, ticket_number TEXT NOT NULL UNIQUE, customer_id INTEGER NOT NULL REFERENCES customers(customer_id), order_id INTEGER REFERENCES orders(order_id),
 customer_name_snapshot TEXT NOT NULL, issue_category TEXT NOT NULL, description TEXT NOT NULL, conversation_summary TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, escalation_status TEXT NOT NULL CHECK(escalation_status IN('Escalated','In Review','Resolved')), assigned_employee_id INTEGER REFERENCES employees(employee_id)
);
CREATE TABLE support_messages (
 message_id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL REFERENCES support_tickets(ticket_id), sender_type TEXT NOT NULL CHECK(sender_type IN('customer','assistant','representative')),
 message_text TEXT NOT NULL, sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_orders_branch_status_placed ON orders(branch_id,status,placed_at);
CREATE INDEX idx_orders_customer_placed ON orders(customer_id,placed_at);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_shifts_branch_clock ON employee_shifts(branch_id,clock_in);
CREATE INDEX idx_tickets_status_date ON support_tickets(escalation_status,created_at);
COMMIT;
-- Cross-row rules (nonempty orders, required delivery address, recipe deduction,
-- reward balances and authoritative totals) must be checked in one API transaction.
