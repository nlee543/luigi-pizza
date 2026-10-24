# Luigi’s Pizzeria

A complete, local college Mini Case prototype built with HTML5, CSS3, and modular vanilla JavaScript. Customers can customize a pizza, check out, track their order, earn rewards, and request support. Employees can advance the same orders, inspect the inventory those orders consumed, track shifts, and review business activity.

## Run locally

Requires Node.js 18 or later. No dependency installation or build step is needed.

If npm is installed, `npm start` and `npm test` are equivalent shortcuts for the commands below. The direct Node commands also work with a standalone Node runtime.

```sh
node scripts/server.js
```

Open **http://localhost:5173** in a browser. Stop the server with Ctrl+C. Set `PORT` to use another port. ES modules require a web server: opening `index.html` directly with `file://` will not work reliably.

Alternative: `python -m http.server 5173` from the project directory. Python is optional and only needed for SQLite verification or this alternative server.

```sh
node --test tests/*.test.js
python scripts/check_database.py
```

With the development server running, `node scripts/check_server.js` checks every local application asset and verifies that the dev server does not serve SQL, README, or Git files.

To create a demonstration SQLite database using the SQLite CLI:

```sh
sqlite3 luigis-demo.db ".read database/schema.sql"
sqlite3 luigis-demo.db ".read database/seed.sql"
```

The browser uses its own fictional data in localStorage; it does **not** connect to this SQL database. The SQL files illustrate the future persistence design. The two seed datasets share business rules but are separate examples, not synchronized copies.

## Client problem and proposed solution

Luigi needs accurate online orders, mobile access, stock visibility, realistic readiness estimates, useful analytics, and a dependable customer support path. This prototype connects those activities around shared services rather than building unrelated restaurant pages.

The customer area has Home, Menu, Build a Pizza, Bag, Checkout, Confirmation, Track Order, Rewards, Account, and Support. The separate Staff demo has Overview, Order Queue, Inventory, Team & Time, Tickets, and administrator-only Promotions. The header/footer provide entry points without mixing staff tools into customer navigation.

## A five-minute presentation

1. Open Home and explain daily hours: **10:00 AM–11:00 PM**.
2. Build a large pizza with pepperoni and mushrooms: **$9.00 + 2 × $3.00 = $15.00**. Change quantity to two: **$30.00**.
3. Add a drink in the Bag. Edit the pizza, apply WELCOME5 if the subtotal is at least $20, then proceed to checkout.
4. Switch between pickup and delivery to show conditional address fields and the $3.00 delivery fee. Use fictional details. Submit a demo order.
5. Show the order number, estimated time, reward points, and tracking timeline. Use “Simulate next step,” or advance the order in Staff → Order Queue.
6. Open Staff → Inventory. Sauce and cheese decrease by two cups for two large pizzas. Restock a low ingredient. Jalapeños start out of stock; attempting an order containing them is rejected without partial changes.
7. Use Employee login in the footer: username **Luigi**, password **Pizza** (case-sensitive). This universal demo login opens Luigi’s administrator workspace. Switch the demo employee to Sam to demonstrate branch-scoped screens. Switch to Luigi for all-branch KPIs, forecasting, and promotion editing. Riverside is a future branch with one example order and no seeded inventory. Use Sign out to close staff access.
8. Open Support and ask about an allergy, payment dispute, or a person. Confirm the ticket details, then review and update the ticket in Staff → Tickets.
9. Open Team & Time as Luigi. The Currently Clocked In card counts employees across all branches; expand it to see names, locations, and clock-in times. Choose a branch to inspect clock-in/out records below. Verify a completed shift; the reviewer and timestamp are recorded. Switch to Sam or Robin to show My Shifts with only that employee’s records. Employees keep the order queue but cannot open revenue/analytics or promotions.
10. Show `database/schema.sql` and the ER diagram in `docs/database-design.md`.

## Business rules and prices

| Size | Diameter | Pizza base | Each topping | Marinara | Cheese | Drink |
|---|---|---:|---:|---|---|---:|
| Small | 8 inches | $5.00 | $1.00 | ¼ cup | ¼ cup | $1.00 |
| Medium | 12 inches | $7.00 | $2.00 | ½ cup | ½ cup | $2.00 |
| Large | 14 inches | $9.00 | $3.00 | 1 cup | 1 cup | $3.00 |

