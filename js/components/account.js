import { customerService } from '../services/customerService.js';
import { rewardsService } from '../services/rewardsService.js';
import { cartService } from '../services/cartService.js';
import { checkoutErrors } from '../utils/validation.js';
import { $, escapeHTML, notify, openDialog, errorBox, dateTime, badge } from '../utils/dom.js';
import { money } from '../utils/currency.js';
import { itemName } from './cart.js';
import { apiClient } from '../services/apiClient.js';
import { store } from '../services/store.js';
export function rewards() {
  const balance = rewardsService.balance();
  return {
    html: `<section class="page-head"><p class="eyebrow">MORE PIZZA. MORE PERKS.</p><h1>Good taste gets rewarded.</h1><p>Earn 1 point for every $1 spent. Use your points for a little extra joy.</p></section><section class="section compact"><div class="rewards-banner"><div><p class="eyebrow">YOUR LUIGI’S BALANCE</p><h2>${balance}<span>points</span></h2><p>${balance >= 100 ? 'You’ve earned a treat.' : 'Only ' + (100 - balance) + ' points to your next $5 reward.'}</p></div><div><label for="reward-progress">Progress to your next 100-point reward</label><progress id="reward-progress" max="100" value="${Math.min(balance, 100)}">${Math.min(balance, 100)}%</progress><small>Points earned on the final demo total, rounded down.<br>Rewards are applied at checkout.</small></div></div><div class="section-heading"><h2>A little something for you.</h2><a class="text-link" href="#account">View your account +</a></div><div class="offers-grid">${rewardsService
      .offers()
      .map(
        (p) =>
          `<article class="panel offer"><p class="eyebrow">${p.requiredPoints ? p.requiredPoints + ' POINTS' : 'ON THE HOUSE'}</p><h3>${escapeHTML(p.name)}</h3><p>${escapeHTML(p.description)}</p><button class="button secondary" data-offer="${p.id}" ${balance < p.requiredPoints ? 'disabled' : ''}>${balance < p.requiredPoints ? 'Need ' + (p.requiredPoints - balance) + ' more points' : p.requiredPoints ? 'Use reward' : 'Apply offer'}</button><small>Ends ${escapeHTML(p.end)} · minimum ${money(p.minSubtotal)}</small></article>`,
      )
      .join('')}</div><section class="panel"><h2>Your points activity</h2>${
      rewardsService.transactions().length
        ? `<ul class="order-line-list">${rewardsService
            .transactions()
            .slice(-10)
            .reverse()
            .map(
              (t) =>
                `<li><span>${escapeHTML(t.orderId)} · ${t.type === 'earn' ? 'Earned' : 'Redeemed'}</span><strong>${t.points > 0 ? '+' : ''}${t.points} points</strong></li>`,
            )
            .join('')}</ul>`
        : '<p class="muted">Your starting balance is fictional demo data. New orders and redemptions appear here.</p>'
    }</section></section>`,
    mount() {
      $('#main').onclick = (e) => {
        const b = e.target.closest('[data-offer]');
        if (b)
          try {
            rewardsService.apply(b.dataset.offer);
            notify('Offer selected. Add your favorites to use it at checkout.');
            location.hash = 'cart';
          } catch (err) {
            notify(err.message);
          }
      };
    },
  };
}
export function account(refresh) {
  const c = customerService.current();
  const orders = customerService.history();
  return {
    html: `<section class="page-head"><p class="eyebrow">YOUR CORNER OF LUIGI’S</p><h1>Hey, ${escapeHTML(c.firstName)}.</h1><p>Your details, your usuals, and all your pizza nights.</p></section><section class="section compact account-grid"><aside class="panel"><div class="avatar" aria-hidden="true">${escapeHTML(c.firstName[0])}</div><h2>${escapeHTML(c.firstName + ' ' + c.lastName)}</h2><p>${escapeHTML(c.email)}<br>${escapeHTML(c.phone)}</p><h3>Saved address</h3><p>${c.address ? escapeHTML(Object.values(c.address).join(', ')) : 'No saved address'}</p><button class="button secondary" id="edit-profile">Edit details</button><hr><label for="demo-customer">Switch fictional demo account</label><select id="demo-customer">${customerService
      .list()
      .map(
        (x) =>
          `<option value="${x.id}" ${x.id === c.id ? 'selected' : ''}>${escapeHTML(x.firstName + ' ' + x.lastName)}</option>`,
      )
      .join(
        '',
      )}</select><small>Mock sign-in. This does not provide secure authentication.</small><a class="text-link" href="#rewards">${rewardsService.balance()} points · View rewards +</a></aside><div><section class="panel"><h2>Recent orders</h2>${
      orders.length
        ? `<ul class="order-line-list">${orders
            .slice(0, 8)
            .map(
              (o) =>
                `<li><div><a href="#track?id=${o.id}"><strong>${o.id}</strong></a><small>${dateTime(o.createdAt)} · ${money(o.total)}</small></div>${badge(o.status)}<button class="button small secondary" data-reorder="${o.id}">Order again</button></li>`,
            )
            .join('')}</ul>`
        : '<p>No orders yet.</p>'
    }</section><section class="panel"><h2>Your recent pizzas</h2>${
      orders
        .flatMap((o) => o.items)
        .filter((i) => i.kind === 'pizza')
        .slice(0, 3)
        .map((i) => `<p>${escapeHTML(itemName(i))} · ${i.toppings.length} toppings</p>`)
        .join('') || '<p>Your favorites will appear after you order.</p>'
    }</section></div></section>`,
    mount() {
      if (apiClient.enabled()) {
        const selector = $('#demo-customer');
        const label = document.querySelector('label[for="demo-customer"]');
        if (label) label.textContent = 'Signed-in customer account';
        selector.disabled = true;
        selector.nextElementSibling.textContent = 'Your account is verified by the server.';
        const logout = document.createElement('button');
        logout.className = 'button secondary full';
        logout.textContent = 'Sign out';
        selector.parentNode.append(logout);
        logout.onclick = async () => {
          try {
            await apiClient.logout();
            store.clearSession();
            location.hash = 'customer-login';
          } catch (error) {
            notify(error.message);
          }
        };
      }
      $('#demo-customer').onchange = (e) => {
        customerService.select(e.target.value);
        refresh();
        notify('Demo account switched.');
      };
      $('#main').onclick = (e) => {
        const b = e.target.closest('[data-reorder]');
        if (b) {
          try {
            const o = orders.find((o) => o.id === b.dataset.reorder);
            for (const item of o.items) cartService.add({ ...item });
            notify('Previous items added at current menu prices.');
            location.hash = 'cart';
          } catch (err) {
            notify(err.message);
          }
        }
      };
      $('#edit-profile').onclick = () =>
        openDialog(
          'Edit your details',
          `<form id="profile-form"><div id="profile-error"></div>${['firstName', 'lastName', 'email', 'phone'].map((key) => `<label for="profile-${key}">${{ firstName: 'First name', lastName: 'Last name', email: 'Email', phone: 'Phone' }[key]}</label><input id="profile-${key}" name="${key}" value="${escapeHTML(c[key])}" type="${key === 'email' ? 'email' : key === 'phone' ? 'tel' : 'text'}" required maxlength="150">`).join('')}<fieldset><legend>Saved address (optional)</legend>${['street', 'city', 'state', 'zip'].map((key) => `<label for="profile-${key}">${{ street: 'Street address', city: 'City', state: 'State', zip: 'ZIP code' }[key]}</label><input id="profile-${key}" name="${key}" value="${escapeHTML(c.address?.[key] || '')}" maxlength="150">`).join('')}</fieldset><button class="button full">Save details</button></form>`,
          (dialog) => {
            $('#profile-form', dialog).onsubmit = async (e) => {
              e.preventDefault();
              const data = Object.fromEntries(new FormData(e.target));
              const hasAddress = ['street', 'city', 'state', 'zip'].some((k) => data[k].trim());
              const errors = checkoutErrors({
                ...data,
                type: hasAddress ? 'delivery' : 'pickup',
                payment: 'store',
              });
              if (Object.keys(errors).length) {
                $('#profile-error', dialog).innerHTML = errorBox(Object.values(errors).join(' '));
                return;
              }
              try {
                await customerService.update({
                  firstName: data.firstName,
                  lastName: data.lastName,
                  email: data.email,
                  phone: data.phone,
                  address: hasAddress
                    ? { street: data.street, city: data.city, state: data.state, zip: data.zip }
                    : null,
                });
              } catch (error) {
                $('#profile-error', dialog).innerHTML = errorBox(error.message);
                return;
              }
              dialog.close();
              refresh();
              notify('Demo profile saved.');
            };
          },
        );
    },
  };
}
