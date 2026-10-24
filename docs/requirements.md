# Requirements — Luigi’s Pizzeria Mini Case

> Integration update: the Python-backed mode now uses real local cookie authentication and SQLite persistence. References to mock roles/storage in the original requirement matrix describe the standalone presentation. See `integration.md` and the root README for the active runtime boundaries, supported employee accounts and preserved mock payments/AI.

## Functional requirements

| ID | Requirement | Prototype implementation |
|---|---|---|
| FR-01 | Select small, medium, or large pizza and see diameter. | Menu / builder |
| FR-02 | Configure toppings from centralized data. | Builder checkboxes |
| FR-03 | Update base, toppings, unit price and subtotal live. | Currency module / live summary |
| FR-04 | Enter quantity and optional instructions. | 1–20 validation; 250-character note |
| FR-05 | Add pizza and configurable drinks to a cart. | Cart service / drinks form |
| FR-06 | Edit pizza, update quantity, and remove lines. | Bag / builder edit mode |
| FR-07 | Display consistent subtotal, tax, discount and total. | Single calculation module |
| FR-08 | Select pickup or delivery at checkout. | Native radio controls |
| FR-09 | Validate name, phone, email and conditional delivery address. | Error summary and field errors |
| FR-10 | Simulate online or store payment without card collection. | Demo checkout options |
| FR-11 | Reject empty carts and accidental duplicate submissions. | Service guard, disabled button, submission key |
| FR-12 | Generate unique order number and confirmation. | Order service / confirmation screen |
| FR-13 | Track status, timestamps and estimated readiness. | Timeline and demo status control |
| FR-14 | Estimate completion from pizza/items/queue/fulfillment. | Documented estimation function |
| FR-15 | Award configurable points and display rewards/history. | Rewards service / screens |
| FR-16 | Redeem eligible offers only with sufficient points. | Checkout revalidation and atomic debit |
| FR-17 | Show customer details, saved address, orders and recent pizzas. | Mock account screen |
| FR-18 | Edit simple profile information and switch demo accounts. | Native edit dialog / fictional account select |
| FR-19 | Provide automated support for routine questions. | Mock assistant abstraction |
| FR-20 | Escalate sensitive, complex, uncertain or human-requested issues. | Conservative classification and ticket dialog |
| FR-21 | Keep representative option visible in support. | Persistent support sidebar button |
| FR-22 | Save ticket number, category, customer/order, summary and status. | Support service and staff review |
| FR-23 | Separate staff screens from customer ordering. | Staff routes and navigation |
| FR-24 | Demonstrate administrator and branch employee scope. | Universal employee demo login, guarded staff routes, sign-out and mock employee/branch selection; no security claim |
| FR-25 | Paginate/filter incoming orders and advance statuses. | Staff order queue |
| FR-26 | Search/filter ingredient stock and identify low/out stock. | Inventory table and text badges |
| FR-27 | Update/restock ingredient amounts and timestamps. | Native stock dialog |
| FR-28 | Deduct recipes on successful order placement. | Atomic stock/order/rewards transaction |
| FR-29 | Prevent insufficient-stock orders and double deduction. | Preflight stock validation; status independent of stock |
| FR-30 | Show fictional employees, branches, positions and hire dates. | Staff directory |
| FR-31 | Clock employee in/out; admins review branch shifts; employees see only their own. | Time tracking service, branch selector, administrator verification with reviewer/time |
| FR-32 | Model restricted pay and benefits separately. | SQL only; absent from browser fixture |
| FR-33 | Show eight business KPI cards. | Staff overview |
| FR-34 | Administrators view seven sales chart types and accessible data. | SVG/CSS graphs and tables; daily graphs calculated from branch orders with chronological zero-filled dates |
| FR-35 | Forecast orders/revenue/base ingredients using actual demo orders. | Selected branch seven-calendar-day average, including zero days, with stated assumptions |
| FR-36 | Manage promotion dates/type/value/points/active state. | Administrator promotion editor |
| FR-37 | Model multi-branch relational persistence. | 30 SQL tables and documented relationships |
| FR-38 | Persist local demo activity with clear storage failures. | Store abstraction / transactional localStorage |
| FR-39 | Present branding, hours, featured pizzas, promo, rewards and tracking. | Home/menu |

## Nonfunctional requirements

| ID | Area | Requirement / acceptance target |
|---|---|---|
| NFR-01 | Accessibility | Target WCAG 2.2 AA: semantic landmarks, labels, keyboard controls, focus, modal containment/restoration, non-color status, chart alternatives, announced errors. Manual audit still required. |
| NFR-02 | Reliability | Validate all money/quantity/contact/stock rules; no partial order after error; loading/empty/success/error states; no silent failure. |
| NFR-03 | Usability | Customer ordering stays separate from staff; base/topping prices and estimates are clear; no inactive unlabeled controls. |
| NFR-04 | Performance | Render six rows per admin page; debounce searches; avoid large DOM fixtures; image dimensions reserved. |
| NFR-05 | Security | No keys, real cards, or payroll in browser fixture; the user-requested universal demo credentials are explicitly nonsecure; escape dynamic strings; all production authentication/authorization on server. |
| NFR-06 | Maintainability | ES modules, central configuration/pricing, service/UI separation, explainable estimates and forecasts. |
| NFR-07 | Scalability | Multi-branch IDs and paginated service shapes; future backend/caching/load balancing/monitoring documented; no 80,000-user claim without testing. |
| NFR-08 | Mobile | Reflow at 320, 375, 390, 768, 1024 and 1440px; large actions, browser zoom, contained wide staff tables. |
| NFR-09 | Privacy | Fictional `.test` contacts only; no real personal data requested; local demo persistence explicitly identified. |
| NFR-10 | Portability | Plain static assets/ES modules; zero dependency local server; SQL runnable with SQLite foreign keys enabled. |

## Assumptions to confirm before production

Tax jurisdiction/rate, delivery fee/zones, points eligible spend, cancellation/reversal rules, topping portion sizes, hours enforcement/timezone, promotion reuse, kitchen capacity, data retention, and employee permissions are business decisions. Prototype defaults are documented in README. Production scale and accessibility conformance require measured testing.
