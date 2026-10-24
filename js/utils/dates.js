// Local calendar-day keys avoid UTC midnight offsets and locale string sorting.
export function dayKey(value) {
  const date = new Date(value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
export function dailyOrderTotals(orders, branchId, days = 14, now = Date.now()) {
  const rows = Array.from({ length: days }, (_, index) => {
    const date = new Date(now);
    date.setHours(12, 0, 0, 0);
    date.setDate(date.getDate() - (days - 1 - index));
    return { date: dayKey(date), orders: 0, revenueCents: 0 };
  });
  const byDay = new Map(rows.map((row) => [row.date, row]));
  for (const order of orders) {
    if (branchId && order.branchId !== branchId) continue;
    const row = byDay.get(dayKey(order.createdAt));
    if (!row) continue;
    row.orders++;
    row.revenueCents += order.subtotal - (order.discount || 0);
  }
  return rows;
}
