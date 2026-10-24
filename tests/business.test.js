import test from 'node:test';
import assert from 'node:assert/strict';
import { SIZES } from '../js/config.js';
import { unitPrice, lineTotal, totals, ingredientUsage } from '../js/utils/currency.js';
import { checkoutErrors } from '../js/utils/validation.js';
import { store } from '../js/services/store.js';
import { cartService } from '../js/services/cartService.js';
import { orderService, estimateMinutes } from '../js/services/orderService.js';
import { rewardsService } from '../js/services/rewardsService.js';
import { aiSupportService } from '../js/services/aiSupportService.js';
const pizza = (size = 'large', toppings = [], quantity = 1) => ({
  kind: 'pizza',
  size,
  toppings,
  quantity,
  instructions: '',
});
const customer = {
  firstName: 'Test',
  lastName: 'Demo',
  email: 'test@example.test',
  phone: '202-555-0111',
  type: 'pickup',
  payment: 'demo',
};
test('required pizza and drink prices are exact for every size', () => {
  for (const [size, base, topping, drink] of [
    ['small', 500, 100, 100],
    ['medium', 700, 200, 200],
    ['large', 900, 300, 300],
  ]) {
    assert.equal(unitPrice(pizza(size)), base);
    assert.equal(unitPrice(pizza(size, ['pepperoni', 'mushrooms'])), base + 2 * topping);
    assert.equal(unitPrice({ kind: 'drink', size, drinkId: 'cola' }), drink);
  }
  assert.equal(lineTotal(pizza('large', ['pepperoni', 'mushrooms'], 2)), 3000);
});
test('quantity, size and topping validation reject malformed orders', () => {
  for (const q of [0, -1, 1.5, 21, NaN]) assert.throws(() => lineTotal(pizza('large', [], q)));
  assert.throws(() => unitPrice(pizza('giant')));
  assert.throws(() => unitPrice(pizza('large', ['bad'])));
  assert.throws(() => unitPrice(pizza('large', ['pepperoni', 'pepperoni'])));
});
test('totals round tax once, apply discount and delivery in integer cents', () => {
  assert.deepEqual(
    totals([pizza('large', ['pepperoni', 'mushrooms'])], { type: 'delivery', discountCents: 500 }),
    { subtotal: 1500, discount: 500, tax: 83, delivery: 300, total: 1383 },
  );
});
test('recipe portions are independent of price and include extra cheese', () => {
  for (const [size, portion] of [
    ['small', 0.25],
    ['medium', 0.5],
    ['large', 1],
  ]) {
    const usage = ingredientUsage([pizza(size, [], 2)]);
    assert.equal(usage.marinara, portion * 2);
    assert.equal(usage.cheese, portion * 2);
  }
  assert.deepEqual(
    ingredientUsage([
      pizza('large', ['extra-cheese', 'pepperoni']),
      { kind: 'drink', size: 'small', drinkId: 'tea', quantity: 2 },
    ]),
    { marinara: 1, cheese: 1.5, pepperoni: 0.5, 'drink-tea': 2 },
  );
});
test('checkout only requires addresses for delivery and rejects bad contacts', () => {
  assert.deepEqual(checkoutErrors(customer), {});
  assert.equal(Object.keys(checkoutErrors({ ...customer, type: 'delivery' })).length, 4);
  assert.ok(checkoutErrors({ ...customer, email: 'bad', phone: '123' }).email);
  assert.ok(checkoutErrors({ ...customer, email: 'bad', phone: '123' }).phone);
});
test('estimation increases with queue, quantities and delivery', () => {
  const base = estimateMinutes([pizza()], 'pickup', 0);
  assert.ok(estimateMinutes([pizza()], 'delivery', 0) > base);
  assert.ok(estimateMinutes([pizza('large', [], 3)], 'pickup', 3) > base);
});
test('cart edit/remove and successful order commit stock, points and idempotency', () => {
  store.reset();
  cartService.add(pizza('large', ['pepperoni']));
  const id = cartService.list()[0].id;
  cartService.update(id, { quantity: 2, toppings: ['pepperoni', 'mushrooms'] });
  assert.equal(lineTotal(cartService.list()[0]), 3000);
  cartService.add({ kind: 'drink', size: 'small', drinkId: 'cola', quantity: 1 });
  cartService.remove(cartService.list()[1].id);
  const before = store.read();
  const order = orderService.place(customer, 'test-idempotency');
  assert.equal(order.total, 3248);
  assert.equal(
    store.read().ingredients.find((i) => i.id === 'marinara').quantity,
    before.ingredients.find((i) => i.id === 'marinara').quantity - 2,
  );
  assert.equal(store.read().rewards.c1, before.rewards.c1 + 32);
  assert.equal(cartService.list().length, 0);
  assert.equal(orderService.place(customer, 'test-idempotency').id, order.id);
  const stock = store.read().ingredients.find((i) => i.id === 'cheese').quantity;
  orderService.advance(order.id);
  assert.equal(store.read().ingredients.find((i) => i.id === 'cheese').quantity, stock);
});
test('insufficient stock rolls back order, cart and rewards together', () => {
  store.reset();
  cartService.add(pizza('large', ['jalapenos']));
  const before = store.read();
  assert.throws(() => orderService.place(customer, 'bad-stock'), /Not enough/);
  assert.deepEqual(store.read(), before);
});
test('rewards cannot redeem without points and eligibility is rechecked', () => {
  store.reset();
  store.transact((s) => (s.rewards.c1 = 20));
  assert.throws(() => rewardsService.apply('REWARD5'), /Not enough/);
  store.transact((s) => (s.rewards.c1 = 160));
  rewardsService.apply('REWARD5');
  cartService.add(pizza());
  const order = orderService.place(customer, 'reward-order');
  assert.equal(order.discount, 500);
  assert.equal(store.read().rewards.c1, 64);
});
test('promo minimum, empty cart and duplicate ids are enforced', () => {
  store.reset();
  assert.throws(() => orderService.place(customer, 'empty'), /empty/);
  cartService.add(pizza('small'));
  rewardsService.apply('WELCOME5');
  assert.throws(() => orderService.place(customer, 'minimum'), /minimum/);
});
test('automated assistant escalates safety, payments, humans and uncertainty', async () => {
  for (const message of [
    'allergy complaint',
    'refund this payment',
    'I want a human',
    'something unrecognized',
  ]) {
    const reply = await aiSupportService.reply(message);
    assert.equal(reply.escalate, true);
  }
  assert.equal((await aiSupportService.reply('pizza prices')).escalate, undefined);
});
