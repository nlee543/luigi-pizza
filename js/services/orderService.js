import { store, uid, page } from './store.js';
import { totals } from '../utils/currency.js';
import { ensureStock } from './inventoryService.js';
import { promotionFor, rewardsService } from './rewardsService.js';
import { checkoutErrors } from '../utils/validation.js';
import { orderSteps, CONFIG } from '../config.js';
import { apiClient } from './apiClient.js';
export function estimateMinutes(items, type, queue) {
  const pizzas = items.filter((i) => i.kind === 'pizza').reduce((n, i) => n + i.quantity, 0);
  const count = items.reduce((n, i) => n + i.quantity, 0);
  return (
    12 +
    pizzas * 3 +
    Math.ceil(count / 3) +
    Math.min(queue * 2, 20) +
    (type === 'delivery' ? 15 : 0)
  );
}
const submissions = new Map();
export const orderService = {
  place(data, submissionId) {
    if (apiClient.enabled())
      return apiClient
        .command('checkout', {
          customer: data,
          submissionId,
          items: store.read().cart,
          promotionId: store.read().selectedPromotion,
        })
        .then((order) => {
          store.transact((state) => {
            state.cart = [];
            state.selectedPromotion = null;
            state.lastOrderId = order.id;
          });
          return order;
        });
    if (!submissionId) throw new Error('Missing submission reference.');
    if (submissions.has(submissionId)) return this.get(submissions.get(submissionId));
    if (Object.keys(checkoutErrors(data)).length)
      throw new Error('Please check the checkout fields.');
    const result = store.transact((s) => {
      const existing = s.orders.find((o) => o.submissionId === submissionId);
      if (existing) return structuredClone(existing);
      if (!s.cart.length) throw new Error('Your cart is empty. Add something delicious first.');
      // Staff branch selection does not change the customer's Downtown store.
      const branchId = CONFIG.branchId;
      const items = structuredClone(s.cart);
      const usage = ensureStock(s, items, branchId);
      const offer = promotionFor(s, totals(items).subtotal);
      const calculated = totals(items, { type: data.type, discountCents: offer.discountCents });
      const customer = s.customers.find((c) => c.id === s.currentCustomerId);
      const createdAt = new Date().toISOString();
      const queue = s.orders.filter(
        (o) => o.branchId === branchId && o.status !== 'Completed',
      ).length;
      const next = Math.max(1040, ...s.orders.map((o) => Number(o.id.split('-')[1]) || 1040)) + 1;
      const order = {
        id: 'LP-' + next,
        submissionId,
        branchId,
        customerId: customer.id,
        customer: {
          firstName: data.firstName.trim(),
          lastName: data.lastName.trim(),
          email: data.email.trim(),
          phone: data.phone.trim(),
        },
        address:
          data.type === 'delivery'
            ? { street: data.street, city: data.city, state: data.state, zip: data.zip }
            : null,
        items,
        type: data.type,
        payment: data.payment,
        ...calculated,
        createdAt,
        estimatedAt: new Date(
          Date.now() + estimateMinutes(items, data.type, queue) * 60000,
        ).toISOString(),
        updatedAt: createdAt,
        status: 'Order Received',
        inventoryDeducted: true,
        promotionId: s.selectedPromotion,
      };
      // Atomic local transaction: stock, reward redemption, order and cart commit together.
      for (const [id, amount] of Object.entries(usage))
        s.ingredients.find((i) => i.id === id && i.branchId === branchId).quantity -= amount;
      if (offer.points) {
        s.rewards[customer.id] -= offer.points;
        s.rewardTransactions.push({
          id: uid('rw'),
          customerId: customer.id,
          orderId: order.id,
          points: -offer.points,
          type: 'redeem',
          createdAt,
        });
      }
      order.pointsEarned = rewardsService.earn(s, order);
      s.orders.unshift(order);
      s.cart = [];
      s.selectedPromotion = null;
      s.lastOrderId = order.id;
      return structuredClone(order);
    });
    submissions.set(submissionId, result.id);
    return result;
  },
  get: (id) => store.read().orders.find((o) => o.id === String(id).trim().toUpperCase()),
  current: () => {
    const s = store.read();
    return s.orders.find((o) => o.id === s.lastOrderId && o.customerId === s.currentCustomerId);
  },
  list({ branchId, status = '', search = '', pageNumber = 1 } = {}) {
    return page(
      store
        .read()
        .orders.filter(
          (o) =>
            (!branchId || o.branchId === branchId) &&
            (!status || o.status === status) &&
            `${o.id} ${o.customer.firstName} ${o.customer.lastName}`
              .toLowerCase()
              .includes(search.toLowerCase()),
        ),
      pageNumber,
    );
  },
  advance(id) {
    if (apiClient.enabled()) return apiClient.command('advance', { id });
    store.transact((s) => {
      const o = s.orders.find((o) => o.id === id);
      if (!o) throw new Error('Order not found.');
      const steps = orderSteps(o.type);
      o.status = steps[Math.min(steps.indexOf(o.status) + 1, steps.length - 1)];
      o.updatedAt = new Date().toISOString();
    });
  },
};
