import { SIZES, TOPPINGS, DRINKS, CONFIG } from '../config.js';
export const money = (cents) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(cents / 100);
export function validQuantity(value) {
  const n = Number(value);
  if (!Number.isInteger(n) || n < 1 || n > CONFIG.maxQuantity)
    throw new Error('Quantity must be a whole number from 1 to 20.');
  return n;
}
export function unitPrice(item) {
  const size = SIZES[item.size];
  if (!size) throw new Error('Choose a valid size.');
  if (item.kind === 'drink') {
    if (!DRINKS.some((d) => d.id === item.drinkId)) throw new Error('Choose a valid drink.');
    return size.drinkCents;
  }
  if (item.kind !== 'pizza' || !Array.isArray(item.toppings)) throw new Error('Invalid menu item.');
  if (
    new Set(item.toppings).size !== item.toppings.length ||
    item.toppings.some((t) => !TOPPINGS.some((x) => x.id === t))
  )
    throw new Error('Invalid toppings.');
  return size.baseCents + item.toppings.length * size.toppingCents;
}
export const lineTotal = (item) => unitPrice(item) * validQuantity(item.quantity);
export function totals(items, { type = 'pickup', discountCents = 0 } = {}) {
  const subtotal = items.reduce((sum, i) => sum + lineTotal(i), 0);
  const discount = Math.min(subtotal, Math.max(0, Math.round(discountCents)));
  const tax = Math.round((subtotal - discount) * CONFIG.taxRate);
  const delivery = type === 'delivery' && items.length ? CONFIG.deliveryFeeCents : 0;
  return { subtotal, discount, tax, delivery, total: subtotal - discount + tax + delivery };
}
export function ingredientUsage(items) {
  const usage = {};
  const add = (id, amount) => {
    usage[id] = (usage[id] || 0) + amount;
  };
  for (const item of items) {
    unitPrice(item);
    const quantity = validQuantity(item.quantity);
    if (item.kind === 'drink') {
      add('drink-' + item.drinkId, quantity);
      continue;
    }
    add('marinara', SIZES[item.size].portionCups * quantity);
    add('cheese', SIZES[item.size].portionCups * quantity);
    for (const id of item.toppings) {
      const topping = TOPPINGS.find((t) => t.id === id);
      add(topping.ingredientId, topping.portions[item.size] * quantity);
    }
  }
  return usage;
}
