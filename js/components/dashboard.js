import { analyticsService } from '../services/analyticsService.js';
import { employeeService } from '../services/employeeService.js';
import { store } from '../services/store.js';
import { money } from '../utils/currency.js';
import { escapeHTML } from '../utils/dom.js';
import { chart } from './charts.js';
export function dashboard() {
  if (!employeeService.isAdmin())
    return {
      html: '<section class="section empty"><h1>Administrator access required.</h1><p>Revenue and analytics are available only to administrators.</p><a class="button" href="#staff/orders">Open order queue</a></section>',
    };
  const branch = employeeService.branch();
  const isAdmin = employeeService.current().role === 'Administrator';
  const kpi = analyticsService.dashboard(branch),
    s = analyticsService.series(branch),
    f = analyticsService.forecast(branch);
  const all = isAdmin ? analyticsService.dashboard() : null;
  const kpis = [
    ['Revenue today', money(kpi.revenue), 'Before tax & delivery'],
    ['Orders today', kpi.orders, 'Placed today'],
    ['Average order value', money(kpi.average), 'Before tax & delivery'],
    ['Pizzas sold', kpi.pizzas, 'Today’s pizza quantities'],
    ['Pending orders', kpi.pending, 'In the kitchen queue'],
    ['Inventory alerts', kpi.alerts, 'Low or out of stock'],
    ['Customers', kpi.customers, 'Unique branch customers'],
    ['Reward members', kpi.members, 'Members ordering at this branch'],
  ];
  return {
    html: `<section class="section compact staff-content"><div class="section-heading"><div><p class="eyebrow">A FRESH LOOK AT YOUR BUSINESS</p><h1>${isAdmin ? 'The big picture.' : 'Your branch at a glance.'}</h1><p class="muted">${escapeHTML(store.read().branches.find((b) => b.id === branch).name)} · ${new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p></div><a class="button" href="#staff/orders">Open order queue</a></div><div class="kpi-grid">${kpis.map(([name, value, hint], i) => `<article class="kpi ${i === 0 ? 'featured' : ''}"><span>${name}</span><strong>${value}</strong><small>${hint}</small></article>`).join('')}</div>${isAdmin ? `<div class="organization-note panel"><strong>All branches today</strong><span>${money(all.revenue)} revenue · ${all.orders} orders · ${all.pending} pending</span></div>` : ''}<div class="charts-grid">${chart(
      'Revenue by day',
      isAdmin
        ? s.history.map((d) => [d.date.slice(5), d.revenueCents])
        : s.branchHistory.map((d) => [d.date, d.revenueCents]),
      {
        currency: true,
        line: true,
        summary: isAdmin
          ? 'Selected branch orders over the last 14 calendar days, including today. Revenue is after discounts, before tax and delivery. Days with no orders show zero.'
          : 'Selected branch demo orders, grouped by local date. Revenue is before tax and delivery.',
      },
    )}${chart(
      'Orders by day',
      isAdmin
        ? s.history.map((d) => [d.date.slice(5), d.orders])
        : s.branchHistory.map((d) => [d.date, d.orders]),
      {
        line: true,
        summary: isAdmin
          ? 'Actual demo orders for the selected branch, grouped by placement date. Includes active and completed orders; days with no orders show zero.'
          : 'Selected branch demo orders only.',
      },
    )}${chart('Sales by pizza size', s.sizes)}${chart('Popular toppings', s.toppings)}${chart('Sales by product category', s.category, { currency: true })}${chart('Pickup vs. delivery', s.fulfillment)}${chart(
      'Peak ordering times',
      Object.entries(s.hours).sort(([a], [b]) => parseInt(a) - parseInt(b)),
    )}</div>${isAdmin ? `<section class="forecast-panel"><div><p class="eyebrow">PLAN THE NEXT PIZZA NIGHT</p><h2>Tomorrow’s forecast.</h2><p>A simple seven-day average for this branch, including today and zero-order days. Planning estimates, not guaranteed sales.</p></div><div class="forecast-stats"><div><strong>${f.projectedOrders}</strong><span>Projected orders</span></div><div><strong>${money(f.projectedRevenue)}</strong><span>Projected revenue</span></div><div><strong>${f.sauceCups} cups</strong><span>Marinara & cheese, each</span></div></div><small>Ingredient estimate assumes 1.4 pizzas per order and 0.6 cup of each base ingredient per pizza. Forecast uses the same branch order records as the daily charts.</small></section>` : ''}</section>`,
  };
}
