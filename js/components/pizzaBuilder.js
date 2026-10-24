import { SIZES, TOPPINGS, FEATURED } from '../config.js';
import { cartService } from '../services/cartService.js';
import { money, unitPrice, lineTotal } from '../utils/currency.js';
import { $, $$, escapeHTML, notify, errorBox } from '../utils/dom.js';
import { photoForToppings } from '../utils/pizzaPhotos.js';
export function pizzaBuilder(params) {
  const editing = cartService.list().find((i) => i.id === params.get('edit') && i.kind === 'pizza');
  const featured = FEATURED.find((p) => p.id === params.get('featured'));
  const pizza = editing
    ? structuredClone(editing)
    : {
        kind: 'pizza',
        size: SIZES[params.get('size')] ? params.get('size') : 'large',
        toppings: featured?.toppings || [],
        quantity: 1,
        instructions: '',
      };
  return {
    html: `<section class="page-head"><p class="eyebrow">YOUR PIZZA. YOUR RULES.</p><h1>${editing ? 'Edit your pizza.' : 'Build something delicious.'}</h1><p>Start with marinara and cheese. Make the rest your own.</p></section><section class="section compact builder-layout"><form id="builder-form"><fieldset><legend><span class="step-number">1</span>Choose your size</legend><div class="builder-sizes">${Object.entries(
      SIZES,
    )
      .map(
        ([id, s]) =>
          `<label class="choice-card"><input type="radio" name="size" value="${id}" ${pizza.size === id ? 'checked' : ''}><strong>${s.name} <span>${s.diameter}″</span></strong><b>${money(s.baseCents)}</b><small>+ ${money(s.toppingCents)} / topping</small></label>`,
      )
      .join(
        '',
      )}</div></fieldset><fieldset><legend><span class="step-number">2</span>Make it yours</legend><p class="field-hint">Marinara and cheese are included. Each selected topping counts once.</p><div class="topping-grid">${TOPPINGS.map((t) => `<label class="topping-choice"><input type="checkbox" name="toppings" value="${t.id}" ${pizza.toppings.includes(t.id) ? 'checked' : ''}><span>${t.name}</span><small class="topping-price"></small></label>`).join('')}</div></fieldset><fieldset><legend><span class="step-number">3</span>The finishing touches</legend><label for="pizza-qty">Quantity</label><input class="quantity-input" id="pizza-qty" name="quantity" type="number" min="1" max="20" step="1" value="${pizza.quantity}" required><label for="instructions">Special instructions <span class="muted">(optional)</span></label><textarea id="instructions" name="instructions" rows="3" maxlength="250" placeholder="Anything we should know?">${escapeHTML(pizza.instructions)}</textarea><small>For allergies, contact a representative before ordering. Instructions cannot guarantee an allergen-free meal.</small></fieldset><div id="builder-error"></div></form><aside class="builder-summary panel"><div class="summary-photo"><img src="assets/pizza.jpg" alt="A freshly baked pizza; your selections are summarized below" width="1000" height="667"></div><div class="panel-body"><p class="eyebrow">MADE JUST FOR YOU</p><h2>Your pizza</h2><div id="pizza-summary" aria-live="polite" aria-atomic="true"></div><button class="button full" type="submit" form="builder-form">${editing ? 'Save changes' : 'Add to bag'} <span aria-hidden="true">+</span></button><p class="field-hint">Prepared fresh at our Downtown branch.</p></div></aside></section>`,
    mount() {
      const form = $('#builder-form');
      const read = () => {
        const data = new FormData(form);
        return {
          ...pizza,
          size: data.get('size'),
          toppings: data.getAll('toppings'),
          quantity: Number(data.get('quantity')),
          instructions: data.get('instructions'),
        };
      };
      function update() {
        const item = read();
        const photo = photoForToppings(item.toppings);
        const preview = $('.summary-photo img');
        if (preview.getAttribute('src') !== photo.src) preview.src = photo.src;
        preview.alt = photo.alt;
        preview.width = photo.width;
        preview.height = photo.height;
        const s = SIZES[item.size];
        $$('.topping-price').forEach((e) => (e.textContent = money(s.toppingCents)));
        try {
          const subtotal = lineTotal(item);
          $('#pizza-summary').innerHTML =
            `<p><strong>${s.name} · ${s.diameter}″</strong><br><span class="muted">${item.toppings.length ? item.toppings.map((id) => TOPPINGS.find((t) => t.id === id).name).join(', ') : 'Classic marinara + cheese'}</span></p><dl class="totals"><div><dt>Base pizza</dt><dd>${money(s.baseCents)}</dd></div><div><dt>${item.toppings.length} topping${item.toppings.length !== 1 ? 's' : ''} × ${money(s.toppingCents)}</dt><dd>${money(item.toppings.length * s.toppingCents)}</dd></div><div><dt>Pizza price</dt><dd>${money(unitPrice(item))}</dd></div><div><dt>Quantity</dt><dd>${item.quantity}</dd></div><div class="total"><dt>Subtotal</dt><dd>${money(subtotal)}</dd></div></dl>`;
          $('#builder-error').textContent = '';
        } catch (e) {
          $('#builder-error').innerHTML = errorBox(e.message);
        }
      }
      form.oninput = update;
      form.onchange = update;
      update();
      form.onsubmit = (e) => {
        e.preventDefault();
        try {
          const item = read();
          if (editing) cartService.update(editing.id, item);
          else cartService.add(item);
          notify(editing ? 'Pizza updated.' : 'Your pizza is in the bag.');
          location.hash = 'cart';
        } catch (error) {
          $('#builder-error').innerHTML = errorBox(error.message);
        }
      };
    },
  };
}
