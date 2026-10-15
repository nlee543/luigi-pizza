BEGIN;
INSERT INTO store_hours VALUES
 (0,'10:00','23:00'),(1,'10:00','23:00'),(2,'10:00','23:00'),(3,'10:00','23:00'),
 (4,'10:00','23:00'),(5,'10:00','23:00'),(6,'10:00','23:00');
INSERT INTO kitchen_settings VALUES(1,2,8);
INSERT INTO menu_items(menu_item_id,name,kind) VALUES
 (1,'Regular crust pizza (marinara and cheese)','pizza'),
 (2,'Coca-Cola fountain drink','beverage'),(3,'Iced Tea','beverage'),(4,'Dr. Pepper','beverage');
-- Large topping price is provisional, as identified in the requirements.
INSERT INTO menu_variants(menu_item_id,size,diameter_inches,price_cents,topping_price_cents) VALUES
 (1,'small',12,500,100),(1,'medium',14,700,200),(1,'large',18,900,300);
INSERT INTO menu_variants(menu_item_id,size,price_cents)
SELECT m.menu_item_id,s.size,s.price FROM menu_items m
CROSS JOIN (SELECT 'small' AS size,100 AS price UNION ALL SELECT 'medium',200 UNION ALL SELECT 'large',300) s
WHERE m.kind='beverage';
INSERT INTO toppings(name) VALUES ('Pepperoni'),('Sausage'),('Beef'),('Green peppers'),('Jalapeños'),
 ('Pineapple'),('Onions'),('Black olives'),('Diced tomatoes');
-- No fabricated recipes, wages, customers, or opening stock.
COMMIT;
