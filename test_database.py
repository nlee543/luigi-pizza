import sqlite3
import tempfile
import unittest
from pathlib import Path

from init_db import connect, initialize


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'test.db'
        initialize(self.path)
        self.db = connect(self.path)
        self.db.execute("INSERT INTO orders(channel,fulfillment,customer_name) VALUES('online','pickup','Test customer')")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def pizza(self):
        self.db.execute("INSERT INTO order_items(order_id,variant_id,item_name,size,quantity,unit_base_price_cents) VALUES(1,1,'Pizza','small',2,500)")
        self.db.execute("INSERT INTO order_item_toppings VALUES(1,1,'Pepperoni',100)")

    def test_totals_and_historical_prices(self):
        self.pizza()
        self.assertEqual(self.db.execute('SELECT * FROM order_totals').fetchone(), (1,1200,111,1311))
        self.db.execute('UPDATE menu_variants SET price_cents=9999')
        self.assertEqual(self.db.execute('SELECT total_cents FROM order_totals').fetchone()[0],1311)

    def test_rounding_and_empty_order(self):
        self.assertEqual(self.db.execute('SELECT total_cents FROM order_totals').fetchone()[0],0)
        self.db.execute("INSERT INTO order_items(order_id,variant_id,item_name,size,quantity,unit_base_price_cents) VALUES(1,1,'Pizza','small',1,500)")
        self.assertEqual(self.db.execute('SELECT tax_cents FROM order_totals').fetchone()[0],46)

    def test_constraints(self):
        for sql in (
            "INSERT INTO orders(channel,fulfillment,customer_name) VALUES('online','delivery','Test')",
            "INSERT INTO orders(channel,fulfillment,customer_name) VALUES('online','dine_in','Test')",
            "INSERT INTO order_items(order_id,variant_id,item_name,size,quantity,unit_base_price_cents) VALUES(999,1,'Pizza','small',1,500)",
            "INSERT INTO order_items(order_id,variant_id,item_name,size,quantity,unit_base_price_cents) VALUES(1,1,'Pizza','small',0,500)",
            "UPDATE menu_variants SET price_cents=1.5",
        ):
            with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)

    def test_drinks_cannot_have_toppings(self):
        drink = self.db.execute("SELECT v.variant_id FROM menu_variants v JOIN menu_items m USING(menu_item_id) WHERE m.kind='beverage' LIMIT 1").fetchone()[0]
        self.db.execute("INSERT INTO order_items VALUES(1,1,?,'Drink','small',1,100)",(drink,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO order_item_toppings VALUES(1,1,'Pepperoni',100)")

    def test_status_history(self):
        self.db.execute("UPDATE orders SET status='preparing' WHERE order_id=1")
        self.assertEqual(self.db.execute('SELECT status FROM order_status_history ORDER BY event_id').fetchall(), [('received',),('preparing',)])

    def test_inventory_and_payroll(self):
        self.pizza()
        self.db.execute("INSERT INTO ingredients VALUES(1,'Cheese','milligram',100)")
        self.db.execute("INSERT INTO inventory_movements(ingredient_id,reason,quantity_delta) VALUES(1,'opening',1000)")
        self.db.execute("INSERT INTO inventory_movements(ingredient_id,order_item_id,reason,quantity_delta) VALUES(1,1,'consumption',-250)")
        self.assertEqual(self.db.execute('SELECT quantity_on_hand FROM inventory_levels').fetchone()[0],750)
        self.db.execute("INSERT INTO employees VALUES(1,'Test employee','staff',1500,1)")
        self.db.execute("INSERT INTO shifts(employee_id,starts_at,ends_at,hourly_rate_cents,worked_minutes) VALUES(1,'2026-10-15 10:00:00','2026-10-15 12:00:00',1500,120)")
        self.assertEqual(self.db.execute('SELECT gross_pay_cents FROM payroll_summary').fetchone()[0],3000)

    def test_existing_database_is_preserved(self):
        with self.assertRaises(FileExistsError):
            initialize(self.path)

    def test_seed_and_integrity(self):
        self.assertEqual(self.db.execute('SELECT count(*) FROM menu_variants').fetchone()[0],12)
        self.assertEqual(self.db.execute('SELECT count(*) FROM toppings').fetchone()[0],9)
        self.assertEqual(self.db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])


if __name__ == '__main__':
    unittest.main()
