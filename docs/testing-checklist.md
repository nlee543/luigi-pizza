# Testing checklist

## Recorded verification

### Integrated application verification (October 24, 2026)

- **PASS:** 26 frontend regression tests, including role scoping and active roster behavior.
- **PASS:** final backend suite: **143 tests passed** (original team checks plus 10 integration tests). Includes sessions/CSRF, ownership, same-size pizzas, authoritative totals, stock/reward transactions, retries, branch scope, shifts, promotions, tickets, profiles, registration, legacy-write protection, rule parity and restart persistence. One non-failing upstream TestClient/httpx deprecation warning remains.
- **PASS:** all **43 application assets** load through the integrated server; database/source/README/Git routes are inaccessible.
- **PASS, browser walkthrough:** database-backed Luigi login, branch review, saved closed-shift verification, customer Alex login, pizza customization/cart/checkout, confirmation LP-1057 ($15.00 subtotal, $1.24 tax, $16.24 total, 16 reward points), Sam login, shared order visibility/status advance, own-shift-only screen and missing admin navigation.
- **PASS, responsive spot checks:** employee My Shifts page at 320, 390, 768 and 1440px had no document-level horizontal overflow. This is not an exhaustive visual audit of every screen.
- **PASS, final admin layout check:** Order Queue at 320, 768, 1024 and 1440px has no document-level horizontal overflow after the staff-navigation wrapping fix. Tables scroll within their containers. The final preview screenshot is `integration-preview.png`.
- **PASS, restart walkthrough:** restarted with the documented Python launcher; Luigi login still worked, LP-1057 remained in the shared data, and the dashboard included its $15.00 net revenue (Downtown total $341.00 / 16 orders during the verification session).
- **Still pending:** full keyboard traversal, screen-reader audit, complete responsive matrix and production load/security tests. Earlier localhost browser failures below describe the original build; current integrated preview is browser-accessible.

### Original standalone build history

Automated checks during this build:

- **PASS:** 16 Node tests covering exact pizza/drink prices, topping/quantity validation, tax/discount/delivery cents, recipe portions, checkout address/contact validation, estimates, cart edits/removal, atomic stock/reward/order commit, idempotency, stock rollback, reward eligibility, promotion minimums, AI escalation, all screen renderers, escaped customer text, branch scope and support-ticket references.
- **PASS:** all JavaScript files parse with `node --check`.
- **PASS:** schema and seed execute in SQLite; 30 tables, foreign keys, integrity, line subtotals, recipe portions, required delivery addresses, nonempty seeded orders, and integrity constraints verified.
- **PASS:** live local HTTP check: all 35 HTML/CSS/JavaScript/image assets return 200; SQL, README and Git files return 404.
- **NOT VERIFIED:** visual layouts, keyboard traversal, screen-reader output and browser end-to-end interactions. The available browser tool returned `net::ERR_BLOCKED_BY_CLIENT` for both localhost and 127.0.0.1. Do not treat the following manual checklist as completed.

Run `node --test tests/*.test.js` and `python scripts/check_database.py` to repeat automated checks. All tests use fictional or in-memory data. If npm is installed, `npm start` and `npm test` are equivalent shortcuts.

## Ordering

- [ ] Small: $5.00 base, $1.00 per topping; medium: $7.00/$2.00; large: $9.00/$3.00.
- [ ] Base includes marinara and cheese; large with two toppings is $15.00; quantity two is $30.00.
- [ ] Small/medium/large drinks are $1.00/$2.00/$3.00.
- [ ] Select/remove toppings and change size; live summary matches Bag and confirmation.
- [ ] Reject 0, negative, fractional and >20 quantities without losing the cart.
- [ ] Edit an existing pizza without adding a duplicate line.
- [ ] Update cart quantities, remove products and reorder a previous order at current prices.
- [ ] Tax rounds once, discounts apply before tax, delivery adds $3.00. Every money value has two decimals.
- [ ] Promo minimum/expiration/inactive status and insufficient reward balances prevent checkout; removing offer restores checkout.

## Inventory

- [ ] One small consumes ¼ cup sauce/cheese each; medium ½ cup each; large 1 cup each.
- [ ] Multiple quantities sum correctly. Extra cheese adds its topping recipe portion.
- [ ] Each drink reduces the selected beverage stock by one unit per quantity.
- [ ] Low/out-of-stock text appears; jalapeños are out and sausage/iced tea are low initially.
- [ ] Attempt an out-of-stock order; cart, points and orders stay unchanged.
- [ ] Advance status repeatedly; stock is never deducted twice.
- [ ] Search, category/status filter, and page through results.
- [ ] Update stock and restock; reject negative/non-numeric amounts and update restock timestamp.
- [ ] Staff branch selection does not change the Downtown customer fulfillment branch.

## Checkout and tracking

- [ ] Empty cart cannot checkout.
- [ ] Name/phone/email errors appear in a focused summary and alongside labeled fields.
- [ ] Invalid email and short/invalid phone are rejected.
- [ ] Pickup ignores hidden address fields. Delivery requires street/city/state/ZIP with valid state/ZIP.
- [ ] Switch back to pickup; address fields leave validation and keyboard order.
- [ ] No card-number fields; payment is explicitly simulated.
- [ ] Double click or retry creates only one order.
- [ ] Stock failure shows an understandable error and permits correction.
- [ ] Confirmation includes number/items/name/type/timestamp/total/points/status/estimate.
- [ ] Track by number, including unknown and another customer’s order; show appropriate errors.
- [ ] Timeline differentiates ready for pickup and out for delivery, and can advance to completed.
- [ ] Estimate increases for more pizzas/queue/delivery; remaining minutes never negative.

