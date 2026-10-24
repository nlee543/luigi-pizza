export { staffTeam } from './teamTime.js';
import { store, page } from '../services/store.js';
import { employeeService } from '../services/employeeService.js';
import { orderService } from '../services/orderService.js';
import { inventoryService, stockStatus } from '../services/inventoryService.js';
import { supportService } from '../services/supportService.js';
import { orderSteps, CONFIG } from '../config.js';
import {
  $,
  escapeHTML,
  dateTime,
  badge,
  notify,
  openDialog,
  errorBox,
  debounce,
} from '../utils/dom.js';
import { money } from '../utils/currency.js';
import { itemName, itemDetails } from './cart.js';
import { staffLinks } from '../services/staffAccess.js';
import { promotionService } from '../services/promotionService.js';
import { apiClient } from '../services/apiClient.js';
export function staffShell(route, content) {
  const state = store.read(),
    employee = employeeService.current(),
    admin = employee.role === 'Administrator';
  const visibleEmployees = apiClient.enabled()
    ? state.employees.filter((e) => e.apiUserId === apiClient.user()?.id)
    : state.employees;
  return `<div class="staff-shell"><section class="staff-toolbar"><div><span class="badge">STAFF DEMO</span><span>${apiClient.enabled() ? 'Connected · database-backed access' : 'Mock access · backend authorization required'}</span><button class="button small secondary" id="refresh-staff">Refresh records</button></div><div class="staff-selectors"><div><label for="staff-person">${apiClient.enabled() ? 'Signed-in employee' : 'Demo employee'}</label><select id="staff-person" ${apiClient.enabled() ? 'disabled' : ''}>${visibleEmployees.map((e) => `<option value="${e.id}" ${e.id === employee.id ? 'selected' : ''}>${escapeHTML(e.firstName + ' ' + e.lastName)} · ${e.role}</option>`).join('')}</select></div><div><label for="staff-branch">Branch</label><select id="staff-branch" ${admin ? '' : 'disabled'}>${state.branches.map((b) => `<option value="${b.id}" ${b.id === state.branchId ? 'selected' : ''}>${b.name}</option>`).join('')}</select></div></div></section><nav class="staff-subnav" aria-label="Management navigation">${staffLinks()
    .map(
      ([id, name]) => `<a href="#${id}" ${route === id ? 'aria-current="page"' : ''}>${name}</a>`,
    )
    .join('')}</nav>${content}</div>`;
}
export function mountStaffShell(refresh) {
  $('#refresh-staff').onclick = async () => {
    try {
      if (apiClient.enabled()) await apiClient.refresh();
      refresh();
      notify('Records refreshed.');
    } catch (error) {
      notify(error.message);
    }
  };
  $('#staff-person').onchange = (e) => {
    employeeService.select(e.target.value);
    refresh();
    notify('Demo employee switched.');
  };
  $('#staff-branch').onchange = (e) => {
    try {
      employeeService.setBranch(e.target.value);
      refresh();
    } catch (err) {
      notify(err.message);
    }
  };
}
function pagination(result) {
  return `<div class="pagination"><span>${result.total} result${result.total === 1 ? '' : 's'} · page ${result.page} of ${result.pages}</span><div><button class="button secondary small" data-page="${result.page - 1}" ${result.page <= 1 ? 'disabled' : ''}>Previous</button><button class="button secondary small" data-page="${result.page + 1}" ${result.page >= result.pages ? 'disabled' : ''}>Next</button></div></div>`;
}
export function staffOrders() {
  let pageNumber = 1;
  return {
    html: `<section class="section compact staff-content"><div class="section-heading"><div><p class="eyebrow">KEEP THE GOOD STUFF MOVING</p><h1>Order queue.</h1></div><span class="badge">${escapeHTML(employeeService.branch())}</span></div><div class="filters"><div><label for="order-search">Search orders or customers</label><input id="order-search" type="search" placeholder="Order number or name"></div><div><label for="order-status">Status</label><select id="order-status"><option value="">All statuses</option>${[...new Set([...orderSteps('pickup'), ...orderSteps('delivery')])].map((s) => `<option>${s}</option>`).join('')}</select></div></div><div id="staff-orders-table"></div></section>`,
    mount() {
      function render() {
        const result = orderService.list({
          branchId: employeeService.branch(),
          search: $('#order-search').value,
          status: $('#order-status').value,
          pageNumber,
        });
        $('#staff-orders-table').innerHTML =
          `<div class="table-wrap panel"><table><caption class="sr-only">Branch order queue</caption><thead><tr><th>Order / customer</th><th>Type</th><th>Total</th><th>Estimated ready</th><th>Status</th><th>Actions</th></tr></thead><tbody>${result.items.map((o) => `<tr><td><strong>${o.id}</strong><small>${escapeHTML(o.customer.firstName + ' ' + o.customer.lastName)}</small></td><td>${o.type}</td><td>${money(o.total)}</td><td>${dateTime(o.estimatedAt)}</td><td>${badge(o.status)}</td><td><div class="table-actions"><button class="button small secondary" data-detail="${o.id}">Details</button><button class="button small" data-advance="${o.id}" ${o.status === 'Completed' ? 'disabled' : ''}>Next status</button></div></td></tr>`).join('') || '<tr><td colspan="6">No orders match your filters.</td></tr>'}</tbody></table></div>${pagination(result)}`;
      }
      $('#order-search').oninput = debounce(() => {
        pageNumber = 1;
        render();
      });
      $('#order-status').onchange = () => {
        pageNumber = 1;
        render();
      };
      $('#staff-orders-table').onclick = async (e) => {
        const b = e.target.closest('button');
        if (!b) return;
        if (b.dataset.page) {
          pageNumber = Number(b.dataset.page);
          render();
        }
        if (b.dataset.advance) {
          try {
            await orderService.advance(b.dataset.advance);
          } catch (error) {
            notify(error.message);
            return;
          }
          render();
          notify('Order status updated.');
        }
        if (b.dataset.detail) {
          const o = orderService.get(b.dataset.detail);
          openDialog(
            o.id + ' · Order details',
            `<p>${escapeHTML(o.customer.firstName + ' ' + o.customer.lastName)} · ${o.type}</p><p>${escapeHTML(o.customer.phone)} · ${escapeHTML(o.customer.email)}</p>${o.address ? `<p>${escapeHTML(Object.values(o.address).join(', '))}</p>` : ''}<ul class="order-line-list">${o.items.map((i) => `<li><div><strong>${i.quantity} × ${escapeHTML(itemName(i))}</strong><small>${escapeHTML(itemDetails(i))}</small>${i.instructions ? `<p>Note: ${escapeHTML(i.instructions)}</p>` : ''}</div></li>`).join('')}</ul><p><strong>${money(o.total)}</strong> · ${escapeHTML(o.status)}</p><p class="field-hint">Stock was deducted on order submission. Advancing status does not deduct it again.</p>`,
          );
        }
      };
      render();
    },
  };
}
export function staffInventory() {
  let pageNumber = 1;
  return {
    html: `<section class="section compact staff-content"><div class="section-heading"><div><p class="eyebrow">FRESH INGREDIENTS. CLEAR NUMBERS.</p><h1>What’s in stock.</h1><p class="muted">Order recipes deduct cups and drink units when checkout succeeds.</p></div></div><div class="filters"><div><label for="inventory-search">Search ingredients</label><input id="inventory-search" type="search" placeholder="Marinara, cheese, pepperoni…"></div><div><label for="inventory-category">Category</label><select id="inventory-category"><option value="">All categories</option>${['Base', 'Meat', 'Vegetables', 'Drinks'].map((c) => `<option>${c}</option>`).join('')}</select></div><div><label for="inventory-status">Stock status</label><select id="inventory-status"><option value="">All stock</option><option>Low Stock</option><option>Out of Stock</option><option>In Stock</option></select></div></div><div id="inventory-table"></div><section class="panel recipe-note"><h2>The recipe behind the numbers.</h2><p>Each pizza includes marinara and cheese: small ¼ cup each, medium ½ cup each, large 1 cup each. Toppings use ⅛, ¼, or ½ cup by size. Every drink uses one stock unit.</p></section></section>`,
    mount() {
      function render() {
        const result = inventoryService.list({
          branchId: employeeService.branch(),
          search: $('#inventory-search').value,
          category: $('#inventory-category').value,
          status: $('#inventory-status').value,
          pageNumber,
        });
        $('#inventory-table').innerHTML =
          `<div class="table-wrap panel"><table><caption class="sr-only">Ingredient stock by branch</caption><thead><tr><th>Ingredient</th><th>On hand</th><th>Reorder level</th><th>Status</th><th>Last restocked</th><th>Actions</th></tr></thead><tbody>${result.items.map((i) => `<tr><td><strong>${i.name}</strong><small>${i.category} · ${i.supplier}</small></td><td>${i.quantity.toFixed(3).replace(/\.?0+$/, '')} ${i.unit}</td><td>${i.reorderLevel} ${i.unit}</td><td><span class="badge ${stockStatus(i) === 'In Stock' ? 'good' : 'warning'}">${stockStatus(i)}</span></td><td>${dateTime(i.lastRestocked)}</td><td><div class="table-actions"><button class="button small secondary" data-stock="${i.id}">Update</button><button class="button small" data-restock="${i.id}">Restock</button></div></td></tr>`).join('') || '<tr><td colspan="6">No matching inventory in this branch. Riverside is a future branch with no stock seeded.</td></tr>'}</tbody></table></div>${pagination(result)}`;
      }
      $('#inventory-search').oninput = debounce(() => {
        pageNumber = 1;
        render();
      });
      for (const id of ['inventory-category', 'inventory-status'])
        $('#' + id).onchange = () => {
          pageNumber = 1;
          render();
        };
      $('#inventory-table').onclick = async (e) => {
        const b = e.target.closest('button');
        if (!b) return;
        if (b.dataset.page) {
          pageNumber = Number(b.dataset.page);
          render();
          return;
        }
        const id = b.dataset.stock || b.dataset.restock;
        if (!id) return;
        const i = inventoryService.all(employeeService.branch()).find((i) => i.id === id);
        const restock = !!b.dataset.restock;
        openDialog(
          (restock ? 'Restock ' : 'Update ') + i.name,
          `<form id="stock-form"><div id="stock-error"></div><p>Currently ${i.quantity} ${i.unit} on hand.</p><label for="stock-amount">${restock ? 'Amount to add' : 'New quantity on hand'} (${i.unit})</label><input id="stock-amount" name="amount" type="number" min="0" max="100000" step="0.001" value="${restock ? '' : i.quantity}" required><button class="button full">${restock ? 'Add stock' : 'Save stock'}</button></form>`,
          (dialog) => {
            $('#stock-form', dialog).onsubmit = async (e) => {
              e.preventDefault();
              try {
                await inventoryService.update(
                  id,
                  employeeService.branch(),
                  new FormData(e.target).get('amount'),
                  restock,
                );
                dialog.close();
                render();
                notify('Ingredient stock updated.');
              } catch (err) {
                $('#stock-error', dialog).innerHTML = errorBox(err.message);
              }
            };
          },
        );
      };
      render();
    },
  };
}
export function staffSupport() {
  let pageNumber = 1;
  return {
    html: `<section class="section compact staff-content"><p class="eyebrow">EVERY ISSUE DESERVES A RESPONSE</p><h1>Support tickets.</h1><p class="muted">${employeeService.current().role === 'Administrator' ? 'Organization-wide escalations' : 'Tickets linked to your branch’s orders. General tickets require an administrator.'}</p><div id="tickets-table"></div></section>`,
    mount() {
      function render() {
        const state = store.read();
        const admin = employeeService.current().role === 'Administrator';
        const result = page(
          state.tickets.filter(
            (t) =>
              admin ||
              state.orders.some(
                (o) => o.id === t.orderId && o.branchId === employeeService.branch(),
              ),
          ),
          pageNumber,
        );
        $('#tickets-table').innerHTML =
          `<div class="table-wrap panel"><table><thead><tr><th>Ticket / customer</th><th>Category</th><th>Order</th><th>Created</th><th>Status</th><th>Action</th></tr></thead><tbody>${result.items.map((t) => `<tr><td><strong>${escapeHTML(t.id)}</strong><small>${escapeHTML(t.customerName)}</small></td><td>${escapeHTML(t.category)}</td><td>${escapeHTML(t.orderId || '—')}</td><td>${dateTime(t.createdAt)}</td><td>${badge(t.status)}</td><td><button class="button small secondary" data-ticket="${t.id}">Review</button></td></tr>`).join('') || '<tr><td colspan="6">No tickets in this view.</td></tr>'}</tbody></table></div>${pagination(result)}`;
      }
      $('#tickets-table').onclick = async (e) => {
        const b = e.target.closest('button');
        if (!b) return;
        if (b.dataset.page) {
          pageNumber = Number(b.dataset.page);
          render();
        }
        if (b.dataset.ticket) {
          const t = store.read().tickets.find((t) => t.id === b.dataset.ticket);
          openDialog(
            'Review ' + t.id,
            `<p><strong>${escapeHTML(t.customerName)}</strong> · ${escapeHTML(t.category)}</p><p>${escapeHTML(t.description)}</p><h3>Conversation summary</h3><pre class="conversation-summary">${escapeHTML(t.summary)}</pre><form id="ticket-update"><label for="ticket-status">Escalation status</label><select id="ticket-status">${['Escalated', 'In Review', 'Resolved'].map((s) => `<option ${t.status === s ? 'selected' : ''}>${s}</option>`).join('')}</select><button class="button full">Save status</button></form>`,
            (dialog) => {
              $('#ticket-update', dialog).onsubmit = async (e) => {
                e.preventDefault();
                try {
                  await supportService.update(t.id, $('#ticket-status', dialog).value);
                } catch (error) {
                  notify(error.message);
                  return;
                }
                dialog.close();
                render();
                notify('Ticket status updated.');
              };
            },
          );
        }
      };
      render();
    },
  };
}
export function staffPromotions(refresh) {
  if (employeeService.current().role !== 'Administrator')
    return {
      html: '<section class="section empty"><h1>Administrator demo required.</h1><p>Switch to Luigi to manage promotions. Real permissions must be enforced by a backend.</p></section>',
    };
  const offers = store.read().promotions;
  return {
    html: `<section class="section compact staff-content"><p class="eyebrow">A LITTLE EXTRA REASON TO ORDER</p><h1>Promotions.</h1><div class="offers-grid">${offers.map((p) => `<article class="panel offer"><p class="eyebrow">${escapeHTML(p.id)}</p><h2>${escapeHTML(p.name)}</h2><p>${escapeHTML(p.description)}</p><dl class="totals"><div><dt>Discount</dt><dd>${p.discountType === 'fixed' ? money(p.discountValue) : p.discountValue + '%'}</dd></div><div><dt>Minimum subtotal</dt><dd>${money(p.minSubtotal)}</dd></div><div><dt>Required points</dt><dd>${p.requiredPoints}</dd></div><div><dt>Dates</dt><dd>${p.start}<br>${p.end}</dd></div></dl>${badge(p.active ? 'Active' : 'Inactive')}<div class="item-actions"><button class="button secondary" data-toggle-promo="${p.id}">${p.active ? 'Deactivate' : 'Activate'}</button><button class="text-button" data-edit-promo="${p.id}">Edit offer</button></div></article>`).join('')}</div></section>`,
    mount() {
      $('#main').onclick = async (e) => {
        const toggle = e.target.closest('[data-toggle-promo]');
        if (toggle) {
          try {
            await promotionService.update(toggle.dataset.togglePromo, {
              active: !offers.find((p) => p.id === toggle.dataset.togglePromo).active,
            });
          } catch (error) {
            notify(error.message);
            return;
          }
          refresh();
          notify('Promotion updated.');
        }
        const edit = e.target.closest('[data-edit-promo]');
        if (edit) {
          const p = offers.find((p) => p.id === edit.dataset.editPromo);
          openDialog(
            'Edit ' + p.id,
            `<form id="promotion-edit"><div id="promotion-error"></div><label for="offer-name">Name</label><input id="offer-name" name="name" value="${escapeHTML(p.name)}" required maxlength="100"><label for="offer-description">Description</label><textarea id="offer-description" name="description" required maxlength="300">${escapeHTML(p.description)}</textarea><label for="offer-type">Discount type</label><select id="offer-type" name="discountType"><option value="fixed" ${p.discountType === 'fixed' ? 'selected' : ''}>Fixed (cents)</option><option value="percent" ${p.discountType === 'percent' ? 'selected' : ''}>Percentage</option></select>${[
              ['discountValue', 'Discount value', p.discountValue],
              ['minSubtotal', 'Minimum subtotal (cents)', p.minSubtotal],
              ['requiredPoints', 'Required reward points', p.requiredPoints],
            ]
              .map(
                ([key, label, value]) =>
                  `<label for="offer-${key}">${label}</label><input id="offer-${key}" name="${key}" type="number" min="0" max="100000" step="1" value="${value}" required>`,
              )
              .join(
                '',
              )}<label for="offer-start">Start date</label><input id="offer-start" name="start" type="date" value="${p.start}" required><label for="offer-end">End date</label><input id="offer-end" name="end" type="date" value="${p.end}" required><button class="button full">Save promotion</button></form>`,
            (dialog) => {
              $('#promotion-edit', dialog).onsubmit = async (e) => {
                e.preventDefault();
                const d = Object.fromEntries(new FormData(e.target));
                for (const key of ['discountValue', 'minSubtotal', 'requiredPoints'])
                  d[key] = Number(d[key]);
                if (d.end < d.start || (d.discountType === 'percent' && d.discountValue > 100)) {
                  $('#promotion-error', dialog).innerHTML = errorBox(
                    'Check the date range. Percentage discounts cannot exceed 100.',
                  );
                  return;
                }
                try {
                  await promotionService.update(p.id, d);
                } catch (error) {
                  $('#promotion-error', dialog).innerHTML = errorBox(error.message);
                  return;
                }
                dialog.close();
                refresh();
                notify('Promotion saved.');
              };
            },
          );
        }
      };
    },
  };
}
