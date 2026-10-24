import { orderService } from '../services/orderService.js';
import { customerService } from '../services/customerService.js';
import { orderSteps } from '../config.js';
import { $, escapeHTML, dateTime, time, errorBox, notify, badge } from '../utils/dom.js';
import { money } from '../utils/currency.js';
import { itemName, itemDetails, totalsMarkup } from './cart.js';
import { apiClient } from '../services/apiClient.js';
export function orderDetail(order, confirmation = false) {
  const steps = orderSteps(order.type),
    index = steps.indexOf(order.status);
  const minutes = Math.max(0, Math.ceil((new Date(order.estimatedAt) - Date.now()) / 60000));
  return `<div class="tracking-card panel"><div class="section-heading"><div><p class="eyebrow">${escapeHTML(order.id)}</p><h2>${confirmation ? 'Thanks, ' + escapeHTML(order.customer.firstName) + '!' : escapeHTML(order.status)}</h2></div>${badge(order.status)}</div><p>${confirmation ? 'Your demo order is in. We’ll take it from here.' : 'We’re keeping an eye on your pizza.'}</p><div class="tracking-estimate"><div><span>Estimated ${order.type === 'delivery' ? 'arrival' : 'ready'} time</span><strong>${time(order.estimatedAt)}</strong></div><div><span>${order.status === 'Completed' ? 'All done' : minutes + ' estimated minutes remaining'}</span><small>Estimates may change with kitchen demand.</small></div></div><ol class="timeline">${steps.map((step, i) => `<li class="${i <= index ? 'done' : ''}" ${i === index ? 'aria-current="step"' : ''}><span class="timeline-dot" aria-hidden="true">${i < index ? '✓' : i + 1}</span><span>${step}${i === index ? '<small>Current step</small>' : ''}</span></li>`).join('')}</ol><div class="row tracking-meta"><span>Received ${dateTime(order.createdAt)}</span><span>Updated ${dateTime(order.updatedAt)}</span></div><div class="demo-controls"><span class="muted">Demo control · status updates are simulated</span><button class="button secondary" id="advance-tracking" ${order.status === 'Completed' ? 'disabled' : ''}>Simulate next step</button></div></div><section class="panel order-details"><h2>Order details</h2><div class="row"><p>${escapeHTML(order.customer.firstName + ' ' + order.customer.lastName)}<br>${order.type === 'delivery' ? 'Delivery' : 'Pickup · Downtown'}</p><p><strong>${money(order.total)}</strong><br>${order.pointsEarned} reward points earned</p></div>${order.address ? `<p>${escapeHTML(Object.values(order.address).join(', '))}</p>` : ''}<ul class="order-line-list">${order.items.map((i) => `<li><span><strong>${i.quantity} × ${escapeHTML(itemName(i))}</strong><small>${escapeHTML(itemDetails(i))}${i.instructions ? ' · ' + escapeHTML(i.instructions) : ''}</small></span></li>`).join('')}</ul>${totalsMarkup(order)}<a class="text-link" href="#support">Need help with your order? +</a></section>`;
}
export function tracker(params, refresh, confirmation = false) {
  const requested = params.get('id');
  const found = requested ? orderService.get(requested) : orderService.current();
  const order = found?.customerId === customerService.current().id ? found : null;
  return {
    html: `<section class="page-head"><p class="eyebrow">${confirmation ? 'FRESH THINGS ARE COMING' : 'FROM OUR OVEN TO YOU'}</p><h1>${confirmation ? 'Pizza night is on.' : 'Follow the good stuff.'}</h1><p>${confirmation ? 'Save your order number for tracking.' : 'Check your order’s progress and estimated ready time.'}</p></section><section class="section compact tracking-layout">${!confirmation ? `<form id="track-form" class="panel track-search"><label for="order-id">Order number</label><div class="inline-field"><input id="order-id" name="id" placeholder="LP-1057" value="${escapeHTML(requested || order?.id || '')}" required maxlength="30"><button class="button">Track order</button></div><p class="field-hint">Demo accounts can view their own orders. Try LP-1041 with Alex’s account.</p><div id="track-error">${requested && !order ? errorBox('No matching order for this demo account. Check the number or switch accounts.') : ''}</div></form>` : ''}${order ? orderDetail(order, confirmation) : '<div class="empty panel"><h2>Your pizza journey starts here.</h2><p>Enter an order number above, or build your next favorite.</p><a class="button secondary" href="#builder">Build a pizza</a></div>'}</section>`,
    mount() {
      if ($('#track-form'))
        $('#track-form').onsubmit = (e) => {
          e.preventDefault();
          location.hash =
            'track?id=' + encodeURIComponent(new FormData(e.target).get('id').trim().toUpperCase());
        };
      if ($('#advance-tracking'))
        if (apiClient.enabled()) $('#advance-tracking').closest('.demo-controls').remove();
      if ($('#advance-tracking'))
        $('#advance-tracking').onclick = async () => {
          try {
            await orderService.advance(order.id);
            refresh();
            notify('Demo order status updated.');
          } catch (err) {
            notify(err.message);
          }
        };
    },
  };
}
