PRAGMA foreign_keys = ON;
BEGIN;
INSERT INTO branches VALUES (1,'Downtown','100 Example Avenue','Chicago','IL','60601','10:00','23:00',1),(2,'Riverside','200 Sample Street','Chicago','IL','60607','10:00','23:00',1);
INSERT INTO customers(customer_id,first_name,last_name,email,phone) VALUES(1,'Alex','Morgan','alex@example.test','202-555-0142'),(2,'Jamie','Rivera','jamie@example.test','202-555-0116'),(3,'Casey','Taylor','casey@example.test','202-555-0193');
INSERT INTO customer_addresses VALUES(1,1,'120 Demo Lane','Chicago','IL','60601','Home');
INSERT INTO employee_roles VALUES(1,'Administrator'),(2,'Branch Employee');
INSERT INTO employees VALUES(1,1,1,'Luigi','Demo','luigi@example.test','202-555-0100','Manager','2023-03-01','Active'),(2,1,2,'Sam','Demo','sam@example.test','202-555-0101','Kitchen lead','2024-08-12','Active'),(3,2,2,'Robin','Demo','robin@example.test','202-555-0102','Shift lead','2025-02-04','Active');
INSERT INTO employee_shifts(shift_id,employee_id,branch_id,clock_in,clock_out) VALUES(1,2,1,datetime('now','-3 hours'),NULL),(2,1,1,datetime('now','-8 hours'),datetime('now','-1 hour')),(3,3,2,datetime('now','-4 hours'),NULL);
INSERT INTO employee_pay VALUES(1,1,2500,'2026-01-01',NULL),(2,2,1800,'2026-01-01',NULL),(3,3,1900,'2026-01-01',NULL);
INSERT INTO employee_benefits VALUES(1,1,'Fictional health plan','2026-01-01',NULL),(2,2,'Fictional meal benefit','2026-01-01',NULL);
INSERT INTO pizza_sizes VALUES(1,'Small',8,500,100,100),(2,'Medium',12,700,200,200),(3,'Large',14,900,300,300);
INSERT INTO menu_items VALUES(1,'Custom pizza','pizza',1),(2,'Classic cola','drink',1),(3,'Lemon-lime soda','drink',1),(4,'Iced tea','drink',1),(5,'Sparkling water','drink',1);
INSERT INTO toppings VALUES(1,'Pepperoni','Meat',1),(2,'Sausage','Meat',1),(3,'Bacon','Meat',1),(4,'Ham','Meat',1),(5,'Chicken','Meat',1),(6,'Mushrooms','Vegetables',1),(7,'Onions','Vegetables',1),(8,'Green peppers','Vegetables',1),(9,'Black olives','Vegetables',1),(10,'Jalapeños','Vegetables',1),(11,'Pineapple','Vegetables',1),(12,'Extra cheese','Cheese',1);
INSERT INTO ingredients VALUES(1,'Marinara sauce','Base','cups'),(2,'Cheese','Base','cups'),(3,'Pepperoni','Meat','cups'),(4,'Sausage','Meat','cups'),(5,'Bacon','Meat','cups'),(6,'Ham','Meat','cups'),(7,'Chicken','Meat','cups'),(8,'Mushrooms','Vegetables','cups'),(9,'Onions','Vegetables','cups'),(10,'Green peppers','Vegetables','cups'),(11,'Black olives','Vegetables','cups'),(12,'Jalapeños','Vegetables','cups'),(13,'Pineapple','Vegetables','cups'),(14,'Classic cola','Drinks','units'),(15,'Lemon-lime soda','Drinks','units'),(16,'Iced tea','Drinks','units'),(17,'Sparkling water','Drinks','units');
INSERT INTO suppliers VALUES(1,'Fictional Fresh Supply','fresh@example.test'),(2,'Demo Beverage Co.','beverages@example.test');
INSERT INTO inventory SELECT 1,ingredient_id,CASE ingredient_id WHEN 1 THEN 48 WHEN 2 THEN 62 WHEN 4 THEN 3 WHEN 12 THEN 0 WHEN 16 THEN 5 ELSE 30 END,CASE WHEN ingredient_id>=14 THEN 10 WHEN ingredient_id<=2 THEN 15 ELSE 4 END,datetime('now','-1 day'),CASE WHEN ingredient_id>=14 THEN 2 ELSE 1 END FROM ingredients;
INSERT INTO recipes(recipe_id,menu_item_id,size_id) SELECT size_id,1,size_id FROM pizza_sizes;
INSERT INTO recipe_components SELECT size_id,1,CASE size_id WHEN 1 THEN 0.25 WHEN 2 THEN 0.5 ELSE 1 END FROM pizza_sizes;
INSERT INTO recipe_components SELECT size_id,2,CASE size_id WHEN 1 THEN 0.25 WHEN 2 THEN 0.5 ELSE 1 END FROM pizza_sizes;
INSERT INTO recipes(recipe_id,topping_id,size_id) SELECT 10+t.topping_id*3+s.size_id,t.topping_id,s.size_id FROM toppings t CROSS JOIN pizza_sizes s;
INSERT INTO recipe_components SELECT r.recipe_id,CASE r.topping_id WHEN 12 THEN 2 ELSE r.topping_id+2 END,CASE r.size_id WHEN 1 THEN 0.125 WHEN 2 THEN 0.25 ELSE 0.5 END FROM recipes r WHERE r.topping_id IS NOT NULL;
INSERT INTO recipes(recipe_id,menu_item_id,size_id) SELECT 100+m.menu_item_id*3+s.size_id,m.menu_item_id,s.size_id FROM menu_items m CROSS JOIN pizza_sizes s WHERE m.product_type='drink';
INSERT INTO recipe_components SELECT recipe_id,menu_item_id+12,1 FROM recipes WHERE menu_item_id>=2;
INSERT INTO promotions VALUES(1,'WELCOME5','A little welcome','$5 off a $20 order.','fixed',500,2000,0,'2026-01-01','2027-12-31',1),(2,'REWARD5','Your next slice of joy','100 points for $5 off.','fixed',500,500,100,'2026-01-01','2027-12-31',1);
INSERT INTO orders VALUES
 (1,'LP-1041','seed-1',1,1,'delivery','Baking',datetime('now','-10 minutes'),datetime('now','+25 minutes'),datetime('now','-2 minutes'),1100,0,91,300,1491,NULL,1),
 (2,'LP-1042','seed-2',2,1,'pickup','Preparing',datetime('now','-8 minutes'),datetime('now','+20 minutes'),datetime('now','-3 minutes'),1200,0,99,0,1299,NULL,1),
 (3,'LP-1043','seed-3',3,1,'pickup','Order Received',datetime('now','-2 minutes'),datetime('now','+25 minutes'),datetime('now','-2 minutes'),1000,0,83,0,1083,NULL,1),
 (4,'LP-1044','seed-4',1,1,'pickup','Completed',datetime('now','-2 hours'),datetime('now','-90 minutes'),datetime('now','-85 minutes'),1500,0,124,0,1624,NULL,1),
 (5,'LP-1045','seed-5',2,1,'delivery','Completed',datetime('now','-3 hours'),datetime('now','-2 hours'),datetime('now','-2 hours'),2000,0,165,300,2465,NULL,1),
 (6,'LP-1046','seed-6',3,1,'pickup','Completed',datetime('now','-4 hours'),datetime('now','-3 hours'),datetime('now','-3 hours'),700,0,58,0,758,NULL,1);