## Rewards, account and support

- [ ] Points earned/debited match the configured rule; redemption is not charged before successful checkout.
- [ ] Switch demo customer; profile/history/balance follow the selected account.
- [ ] Edit contact/saved address; validation rejects incomplete address.
- [ ] Menu/price/reward/order/hour/promotion answers are accurate and identify automation.
- [ ] Refund, fraud/payment, allergy/safety, repeated failures, severe delivery, employee/legal concerns, explicit human request and uncertainty offer escalation.
- [ ] Representative button remains available during chat.
- [ ] Ticket contains number/customer/order/category/description/summary/messages/time/status.
- [ ] Review ticket from staff and change Escalated → In Review → Resolved.
- [ ] Navigate away while assistant is thinking; no visible failure or corrupted conversation.

## Staff and analytics

- [ ] Employee login accepts Luigi / Pizza (case-sensitive), rejects incorrect entries with an announced error, and opens the staff workspace.
- [ ] Direct staff URLs redirect to login when signed out; successful login returns to the requested staff route.
- [ ] Refresh preserves the tab’s demo session; Sign out prevents reopening staff screens without login. This is a bypassable front-end demo gate, not secure authorization.

- [ ] Sam/Robin see their assigned branch; Luigi can choose branches and manage offers/forecast.
- [ ] Customer navigation never includes payroll/employee tools.
- [ ] Orders search/filter/pagination and details/status changes work.
- [ ] All eight KPIs are labeled and have correct current-day scope.
- [ ] Seven chart types have accessible equivalent data tables.
- [ ] Employees have no Overview link; direct overview URLs go to Order Queue, and analytics service calls reject non-admin roles.
- [ ] Daily revenue/counts derive from branch order records, sort chronologically, include zero-order days, and reconcile with today’s KPIs. Category revenue includes allocated discounts.
- [ ] Team & Time has an administrator branch selector and exact clock-in/out records; closed shifts can be verified with reviewer/time.
- [ ] Branch employees see only their own shift history and hours; they cannot verify shifts or inspect another employee’s records.
- [ ] Administrator Currently Clocked In card counts all branches and expands to list each employee’s name, actual shift branch and clock-in time. Clock-out removes the employee from the roster and total; branch employees can expand only their own active shift.
- [ ] Forecast explicitly says forecast and explains seven-day average/portion assumptions.
- [ ] Clock in/out prevents multiple open shifts; hours and active counts update.
- [ ] Promotion edits validate dates/percentage and affect checkout eligibility.

## Accessibility

- [ ] Tab through each route without a mouse; skip link reaches main.
- [ ] Focus is visible and unobscured; route changes focus main and no sticky layer hides controls.
- [ ] Every input/select has a programmatically associated label; grouped controls have legends.
- [ ] Native dialogs contain keyboard focus, close with Escape/close button, and restore focus to the trigger after rerender.
- [ ] Validation summary links focus erroneous fields; errors announce and `aria-invalid` is set.
- [ ] Builder price/cart updates and support messages announce without excessive repetition.
- [ ] Screen reader can read order status steps, stock warnings and chart tables.
- [ ] Text contrast is at least 4.5:1; large text/essential control boundaries meet applicable AA ratios.
- [ ] Test 200% text size and 400% page zoom / 320 CSS pixel reflow.
- [ ] Touch actions remain at least 44px in this design; controls do not overlap.
- [ ] Reduced-motion setting disables transitions; browser zoom remains enabled.

## Responsive / visual

| Width | Screen | Checks | Result |
|---|---|---|---|
| 320px | Small phone | Nav, builder, two-column choices, forms, checkout, dialogs; no page overflow | Pending |
| 375px | Phone | Hero, bag quantities, rewards, support | Pending |
| 390px | Large phone | Entire order flow and touch controls | Pending |
| 768px | Tablet | Side-by-side panels, labels, charts, contained tables | Pending |
| 1024px | Laptop | Navigation and three-column menu | Pending |
| 1440px+ | Desktop | Max-width spacing, hero, staff dashboard | Pending |

Staff data tables intentionally scroll inside their containers. Confirm the surrounding document remains within the viewport at every width. Image loading and font fallbacks should preserve usable layouts offline.

## Reliability and security

- [ ] Disable or exhaust localStorage; show understandable errors and avoid partial commits.
- [ ] Corrupt saved data; display recovery feedback or the route error state.
- [ ] Two browser tabs refresh on changes; document that concurrent writes are not guaranteed.
- [ ] Enter `<script>`/HTML in notes, profile names, chat and tickets; display text, never execute it.
- [ ] Inspect browser fixture: no real keys/passwords/cards or employee pay/benefits.
- [ ] Explain that switching roles/hiding buttons is not production authorization.

## Production-only testing

API authorization/ownership, inventory concurrency, payment provider idempotency, fraud handling, tax jurisdictions, delivery-zone checks, order/refund reversals, durable backups, rate limiting, capacity/load tests, and third-party accessibility review remain outside this local prototype.
