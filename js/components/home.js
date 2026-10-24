import { FEATURED, SIZES } from '../config.js';
import { money, unitPrice } from '../utils/currency.js';
import { PIZZA_PHOTOS } from '../utils/pizzaPhotos.js';
export function featuredCards() {
  return FEATURED.map(
    (p) =>
      `<article class="menu-card"><div class="pizza-photo"><img src="${PIZZA_PHOTOS[p.id].src}" alt="${PIZZA_PHOTOS[p.id].alt}" width="${PIZZA_PHOTOS[p.id].width}" height="${PIZZA_PHOTOS[p.id].height}" loading="lazy"><span class="photo-label">${p.tag}</span></div><div class="menu-card-body"><div class="row"><h3>${p.name}</h3><strong>${money(unitPrice({ kind: 'pizza', size: 'large', toppings: p.toppings }))}</strong></div><p>${p.description}</p><div class="row"><small>Large · 14″${p.toppings.length ? ' · ' + p.toppings.length + ' topping' + (p.toppings.length > 1 ? 's' : '') : ''}</small><a class="text-link" href="#builder?featured=${p.id}">Make it yours <span aria-hidden="true">+</span></a></div></div></article>`,
  ).join('');
}
export function home() {
  return `<section class="hero"><div class="hero-copy"><div class="eyebrow"><span class="tiny-line"></span> YOUR NEW FAVORITE PIZZA PLACE</div><h1>A little crust.<br>A lot of <em>love.</em></h1><p>Fresh ingredients. Golden crusts. Your pizza, your way.<br>Good times start with Luigi’s.</p><div class="hero-actions"><a class="button" href="#builder">Order now <span aria-hidden="true">+</span></a><a class="button secondary" href="#menu">Explore the menu</a></div><div class="hero-details"><span><strong>Made to order</strong><small>Fresh from our oven</small></span><span><strong>Pickup or delivery</strong><small>Whatever your plans</small></span></div></div><div class="hero-image"><img src="assets/pizza.jpg" alt="Golden cheese pizza with fresh basil on a wooden board" width="1000" height="667" fetchpriority="high"><div class="image-note"><span>THE GOOD STUFF</span><strong>Fresh. Hot. Yours.</strong></div><div class="round-stamp" aria-hidden="true">FRESH<br>FROM THE<br><b>OVEN</b></div></div></section><section class="promise-strip" aria-label="Our pizza basics"><span>MADE FRESH DAILY</span><span>MARINARA + CHEESE INCLUDED</span><span>PIZZAS FROM $5.00</span><span>GOOD FOOD, NO FUSS</span></section><section class="section"><div class="section-heading"><div><p class="eyebrow">THE USUALS, BUT BETTER</p><h2>Meet your next favorite.</h2></div><a class="text-link" href="#menu">View the full menu <span aria-hidden="true">+</span></a></div><div class="menu-grid">${featuredCards()}</div></section><section class="promo-band"><div><p class="eyebrow">A LITTLE SOMETHING FOR YOU</p><h2>Your first bite comes<br>with $5 off.</h2><p>Use <strong>WELCOME5</strong> on an order of $20 or more.</p><a class="button light" href="#builder">Start your order</a></div><div class="promo-type" aria-hidden="true">GOOD<br><em>taste.</em><span>GREAT COMPANY.</span></div></section><section class="section quick-links"><a href="#track"><span class="link-number">01</span><h3>From oven to doorstep.</h3><p>Follow your order, every step of the way.</p><span class="text-link">Track your order +</span></a><a href="#rewards"><span class="link-number">02</span><h3>Good pizza pays you back.</h3><p>Earn a point for every dollar. Your next treat is closer.</p><span class="text-link">Explore rewards +</span></a><a href="#support"><span class="link-number">03</span><h3>We’re here for you.</h3><p>Quick answers or a hand from a representative.</p><span class="text-link">Get support +</span></a></section>`;
}
export function menu() {
  return `<section class="page-head"><p class="eyebrow">FRESH FROM THE OVEN</p><h1>The menu.</h1><p>A good pizza starts with a great base. Marinara and cheese are always included.</p></section><section class="section compact"><h2>Pick your perfect size.</h2><div class="size-grid">${Object.entries(
    SIZES,
  )
    .map(
      ([id, s]) =>
        `<article class="size-card"><span class="eyebrow">${s.diameter} INCHES</span><h3>${s.name}</h3><div class="price">${money(s.baseCents)}</div><p>+ ${money(s.toppingCents)} per topping</p><small>Marinara + cheese included<br>${s.portionCups} cup of each</small><a class="button secondary" href="#builder?size=${id}">Build a ${id} pizza</a></article>`,
    )
    .join(
      '',
    )}</div></section><section class="section compact"><div class="section-heading"><h2>The house favorites.</h2><span class="muted">Shown as large · customize any size</span></div><div class="menu-grid">${featuredCards()}</div></section><section class="section compact drink-banner"><div><p class="eyebrow">SOMETHING TO SIP</p><h2>Make it a meal.</h2><p>Classic cola · Lemon-lime soda · Iced tea · Sparkling water</p><p><strong>Small $1.00 · Medium $2.00 · Large $3.00</strong></p></div><a class="button" href="#cart">Add a drink</a></section>`;
}
