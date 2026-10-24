# Integration decisions

## Sources

Shared backend files in both supplied ZIPs matched byte-for-byte. The SageZ-jpg branch additionally contained an older frontend that calls outdated `/users` routes and uses the older PUT status contract. The included API requires authenticated sessions, CSRF, and PATCH for statuses. The integrated application serves the root `index.html`; the unused alternate frontend was removed during cleanup.

The original team history remains in Git. `backend/README.md` retains the team's backend documentation; the root README covers the integrated application. Scrum planning is in `docs/backlog.md`. Local ZIP backups are excluded from the repository.

## Mapping

| UI field | Team model / mapping |
|---|---|
| `size`, `baseCents` | `Pizza.id`, size, decimal price; size maps to catalog primary key. |
| `drinkId` + size | One numeric `Drink.id` per beverage/size pair. |
| topping string IDs | Numeric `Topping.id` lookup. |
| customer ID, first/last name, phone | Numeric `User.id`, name and phone_number; fixture IDs preserved; new customers use `u<id>`. |
| LP order number | Metadata display ID plus numeric `apiOrderId` FK mapping to `Order.id`. |
| `createdAt` | `Order.order_time`, represented as UTC ISO timestamps. |
| item arrays | Team `OrderPizza`, `OrderDrink`, `OrderTopping` relationships. |
| Order Received, Preparing, Completed | order_received, preparing, completed. |
| Baking, Quality Check | Kept in extension metadata; upstream status remains preparing. |
| Ready for Pickup, Out for Delivery | ready_for_pickup, out_for_delivery. |
| ingredient cups | `Inventory.quantity` multiplied by eight, unit eighth-cup; UI retains exact cups. |
| Administrator, Branch Employee | Team User.role admin/staff, authenticated through original cookies. |
| branch, recipe, rewards, shifts, promotions, tickets | Additive `ui_workspace` extension document; no upstream equivalents existed. |

## Intentional model change

Removed the unique `(order_id,pizza_id)` constraint on `OrderPizza`: two large pizzas with different toppings must remain separate lines. The original REST API continues checking its own one-product-per-request contract; the bridge may write distinct customized lines. The database regression test was updated for this intended behavior. Other imported tests are preserved.

The integrated database is new. An existing legacy database with the old unique index would require a reviewed migration. Initialization refuses to seed over nonempty legacy tables. Do not delete a teammate's database or apply this integration over one without a copy and migration plan.

## Transaction and persistence contract

The frontend does not upload arbitrary state. `/api/bridge/command` accepts named commands: checkout, advance, stock, clock, verify, profile, promotion, ticket and ticket-status. It authenticates using the team's dependencies and CSRF checks, serializes writers with `BEGIN IMMEDIATE`, validates server prices/stock/rewards, updates ORM and extension data together, and commits once. Errors roll back every change. Customer submission keys make retries idempotent.

Order metadata, branch stock, rewards, shifts and support features persist in SQLite's `ui_workspace` JSON document. Numeric mappings connect it to the team's tables. The UI's former local service methods return promises in integrated mode; event handlers await them before announcing success. The cart and chat draft stay local. Data refreshes on login/navigation or Refresh Records; there is no push/polling.

Legacy writes are blocked only in the integrated mount, so direct order/inventory edits cannot bypass metadata or stock/reward rules. The team standalone API remains separately runnable for its tests. Legacy read routes expose the team's original numeric representation.

## Identity and scope

Reuse Argon2, HttpOnly SameSite cookies, session expiry and CSRF headers from `api/auth.py`. Demo usernames map to seeded email accounts. Customer registration uses the original API; new accounts begin with zero points. Profile email is fixed because it is the login identifier; a separate verified email-change flow is future work.

Customer snapshots contain only their own orders/account/reward history/tickets. Staff snapshots contain assigned branch orders/stock/related tickets and only the employee's own shifts. Admins receive all branch records. The integrated identity picker is disabled. Changing a client ID cannot change backend permissions. Staff still see order totals needed for fulfillment; aggregated revenue screens remain admin-only.

Supported employee accounts are the three seeded mapped employees. Future account provisioning needs both the team's user account and branch/employee metadata. The demo has known shared credentials and local HTTP cookie settings: it is not public production hosting.

## Fixture and schema boundaries

`frontend-fixture.json` was exported from our JavaScript `initialData()` and `config.js` and is a versioned server seed/rules input. It is not runtime client data. Seed dates are shifted relative to first startup and then retained. Startup does not run the team's older 100-order kg/liter `seed.py`, which has different units and no login credentials.

The server validates prices from fixture rules mapped to the seeded team catalog. Catalog writes are disabled in integrated mode. Future catalog administration must synchronize authoritative rules and UI menu display through an API; never change just one copy. The integration tests check fixture prices/portions against the JavaScript configuration.

The original 30-table SQL files remain analysis/reference artifacts. Active schema comes from SQLAlchemy plus the extension table. The extension preserves features without discarding team code, but it should eventually be normalized into dedicated tables with SQL pagination and suitable concurrency controls. No high-volume scalability claim is made.

## Startup and serving

The launcher defaults to port 5174 to coexist with the old standalone preview on 5173. UI and API share one origin; no permissive CORS or localStorage auth tokens. Only root, runtime flag, js/css/assets and API routes are served. Python, database files, backups and docs are not static routes.

Use local fictional data. Production needs HTTPS, secure cookies, private provisioning, rate limiting, backups, monitoring, migrations and accessibility/security review. Real payments, AI provider integration, notifications and delivery fulfillment remain future work.
