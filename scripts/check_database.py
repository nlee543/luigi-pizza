"""Build a throwaway SQLite database and verify relationships and demo prices."""
from pathlib import Path
import sqlite3
root = Path(__file__).resolve().parents[1]
db = sqlite3.connect(':memory:')
db.executescript((root / 'database/schema.sql').read_text(encoding='utf-8'))
db.executescript((root / 'database/seed.sql').read_text(encoding='utf-8'))
assert db.execute('PRAGMA foreign_key_check').fetchall() == []
assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
assert db.execute('SELECT base_price_cents,topping_price_cents,drink_price_cents FROM pizza_sizes ORDER BY size_id').fetchall() == [(500,100,100),(700,200,200),(900,300,300)]
assert db.execute('SELECT quantity FROM recipe_components WHERE ingredient_id=1 ORDER BY recipe_id').fetchall() == [(0.25,),(0.5,),(1.0,)]
assert db.execute('SELECT COUNT(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id=o.order_id)').fetchone()[0] == 0
assert db.execute("SELECT COUNT(*) FROM orders o WHERE fulfillment_type='delivery' AND NOT EXISTS (SELECT 1 FROM order_delivery_addresses a WHERE a.order_id=o.order_id)").fetchone()[0] == 0
for order_id, subtotal in db.execute('SELECT order_id,subtotal_cents FROM orders'):
    actual = db.execute('SELECT SUM(quantity*unit_price_cents) FROM order_items WHERE order_id=?',(order_id,)).fetchone()[0]
    assert actual == subtotal, (order_id, actual, subtotal)
for query in ["UPDATE inventory SET quantity_on_hand=-1 WHERE ingredient_id=1", "INSERT INTO order_items VALUES(100,999,1,1,1,500,'')", "UPDATE orders SET total_cents=1 WHERE order_id=1", "INSERT INTO employee_shifts(shift_id,employee_id,branch_id,clock_in) VALUES(99,2,1,CURRENT_TIMESTAMP)", "UPDATE employee_shifts SET verified_by=1,verified_at=CURRENT_TIMESTAMP WHERE shift_id=1"]:
    try:
        db.execute(query)
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError('Expected database constraint failure: '+query)
tables=db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f'SQLite schema + seed verified: {len(tables)} tables; foreign keys, integrity, totals, portions, delivery addresses, nonempty orders, and constraints passed.')
