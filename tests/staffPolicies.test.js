import test from 'node:test';
import assert from 'node:assert/strict';
import { store } from '../js/services/store.js';
import { employeeService } from '../js/services/employeeService.js';
import { analyticsService } from '../js/services/analyticsService.js';
import { staffLinks, allowedStaffRoute } from '../js/services/staffAccess.js';
import { staffTeam } from '../js/components/teamTime.js';
import { dailyOrderTotals } from '../js/utils/dates.js';

test('employees see solely their own shifts, even when asking for another branch', () => {
  store.reset();
  employeeService.select('e2');
  assert.deepEqual(
    employeeService.shifts('downtown').map((s) => s.employeeId),
    ['e2'],
  );
  assert.deepEqual(
    employeeService.shifts('riverside').map((s) => s.employeeId),
    ['e2'],
  );
  assert.match(staffTeam(() => {}).html, /My shifts/);
  assert.doesNotMatch(staffTeam(() => {}).html, /team-review-branch|Employee directory/);
  employeeService.select('e3');
  assert.deepEqual(
    employeeService.shifts('downtown').map((s) => s.employeeId),
    ['e3'],
  );
});

test('administrators review branches and verify only completed shifts', () => {
  store.reset();
  assert.equal(employeeService.shifts('downtown').length, 2);
  assert.equal(employeeService.shifts('riverside').length, 1);
  assert.match(staffTeam(() => {}).html, /Branch to review/);
  employeeService.verifyShift('sh2');
  const shift = employeeService.shifts('downtown').find((s) => s.id === 'sh2');
  assert.equal(shift.verifiedBy, 'e1');
  assert.ok(shift.verifiedAt);
  assert.throws(() => employeeService.verifyShift('sh1'), /Clock out/);
  employeeService.select('e2');
  assert.throws(() => employeeService.verifyShift('sh2'), /administrator/);
});

test('employee routes keep the order queue and restrict overview and analytics services', () => {
  store.reset();
  employeeService.select('e2');
  assert.equal(allowedStaffRoute('staff'), 'staff/orders');
  assert.equal(allowedStaffRoute('staff/promotions'), 'staff/orders');
  assert.equal(allowedStaffRoute('staff/orders'), 'staff/orders');
  assert.ok(staffLinks().some(([route]) => route === 'staff/orders'));
  assert.ok(!staffLinks().some(([route]) => route === 'staff'));
  assert.throws(() => analyticsService.dashboard('downtown'), /Administrator/);
  assert.throws(() => analyticsService.series('downtown'), /Administrator/);
  assert.throws(() => analyticsService.forecast('downtown'), /Administrator/);
});

test('daily graphs aggregate real orders by branch and date, filling gaps in order', () => {
  const now = new Date(2026, 9, 3, 15).getTime();
  const date = (day) => new Date(2026, 9, day, 14).toISOString();
  const orders = [
    { branchId: 'downtown', createdAt: date(3), subtotal: 1500, discount: 500 },
    { branchId: 'downtown', createdAt: date(1), subtotal: 900, discount: 0 },
    { branchId: 'downtown', createdAt: date(3), subtotal: 700, discount: 0 },
    { branchId: 'riverside', createdAt: date(3), subtotal: 5000, discount: 0 },
  ];
  assert.deepEqual(dailyOrderTotals(orders, 'downtown', 3, now), [
    { date: '2026-10-01', orders: 1, revenueCents: 900 },
    { date: '2026-10-02', orders: 0, revenueCents: 0 },
    { date: '2026-10-03', orders: 2, revenueCents: 1700 },
  ]);
  assert.equal(dailyOrderTotals(orders, undefined, 3, now)[2].revenueCents, 6700);
});

test('today chart values reconcile with KPIs and legacy synthetic history is ignored', () => {
  store.reset();
  store.transact((state) => {
    state.salesHistory = [{ date: '2026-10-01', orders: 999, revenueCents: 999999 }];
  });
  const kpi = analyticsService.dashboard('downtown');
  const series = analyticsService.series('downtown');
  assert.equal(series.history.length, 14);
  assert.equal(series.history.at(-1).orders, kpi.orders);
  assert.equal(series.history.at(-1).revenueCents, kpi.revenue);
  const allRevenue = store
    .read()
    .orders.filter((o) => o.branchId === 'downtown')
    .reduce((sum, o) => sum + o.subtotal - o.discount, 0);
  assert.equal(series.category.Pizza + series.category.Drinks, allRevenue);
  assert.ok(!series.history.some((row) => row.orders === 999));
});
