import { store } from './store.js';
import { lineTotal } from '../utils/currency.js';
import { requireAdmin } from './staffAccess.js';
import { dailyOrderTotals, dayKey } from '../utils/dates.js';
export const analyticsService = {
  dashboard(branchId) {
    requireAdmin();
    const s = store.read();
    const day = dayKey(Date.now());
    const orders = s.orders.filter(
      (o) => (!branchId || o.branchId === branchId) && dayKey(o.createdAt) === day,
    );
    const revenue = orders.reduce((n, o) => n + o.subtotal - o.discount, 0);
    const pizzas = orders
      .flatMap((o) => o.items)
      .filter((i) => i.kind === 'pizza')
      .reduce((n, i) => n + i.quantity, 0);
    const ingredients = s.ingredients.filter((i) => !branchId || i.branchId === branchId);
    return {
      revenue,
      orders: orders.length,
      average: orders.length ? Math.round(revenue / orders.length) : 0,
      pizzas,
      pending: s.orders.filter(
        (o) => (!branchId || o.branchId === branchId) && o.status !== 'Completed',
      ).length,
      alerts: ingredients.filter((i) => i.quantity <= i.reorderLevel).length,
      customers: new Set(
        s.orders.filter((o) => !branchId || o.branchId === branchId).map((o) => o.customerId),
      ).size,
      members: new Set(
        s.orders
          .filter((o) => (!branchId || o.branchId === branchId) && s.rewards[o.customerId] > 0)
          .map((o) => o.customerId),
      ).size,
    };
  },
  series(branchId) {
    requireAdmin();
    const s = store.read();
    const orders = s.orders.filter((o) => !branchId || o.branchId === branchId);
    const sizes = { Small: 0, Medium: 0, Large: 0 },
      toppings = {},
      category = { Pizza: 0, Drinks: 0 },
      fulfillment = { Pickup: 0, Delivery: 0 },
      hours = {};
    for (const o of orders) {
      fulfillment[o.type === 'pickup' ? 'Pickup' : 'Delivery']++;
      const hour = new Date(o.createdAt).getHours() + ':00';
      hours[hour] = (hours[hour] || 0) + 1;
      const pizzaGross = o.items
        .filter((i) => i.kind === 'pizza')
        .reduce((sum, i) => sum + lineTotal(i), 0);
      const gross = o.items.reduce((sum, i) => sum + lineTotal(i), 0);
      const net = o.subtotal - (o.discount || 0);
      const pizzaNet = gross ? Math.round((net * pizzaGross) / gross) : 0;
      category.Pizza += pizzaNet;
      category.Drinks += net - pizzaNet;
      for (const i of o.items) {
        if (i.kind === 'pizza') {
          sizes[i.size[0].toUpperCase() + i.size.slice(1)] += i.quantity;
          for (const t of i.toppings) toppings[t] = (toppings[t] || 0) + i.quantity;
        }
      }
    }
    return {
      history: dailyOrderTotals(s.orders, branchId),
      branchHistory: dailyOrderTotals(s.orders, branchId),
      sizes,
      toppings,
      category,
      fulfillment,
      hours,
    };
  },
  forecast(branchId) {
    requireAdmin();
    const h = dailyOrderTotals(store.read().orders, branchId, 7);
    const projectedOrders = Math.round(h.reduce((n, d) => n + d.orders, 0) / h.length);
    const projectedRevenue = Math.round(h.reduce((n, d) => n + d.revenueCents, 0) / h.length);
    return {
      projectedOrders,
      projectedRevenue,
      sauceCups: Math.ceil(projectedOrders * 1.4 * 0.6),
      cheeseCups: Math.ceil(projectedOrders * 1.4 * 0.6),
    };
  },
};