INSERT INTO order_contacts SELECT o.order_id,c.first_name,c.last_name,c.email,c.phone FROM orders o JOIN customers c ON c.customer_id=o.customer_id;
INSERT INTO order_delivery_addresses VALUES(1,'120 Demo Lane','Chicago','IL','60601'),(5,'220 Fictional Road','Chicago','IL','60607');
INSERT INTO order_items VALUES(1,1,1,3,1,900,''),(2,1,2,2,1,200,''),(3,2,1,3,1,1200,''),(4,3,1,1,2,500,''),(5,4,1,3,1,1500,''),(6,5,1,1,4,500,''),(7,6,1,2,1,700,'');
INSERT INTO order_item_toppings VALUES(3,1,300),(5,1,300),(5,6,300);
INSERT INTO order_status_events(order_id,status,occurred_at) SELECT order_id,status,last_status_at FROM orders;
INSERT INTO payments(order_id,payment_method,amount_cents,status) SELECT order_id,'pay_at_store',total_cents,CASE WHEN status='Completed' THEN 'paid' ELSE 'pending' END FROM orders;
INSERT INTO rewards_accounts(customer_id,starting_points) VALUES(1,144),(2,54),(3,16);
INSERT INTO rewards_transactions(customer_id,order_id,points_change,transaction_type) VALUES(1,4,16,'earn'),(2,5,24,'earn'),(3,6,7,'earn');
INSERT INTO customer_promotions(customer_id,promotion_id) VALUES(1,1),(1,2),(2,1),(3,1);
INSERT INTO support_tickets VALUES(1,'TK-1001',2,5,'Jamie Rivera','Order issue','A topping was missing.','Customer asked for help with missing pepperoni.',datetime('now','-1 hour'),'Escalated',NULL);
INSERT INTO support_messages(ticket_id,sender_type,message_text) VALUES(1,'customer','A topping was missing.'),(1,'assistant','I will record the issue for a representative.');
-- Stock represents a post-order snapshot. Seeded historical orders are already deducted.
COMMIT;
