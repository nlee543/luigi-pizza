import { store, uid } from './store.js';
import { CONFIG } from '../config.js';
export function promotionFor(state, subtotal) {
  const id = state.selectedPromotion;
  if (!id) return { discountCents: 0, points: 0 };
  const p = state.promotions.find((p) => p.id === id);
  const day = new Date().toISOString().slice(0, 10);
  if (!p || !p.active || p.start > day || p.end < day)
    throw new Error('This promotion is no longer active. Remove it from your cart.');
  if (subtotal < p.minSubtotal)
    throw new Error('This promotion’s minimum order amount has not been reached.');
  if ((state.rewards[state.currentCustomerId] || 0) < p.requiredPoints)
    throw new Error('You do not have enough points for this reward.');
  return {
    discountCents:
      p.discountType === 'percent'
        ? Math.round((subtotal * p.discountValue) / 100)
        : p.discountValue,
    points: p.requiredPoints,
  };
}
export const rewardsService = {
  balance: () => {
    const s = store.read();
    return s.rewards[s.currentCustomerId] || 0;
  },
  offers: () =>
    store
      .read()
      .promotions.filter(
        (p) =>
          p.active &&
          p.start <= new Date().toISOString().slice(0, 10) &&
          p.end >= new Date().toISOString().slice(0, 10),
      ),
  apply(code) {
    store.transact((s) => {
      const id = String(code).trim().toUpperCase();
      const p = s.promotions.find((p) => p.id === id);
      if (!p || !p.active) throw new Error('Promotion code not found.');
      if ((s.rewards[s.currentCustomerId] || 0) < p.requiredPoints)
        throw new Error('Not enough reward points.');
      s.selectedPromotion = id;
    });
  },
  remove() {
    store.transact((s) => {
      s.selectedPromotion = null;
    });
  },
  earn(state, order) {
    const points = Math.floor((order.total / 100) * CONFIG.pointsPerDollar);
    state.rewards[order.customerId] = (state.rewards[order.customerId] || 0) + points;
    state.rewardTransactions.push({
      id: uid('rw'),
      customerId: order.customerId,
      orderId: order.id,
      points,
      createdAt: new Date().toISOString(),
      type: 'earn',
    });
    return points;
  },
  transactions: () => {
    const s = store.read();
    return s.rewardTransactions.filter((t) => t.customerId === s.currentCustomerId);
  },
};
