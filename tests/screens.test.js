// Screen render checks complement service tests. They do not replace a real
// browser, screen-reader audit, or responsive visual inspection.
import test from 'node:test';
import assert from 'node:assert/strict';
import { home, menu } from '../js/components/home.js';
import { pizzaBuilder } from '../js/components/pizzaBuilder.js';
import { cart } from '../js/components/cart.js';
import { checkout } from '../js/components/checkout.js';
import { tracker } from '../js/components/orderTracker.js';
import { rewards, account } from '../js/components/account.js';
import { supportChat } from '../js/components/supportChat.js';
import { dashboard } from '../js/components/dashboard.js';
import {
  staffOrders,
  staffInventory,
  staffTeam,
  staffSupport,
  staffPromotions,
  staffShell,
} from '../js/components/staff.js';
import { store } from '../js/services/store.js';
import { cartService } from '../js/services/cartService.js';
import { employeeService } from '../js/services/employeeService.js';
import { customerService } from '../js/services/customerService.js';
import { supportService } from '../js/services/supportService.js';
import { orderService } from '../js/services/orderService.js';
import { escapeHTML } from '../js/utils/dom.js';
const refresh = () => {};
test('every customer and staff route produces its primary screen without rendering errors', () => {
  store.reset();
  cartService.add({
    kind: 'pizza',
    size: 'large',
    quantity: 1,
    toppings: ['pepperoni'],
    instructions: '',
  });
  const screens = [
    home(),
    menu(),
    pizzaBuilder(new URLSearchParams()).html,
    cart(refresh).html,
    checkout().html,
    tracker(new URLSearchParams('id=LP-1041'), refresh).html,
    rewards().html,
    account(refresh).html,
    supportChat().html,
    dashboard().html,
    staffOrders().html,
    staffInventory().html,
    staffTeam(refresh).html,
    staffSupport().html,
    staffPromotions(refresh).html,
  ];
  for (const html of screens) {
    assert.match(html, /<h1>/);
    assert.doesNotMatch(html, /\bundefined\b|\bNaN\b/);
    const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
    assert.equal(new Set(ids).size, ids.length, 'IDs must be unique within each screen');
  }
  assert.match(checkout().html, /hidden disabled/);
  assert.match(pizzaBuilder(new URLSearchParams()).html, /aria-live="polite"/);
  assert.match(supportChat().html, /Talk to a Representative/);
  assert.equal((dashboard().html.match(/<summary>View chart data<\/summary>/g) || []).length, 7);
});
test('customer text is escaped in profile, notes and tracking screens', () => {
  store.reset();
  const malicious = '<img src=x onerror="alert(1)">';
  customerService.update({ firstName: malicious });
  cartService.add({
    kind: 'pizza',
    size: 'small',
    quantity: 1,
    toppings: [],
    instructions: malicious,
  });
  assert.ok(account(refresh).html.includes(escapeHTML(malicious)));
  assert.ok(cart(refresh).html.includes(escapeHTML(malicious)));
  assert.ok(!cart(refresh).html.includes(malicious));
});
test('branch staff cannot render revenue or promotion management', () => {
  store.reset();
  employeeService.select('e3');
  const html = dashboard().html;
  assert.match(html, /Administrator access required/);
  assert.doesNotMatch(html, /14 days of fictional organization sales history/);
  assert.match(staffPromotions(refresh).html, /Administrator demo required/);
  assert.doesNotMatch(staffShell('staff', html), /href="#staff\/promotions"/);
  assert.doesNotMatch(staffShell('staff', html), /href="#staff"/);
  assert.match(staffShell('staff/orders', staffOrders().html), /href="#staff\/orders"/);
});
test('changing staff branch does not change customer checkout fulfillment', () => {
  store.reset();
  employeeService.setBranch('riverside');
  cartService.add({ kind: 'pizza', size: 'large', quantity: 1, toppings: [], instructions: '' });
  const order = orderService.place(
    {
      firstName: 'Test',
      lastName: 'Demo',
      phone: '202-555-0105',
      email: 'test@example.test',
      type: 'pickup',
      payment: 'store',
    },
    'branch-separation',
  );
  assert.equal(order.branchId, 'downtown');
});
test('support tickets validate customer order references and preserve escalation context', () => {
  store.reset();
  supportService.addMessage('customer', 'A topping was missing.');
  assert.throws(
    () =>
      supportService.createTicket({
        category: 'Order issue',
        description: 'Missing topping',
        orderId: 'LP-1042',
      }),
    /not found/,
  );
  const ticket = supportService.createTicket({
    category: 'Order issue',
    description: 'Missing topping',
    orderId: 'lp-1041',
  });
  assert.equal(ticket.orderId, 'LP-1041');
  assert.equal(ticket.status, 'Escalated');
  assert.ok(ticket.summary.includes('A topping was missing.'));
  assert.ok(ticket.messages.length > 0);
  customerService.select('c2');
  assert.equal(
    supportService.messages().length,
    1,
    'Switching customer clears the previous demo conversation',
  );
});