- Marinara and cheese are included in the base. Extra cheese is a charged topping and consumes additional cheese.
- Configurable toppings consume ⅛, ¼, or ½ cup by size. These are **demo assumptions**; only sauce and cheese portions were specified by the client.
- Quantities are whole numbers from 1–20 per line. Multiple lines may be added.
- Prices and recipes live in `js/config.js`. **All** pizza, drink, line, cart, and checkout calculations use `js/utils/currency.js` with integer cents. Tax rounds once per order.
- **Demo assumptions:** tax is 8.25%, delivery is $3.00, and reward points are `floor(final total dollars × 1)` including tax and delivery. Production tax, delivery zones, and reward policy need confirmation.
- WELCOME5 discounts $5.00 on a subtotal of at least $20.00; REWARD5 costs 100 points and discounts $5.00. One offer per order, revalidated at submission. Reward points are deducted only on successful checkout.
- Checkout commits stock deduction, redemption, points earned, order creation, and cart clearing in one local transaction. Failed validation or insufficient stock leaves everything unchanged. Stock is deducted on successful order placement, not each status change.
- Every order has a unique number and a submission key for retry protection. This is a single-browser demonstration, not distributed transaction protection.
- Estimates: `12 + 3 × pizzas + ceil(items / 3) + min(2 × queued orders, 20) + 15 if delivery` minutes. Times are estimates; delivery displays estimated arrival.
- Mock orders are accepted outside business hours for presentation. A backend would enforce actual operating hours and branch availability.

## Technology and organization

No React, Vue, Angular, chart library, or third-party runtime JavaScript dependency. Charts use SVG and CSS with equivalent data tables.

```text
index.html                 Semantic application shell
assets/                    Local pizza photograph and favicon
css/styles.css             Shared brand and component styling
css/customer.css           Ordering, account and support components
css/staff.css              Staff dashboard and management components
css/responsive.css         Breakpoints and reduced motion
js/app.js                  Hash routes and screen lifecycle
js/config.js               Prices, portions, statuses, demo policies
js/data.js                 Fictional initial data
js/services/               Menu, cart, order, inventory, customer,
                           employee, analytics, rewards, support,
                           automated assistant, transactional store
js/components/             Customer and staff screen renderers
js/utils/                  Currency, validation, safe HTML, focus helpers
database/schema.sql        30 normalized relational tables and a view
database/seed.sql          Fictional SQL demonstration data
docs/                      Requirements, ER design, QA checklist
scripts/server.js          Zero-dependency local development server
scripts/check_database.py  In-memory SQLite verification
scripts/check_server.js    Local HTTP asset/access verification
tests/business.test.js     Node business-rule regression tests
tests/screens.test.js      Route rendering, escaping and role-scope checks
```

`store.js` owns reads and mutation. Services return copies, paginated results, and clear errors. UI modules render and bind controls; they do not carry their own pricing formulas. Search is debounced and admin tables render six results per page. Services currently return local results; production versions should request server-filtered, paginated responses.

## Accessibility approach

The target is WCAG 2.2 AA, **not a certified compliance claim**. Semantic landmarks, a skip link, heading hierarchy, explicit labels, native radio/checkbox controls, visible focus, at least 44px actions, error summaries, per-field descriptions, status announcements, and reduced motion support are implemented. Route navigation focuses the main content. Native `<dialog>` provides modal focus containment and Escape dismissal; the helper restores focus on closing.

Charts include expandable data tables. Stock badges and order steps include text instead of relying on color. Mobile layouts collapse grids and preserve browser zoom. Wide staff tables scroll within their own containers; the page should not overflow horizontally. Contrast, keyboard use, screen readers, and 320–1440px layouts still need the manual checks listed in `docs/testing-checklist.md` because the available in-app browser blocked localhost during this build.

## Database

SQLite-compatible SQL uses primary keys, foreign keys, check constraints, unique keys, and indexes. Money uses integer cents and stock uses ingredient units. Recipes connect sizes/products/toppings to ingredients through components. Orders contain price/contact/address snapshots for historical accuracy. Rewards use a transaction ledger and a calculated balance view. Payroll and benefits have separate restricted tables. See `docs/database-design.md` for relationships and transaction responsibilities.

## Automated support architecture

`aiSupportService.reply()` currently uses transparent mock responses and conservative keyword classification. It answers price, menu, order, reward, promotion, hours, and profile questions. Safety, allergy, payment, fraud, employee/legal issues, severe delivery problems, explicit human requests, and uncertainty open an escalation form. Confirming creates a local ticket with customer, order reference, category, description, conversation summary/messages, timestamp, and status. “Talk to a Representative” remains visible on the support screen.

A future `POST /api/support/chat` should authenticate the customer, retrieve only authorized context, keep provider keys server-side, enforce escalation policies outside the model, and log decisions. Ticket creation and notifications require separate server endpoints. The assistant must never grant refunds, change payments, or make unsupported safety claims.

## Mocked functionality and limitations

