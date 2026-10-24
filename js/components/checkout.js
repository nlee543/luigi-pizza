import { cartService } from '../services/cartService.js';
import { customerService } from '../services/customerService.js';
import { orderService } from '../services/orderService.js';
import { store, uid } from '../services/store.js';
import { promotionFor } from '../services/rewardsService.js';
import { totals } from '../utils/currency.js';
import { checkoutErrors } from '../utils/validation.js';
import { $, $$, escapeHTML, errorBox, notify } from '../utils/dom.js';
import { totalsMarkup } from './cart.js';
const field = (name, label, value = '', type = 'text', autocomplete = '', required = true) =>
  `<div class="form-field"><label for="${name}">${label}${required ? '' : ' (optional)'}</label><input id="${name}" name="${name}" type="${type}" value="${escapeHTML(value)}" autocomplete="${autocomplete}" ${required ? 'required' : ''} maxlength="150" aria-describedby="error-${name}"><small class="field-error" id="error-${name}"></small></div>`;
export function checkout() {
  const items = cartService.list();
  if (!items.length)
    return {
      html: '<section class="section empty"><h1>Your bag is empty.</h1><a class="button" href="#builder">Build a pizza</a></section>',
    };
  const c = customerService.current();
  const address = c.address || {};
  const submissionId = uid('submission');
  let submitting = false;
  return {
    html: `<section class="page-head"><p class="eyebrow">THE LAST STEP BEFORE THE FIRST BITE</p><h1>Let’s make it official.</h1><p>Demo checkout. No real payment or restaurant order is created.</p></section><section class="section compact cart-layout"><form id="checkout-form" novalidate><div id="checkout-errors" tabindex="-1"></div><fieldset><legend>How would you like your order?</legend><div class="builder-sizes two"><label class="choice-card"><input type="radio" name="type" value="pickup" checked><strong>Pickup</strong><small>Downtown · no delivery fee</small></label><label class="choice-card"><input type="radio" name="type" value="delivery"><strong>Delivery</strong><small>Demo delivery · $3.00 fee</small></label></div></fieldset><fieldset><legend>Your details</legend><div class="form-grid">${field('firstName', 'First name', c.firstName, 'text', 'given-name')}${field('lastName', 'Last name', c.lastName, 'text', 'family-name')}${field('phone', 'Phone number', c.phone, 'tel', 'tel')}${field('email', 'Email address', c.email, 'email', 'email')}</div></fieldset><fieldset id="address-fields" hidden disabled><legend>Delivery address</legend><div class="form-grid">${field('street', 'Street address', address.street, 'text', 'street-address')}${field('city', 'City', address.city, 'text', 'address-level2')}${field('state', 'State', address.state, 'text', 'address-level1')}${field('zip', 'ZIP code', address.zip, 'text', 'postal-code')}</div><p class="field-hint">Delivery is simulated. Service-area verification would be handled by a backend.</p></fieldset><fieldset><legend>Payment</legend><label class="radio-line"><input type="radio" name="payment" value="demo" checked> Pay Online — Demo (simulated approval)</label><label class="radio-line"><input type="radio" name="payment" value="store"> Pay at Store / on delivery</label><p class="field-hint">Do not enter card details. No money is charged.</p></fieldset></form><aside class="panel order-summary"><h2>Your order</h2><div id="checkout-totals" aria-live="polite"></div><button class="button full" type="submit" form="checkout-form" id="place-order">Place demo order</button><p class="field-hint">Estimated timing is shown after confirmation. Preparation depends on order size and the current queue.</p></aside></section>`,
    mount() {
      const form = $('#checkout-form');
      function update() {
        const type = new FormData(form).get('type');
        $('#address-fields').hidden = type !== 'delivery';
        $('#address-fields').disabled = type !== 'delivery';
        try {
          $('#checkout-totals').innerHTML = totalsMarkup(
            totals(items, {
              type,
              discountCents: promotionFor(store.read(), totals(items).subtotal).discountCents,
            }),
          );
          $('#place-order').disabled = false;
        } catch (err) {
          $('#checkout-totals').innerHTML = errorBox(err.message);
          $('#place-order').disabled = true;
        }
      }
      form.onchange = update;
      update();
      form.onsubmit = async (e) => {
        e.preventDefault();
        if (submitting) return;
        const data = Object.fromEntries(new FormData(form));
        const errors = checkoutErrors(data);
        $$('.field-error').forEach((el) => (el.textContent = ''));
        $$('input[aria-invalid]').forEach((el) => el.removeAttribute('aria-invalid'));
        if (Object.keys(errors).length) {
          for (const [key, message] of Object.entries(errors)) {
            if ($('#error-' + key)) $('#error-' + key).textContent = message;
            $('#' + key)?.setAttribute('aria-invalid', 'true');
          }
          $('#checkout-errors').innerHTML =
            `<div class="error" role="alert"><strong>Please check ${Object.keys(errors).length} field(s).</strong><ul>${Object.entries(
              errors,
            )
              .map(
                ([key, m]) =>
                  `<li><a href="#${key}" data-field="${key}">${escapeHTML(key)}: ${escapeHTML(m)}</a></li>`,
              )
              .join('')}</ul></div>`;
          $('#checkout-errors').focus();
          return;
        }
        submitting = true;
        $('#place-order').disabled = true;
        $('#place-order').textContent = 'Placing your order…';
        try {
          await new Promise((r) => setTimeout(r, 400));
          const order = await orderService.place(data, submissionId);
          notify(`Order ${order.id} received. Thanks!`);
          location.hash = 'confirmation?id=' + order.id;
        } catch (err) {
          $('#checkout-errors').innerHTML = errorBox(err.message);
          $('#checkout-errors').focus();
          submitting = false;
          $('#place-order').disabled = false;
          $('#place-order').textContent = 'Try again';
        }
      };
      $('#checkout-errors').onclick = (e) => {
        const a = e.target.closest('[data-field]');
        if (a) {
          e.preventDefault();
          $('#' + a.dataset.field)?.focus();
        }
      };
    },
  };
}
