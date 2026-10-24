import { SIZES, TOPPINGS, DRINKS } from '../config.js';
import { store } from '../services/store.js';
import { cartService } from '../services/cartService.js';
import { rewardsService, promotionFor } from '../services/rewardsService.js';
import { money, lineTotal, totals } from '../utils/currency.js';
import { $, escapeHTML, notify, errorBox } from '../utils/dom.js';
export const itemName = (i) =>
  i.kind === 'pizza'
    ? `${SIZES[i.size].name} pizza · ${SIZES[i.size].diameter}″`
    : `${SIZES[i.size].name} ${DRINKS.find((d) => d.id === i.drinkId)?.name || 'drink'}`;
export const itemDetails = (i) =>
  i.kind === 'pizza'
    ? i.toppings.length
      ? i.toppings.map((id) => TOPPINGS.find((t) => t.id === id)?.name || id).join(', ')
      : 'Marinara + cheese included'
    : '';
export function totalsMarkup(t) {
  return `<dl class="totals"><div><dt>Subtotal</dt><dd>${money(t.subtotal)}</dd></div>${t.discount ? `<div><dt>Discount</dt><dd>−${money(t.discount)}</dd></div>` : ''}<div><dt>Estimated tax (8.25%)</dt><dd>${money(t.tax)}</dd></div>${t.delivery ? `<div><dt>Delivery</dt><dd>${money(t.delivery)}</dd></div>` : ''}<div class="total"><dt>Total</dt><dd>${money(t.total)}</dd></div></dl>`;
}
export function cart(refresh) {
  const items = cartService.list();
  const state = store.read();
  let t,
    error = '';
  try {
    t = totals(items, { discountCents: promotionFor(state, totals(items).subtotal).discountCents });
  } catch (e) {
    t = totals(items);
    error = e.message;
  }
  return {
    html: `<section class="page-head"><p class="eyebrow">GOOD CHOICES, ALL AROUND</p><h1>Your bag.</h1><p>${items.length ? 'One step closer to pizza night.' : 'Let’s get something delicious in here.'}</p></section><section class="section compact cart-layout"><div>${items.length ? `<div class="cart-items">${items.map((i) => `<article class="cart-item"><div class="item-monogram" aria-hidden="true">${i.kind === 'pizza' ? 'P' : 'D'}</div><div class="cart-item-info"><h2>${escapeHTML(itemName(i))}</h2><p>${escapeHTML(itemDetails(i))}</p>${i.instructions ? `<small>Note: ${escapeHTML(i.instructions)}</small>` : ''}<div class="item-actions">${i.kind === 'pizza' ? `<a href="#builder?edit=${i.id}" class="text-link">Edit pizza</a>` : ''}<button type="button" class="text-button" data-remove="${i.id}">Remove<span class="sr-only"> ${escapeHTML(itemName(i))}</span></button></div></div><div class="cart-item-price"><strong>${money(lineTotal(i))}</strong><label class="sr-only" for="qty-${i.id}">${escapeHTML(itemName(i))} quantity</label><input id="qty-${i.id}" type="number" min="1" max="20" value="${i.quantity}" data-qty="${i.id}"></div></article>`).join('')}</div><a class="text-link add-pizza" href="#builder">+ Add another pizza</a>` : '<div class="empty panel"><h2>Your next favorite is waiting.</h2><p>Pick a size, add your favorite toppings, and make it yours.</p><a class="button" href="#builder">Build a pizza</a></div>'}<section class="panel drinks-panel"><h2>Don’t forget the drinks.</h2><p>Small $1.00 · Medium $2.00 · Large $3.00</p><form id="drink-form" class="drink-form"><div><label for="beverage">Beverage</label><select id="beverage" name="drinkId">${DRINKS.map((d) => `<option value="${d.id}">${d.name}</option>`).join('')}</select></div><div><label for="drink-size">Size</label><select id="drink-size" name="size">${Object.entries(
      SIZES,
    )
      .map(([id, s]) => `<option value="${id}">${s.name} · ${money(s.drinkCents)}</option>`)
      .join(
        '',
      )}</select></div><button class="button secondary">Add drink</button></form></section></div><aside class="panel order-summary"><p class="eyebrow">THE GOOD STUFF ADDS UP</p><h2>Order summary</h2><div id="cart-error">${error ? errorBox(error) : ''}</div>${totalsMarkup(t)}<form id="promo-form"><label for="promo">Have a promo code?</label><div class="inline-field"><input id="promo" name="promo" placeholder="WELCOME5" maxlength="40"><button class="button secondary">Apply</button></div></form>${state.selectedPromotion ? `<p class="promotion-applied">${escapeHTML(state.selectedPromotion)} selected <button class="text-button" id="remove-promo">Remove</button></p>` : ''}<a class="button full ${!items.length || error ? 'disabled' : ''}" href="${items.length && !error ? '#checkout' : '#cart'}" ${!items.length || error ? 'aria-disabled="true"' : ''}>Checkout</a><small>Pickup total shown. Delivery adds $3.00 at checkout. Tax is a demo estimate.</small></aside></section>`,
    mount() {
      $('#main').onclick = (e) => {
        const button = e.target.closest('[data-remove]');
        if (button) {
          cartService.remove(button.dataset.remove);
          notify('Item removed.');
          refresh();
        }
      };
      $('#main').onchange = (e) => {
        if (e.target.matches('[data-qty]')) {
          try {
            cartService.quantity(e.target.dataset.qty, e.target.value);
            refresh();
            notify('Quantity updated.');
          } catch (err) {
            $('#cart-error').innerHTML = errorBox(err.message);
            e.target.value = cartService.list().find((i) => i.id === e.target.dataset.qty).quantity;
          }
        }
      };
      $('#drink-form').onsubmit = (e) => {
        e.preventDefault();
        const data = new FormData(e.target);
        try {
          cartService.add({
            kind: 'drink',
            size: data.get('size'),
            drinkId: data.get('drinkId'),
            quantity: 1,
          });
          refresh();
          notify('Drink added to your bag.');
        } catch (err) {
          $('#cart-error').innerHTML = errorBox(err.message);
        }
      };
      $('#promo-form').onsubmit = (e) => {
        e.preventDefault();
        try {
          rewardsService.apply(new FormData(e.target).get('promo'));
          refresh();
          notify('Promotion selected. Eligibility checked against your total.');
        } catch (err) {
          $('#cart-error').innerHTML = errorBox(err.message);
        }
      };
      if ($('#remove-promo'))
        $('#remove-promo').onclick = () => {
          rewardsService.remove();
          refresh();
        };
    },
  };
}