- Login/roles, payments, kitchen status, support conversations and escalation, and forecasts are mocked. Analytics calculate from actual local demo order records. Employee login uses the user-requested universal **Luigi / Pizza** credentials, stored in source solely for this demonstration. All staff routes redirect to login until signed in; sessionStorage keeps the demo session for the browser tab, and Sign out clears it. This client-side gate is bypassable and is not secure password protection. No real restaurant receives orders or tickets; no real charge occurs.
- Data persists only in this browser’s localStorage. Do not enter real personal data. Browser users can inspect and modify it, including staff roles. Switching roles merely demonstrates UI scope.
- No real-time synchronization between employees/devices. A storage event refreshes another tab but cannot prevent concurrent lost writes.
- The customer currently orders from Downtown. Staff can inspect Downtown/Riverside, but customer branch selection is a future feature.
- Inventory transactions have no server audit log or cancellation reversal UI; SQL models movements for that future work. Seed stock is a post-order snapshot.
- Customer promotion assignment tables model future targeted/single-use offers. The current demo permits reuse of WELCOME5. Earned points are credited on placement; cancellation/refund reversal requires a backend policy.
- Revenue/analytics are administrator-only, with both route and service-level demo role checks. Employees retain order queue, inventory, support tickets and their own shifts. The demo employee selector remains a presentation tool, not a secure identity system.
- Revenue/orders by day use the selected branch’s actual demo orders over 14 chronological calendar days. Missing days are zero; revenue is subtotal minus discount, excluding tax/delivery. Counts include active and completed orders. Today’s chart values reconcile with today’s KPIs. The old synthetic salesHistory array is ignored. Category sales allocate discounts proportionally so category totals reconcile with net revenue.
- Forecasts use the same branch’s last seven calendar days, including today and zero-order days; assumptions are illustrative, not machine learning. Fresh fixtures have orders only near the current time, so older days correctly show zero. Hour/date buckets use the local browser timezone.
- Native browser validation and local data validation are not substitutes for server validation, security, payment compliance, or an accessibility audit.
- The photograph is illustrative. All menu cards reuse it and label its contents; it does not depict every configured topping. Fonts fall back to system fonts offline.

## Production backend and scale

The 70,000–80,000 interaction requirement is an architecture consideration, not a load test result. Production needs authenticated application servers, an API, a database server, server-enforced branch/role permissions, TLS, caching, load balancing as traffic grows, monitoring/logging, backups, rate limiting, and production hosting.

Suggested endpoints mirror the services: `GET /menu`, `GET /orders?cursor=...&branch=...`, `POST /orders` with an idempotency key, `PATCH /orders/:id/status`, `GET /inventory`, `POST /inventory/:id/movements`, `/customers/me`, `/rewards`, `/employees/shifts`, `/analytics`, `/promotions`, `/support/tickets`, and `/support/chat`.

Order creation must authoritatively recalculate totals and use one database transaction to lock/check stock, insert nonempty items, record payments, debit inventory, and update rewards. Enforce required delivery/contact details and authorized ownership. Use a payment provider’s hosted/tokenized flow, never client-side card storage. Status updates may arrive by polling or server-sent events. SQLite is useful for this class demo; choose a suitable production database and capacity-test the API before claiming scale.

Payroll/benefits must use restricted endpoints and access controls, encryption where appropriate, and audit logging. The browser fixture deliberately contains no pay/benefit details. The universal demo password is included at the user’s request; never use it as a production credential. No API keys are included.

## Initial Scrum backlog

| Priority | User story | Acceptance criteria |
|---|---|---|
| P1 | As a customer, I want to customize pizza so I can order what I like. | All three required sizes/prices; toppings update instantly; invalid quantities rejected; controls work by keyboard. |
| P1 | As a customer, I want a clear total before checkout. | One pricing module; edit/remove/add drinks; two-decimal display; tax, discount, delivery shown. |
| P1 | As a customer, I want to submit my order reliably. | Empty cart blocked; delivery address conditional; field errors linked; duplicate retries return the same order; no real cards collected. |
| P1 | As a manager, I want stock to reflect orders. | Exact sauce/cheese portions; topping recipes independent of prices; failed stock checks commit nothing; clear low/out-of-stock labels. |
| P1 | As an employee, I want an incoming order queue. | Branch filtering, pagination, item details and status advance; stock never deducted twice. |
| P2 | As a customer, I want to track readiness. | Order number, timeline, current status, received/updated times, estimated minutes and explicit uncertainty. |
| P2 | As a customer, I want rewards for purchases. | Configurable conversion; visible balance/history; insufficient balances cannot redeem; debit only after successful order. |
| P2 | As a customer with a problem, I want a person when needed. | Automated identity; representative button always present on Support; conservative escalation; complete locally reviewable ticket. |
| P2 | As an administrator, I want analytics and forecasts. | Eight KPIs; seven chart types with data tables; forecast labeled and explained; organization summary. |
| P2 | As an employee, I want to track my hours. | One open shift per employee; clock in/out; branch/date/hour display. |
| P3 | As a manager, I want to configure promotions. | Edit amount/type/dates/points and active status; checkout revalidates eligibility. |
| Future | As an owner, I want secure multi-branch operations. | Server authorization, concurrency-safe stock, payment integration, monitoring and capacity tests. |

Suggested sprints: (1) menu/builder/pricing/cart; (2) checkout/orders/inventory; (3) staff/analytics/rewards/support; (4) database/docs/accessibility and real-backend planning. Definition of done: feature works, business checks pass, QA checklist is recorded, docs agree, and mock boundaries are explicit.

## Asset credit

Local pizza image: [manoo manoo on Unsplash](https://unsplash.com/photos/iPh0NDrYpzI), downloaded from Unsplash’s image endpoint for the college prototype. Display typography: Manrope; body: DM Sans via Google Fonts, with local system fallbacks. Favicon is a project-authored letter mark.
