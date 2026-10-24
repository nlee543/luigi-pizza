// All money is integer cents; recipes use cups or units, never prices.
export const CONFIG = Object.freeze({
  taxRate: 0.0825,
  deliveryFeeCents: 300,
  pointsPerDollar: 1,
  pageSize: 6,
  storageKey: 'luigis-demo-v1',
  branchId: 'downtown',
  hours: '10:00 AM – 11:00 PM',
  maxQuantity: 20,
});
export const SIZES = Object.freeze({
  small: {
    name: 'Small',
    diameter: 8,
    baseCents: 500,
    toppingCents: 100,
    portionCups: 0.25,
    drinkCents: 100,
  },
  medium: {
    name: 'Medium',
    diameter: 12,
    baseCents: 700,
    toppingCents: 200,
    portionCups: 0.5,
    drinkCents: 200,
  },
  large: {
    name: 'Large',
    diameter: 14,
    baseCents: 900,
    toppingCents: 300,
    portionCups: 1,
    drinkCents: 300,
  },
});
export const TOPPINGS = [
  ['pepperoni', 'Pepperoni', 'Meat'],
  ['sausage', 'Sausage', 'Meat'],
  ['bacon', 'Bacon', 'Meat'],
  ['ham', 'Ham', 'Meat'],
  ['chicken', 'Chicken', 'Meat'],
  ['mushrooms', 'Mushrooms', 'Vegetables'],
  ['onions', 'Onions', 'Vegetables'],
  ['peppers', 'Green peppers', 'Vegetables'],
  ['olives', 'Black olives', 'Vegetables'],
  ['jalapenos', 'Jalapeños', 'Vegetables'],
  ['pineapple', 'Pineapple', 'Vegetables'],
  ['extra-cheese', 'Extra cheese', 'Cheese'],
].map(([id, name, category]) => ({
  id,
  name,
  category,
  ingredientId: id === 'extra-cheese' ? 'cheese' : id,
  portions: { small: 0.125, medium: 0.25, large: 0.5 },
}));
export const DRINKS = [
  { id: 'cola', name: 'Classic cola' },
  { id: 'lemon', name: 'Lemon-lime soda' },
  { id: 'tea', name: 'Iced tea' },
  { id: 'water', name: 'Sparkling water' },
];
export const FEATURED = [
  {
    id: 'classic',
    name: 'The Classic',
    tag: 'THE ORIGINAL',
    description: 'Marinara, melty cheese, and a golden crust. Sometimes simple is everything.',
    toppings: [],
  },
  {
    id: 'pepperoni',
    name: 'Pepperoni Club',
    tag: 'CROWD FAVORITE',
    description: 'Our classic base with plenty of pepperoni. Your Friday-night go-to.',
    toppings: ['pepperoni'],
  },
  {
    id: 'garden',
    name: 'Garden Party',
    tag: 'FRESH PICK',
    description: 'Mushrooms, green peppers, and onions. Big flavor, all vegetables.',
    toppings: ['mushrooms', 'peppers', 'onions'],
  },
];
export const STATUS = ['Order Received', 'Preparing', 'Baking', 'Quality Check'];
export const orderSteps = (type) => [
  ...STATUS,
  type === 'delivery' ? 'Out for Delivery' : 'Ready for Pickup',
  'Completed',
];
