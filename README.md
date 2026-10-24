# Luigi’s Pizzeria — integrated team application

Our HTML/CSS/vanilla-JavaScript interface now runs with the team’s **FastAPI + SQLAlchemy + SQLite backend**. Original ZIPs are untouched. A pre-integration frontend backup is in `backups/frontend-before-integration.zip`.

## Run the integrated application

From this project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/start-integrated.py
```

Open **http://localhost:5174**. Use that address consistently; localhost and 127.0.0.1 have separate cookies. Stop with Ctrl+C. `node scripts/start.js` or `npm start` launches the same backend.

First-time setup on another computer (Python 3.12 recommended):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe scripts/start-integrated.py
```

On macOS/Linux use `python3 -m venv .venv` and `.venv/bin/python`. Set `PORT` before launching to change ports; the launcher configures matching local allowed origins. No frontend build/install is required.

First startup creates `backend/luigi_pizza.db` with fictional data. Later restarts preserve orders, stock, rewards, profiles, shifts, verification, promotions and tickets. No real data has been imported. Legacy browser-only orders remain in the standalone demo and are not silently imported. This server is loopback-only and configured for local HTTP, not public deployment.

## Demonstration logins

Intentionally public **local demo credentials**, not production secrets. Passwords are stored as Argon2 hashes in the database.

| Account | Login screen | Username/email | Password |
|---|---|---|---|
| Luigi / admin | Employee login | `Luigi` or `luigi@example.test` | `Pizza` |
| Sam / Downtown | Employee login | `Sam` or `sam@example.test` | `EmployeePizza!2026` |
| Robin / Riverside | Employee login | `Robin` or `robin@example.test` | `EmployeePizza!2026` |
| Alex / customer | Account | `alex@example.test` | `CustomerPizza!2026` |
| Jamie / customer | Account | `jamie@example.test` | `CustomerPizza!2026` |
| Casey / customer | Account | `casey@example.test` | `CustomerPizza!2026` |

Customers can register using fictional details and a password of at least 12 characters. The requested short Luigi/Pizza password is retained only for the seeded demo admin. Sign out to change accounts. The role dropdown is disabled in integrated mode: employees must authenticate as themselves. Admins can choose branches to review.

## Connected features

- Pizza customization, cart editing, drinks, delivery forms, server-validated checkout, confirmation, tracking, history, points and redemption.
- Shared order queue; saved employee status updates are visible to customers after refresh/navigation.
- Recipe stock deduction on placement; insufficient-stock failures roll back. Status changes never deduct twice.
- Admin branch review, all-branch active roster, exact shift timestamps, clock-in/out and closed-shift verification.
- Staff receive only assigned branch orders/stock/tickets and their own shifts from the integration API. Revenue Overview remains admin-only.
- Admin graphs/forecasts use shared order records. The server recalculates prices, discounts, tax, delivery and rewards.
- Profile edits, promotions, support tickets and escalation statuses persist in SQLite.
- Automated support replies and payments remain explicitly simulated.
- Authentication reuses the team’s cookie sessions, CSRF protection and password hashing.

Use **Refresh records** in staff screens to see other browsers’ changes. Navigation also reloads server records. Automatic push updates are not implemented.

## Prices and portions

| Size | Diameter | Base | Each topping | Sauce and cheese, each | Drink |
|---|---|---:|---:|---|---:|
| Small | 8 inches | $5.00 | $1.00 | ¼ cup | $1.00 |
| Medium | 12 inches | $7.00 | $2.00 | ½ cup | $2.00 |
| Large | 14 inches | $9.00 | $3.00 | 1 cup | $3.00 |

Marinara/cheese are included. Extra cheese consumes an additional topping portion. Other toppings use configurable ⅛/¼/½-cup demo portions. Money uses integer cents in JavaScript and decimal half-up rounding in Python. Demo tax is 8.25%, delivery $3.00, and points equal final dollars rounded down. WELCOME5 gives $5 off a $20 subtotal; REWARD5 costs 100 points for $5 off. One offer per order.

The team's inventory has one decimal place, which cannot directly represent ⅛ cup. Its rows store **eighth-cup units**, while the UI shows cups: 1 cup = 8.0 units, ⅛ cup = 1.0 unit. Do not treat the older kg/liter seed data as cup recipes; the integration initializes a compatible fresh fixture.

## Organization

```text
backend/api/main.py, auth.py   Team API and cookie authentication
backend/models.py             Team SQLAlchemy models
backend/database.py           Team database setup
backend/seed.py, migrate_*.py  Original team tools, not integration initialization
backend/README.md             Original team documentation
backend/integration.py        Field/ID adapter and transactional commands
backend/integrated_app.py     Single-origin UI plus /api
backend/frontend-fixture.json Versioned rules and fictional initial data
backend/requirements-lock.txt Exact verified Python dependency versions
js/services/apiClient.js      API transport, sessions, CSRF and refresh
js/services/*                Integrated/standalone service implementations
js/components/*              Customer and staff screens
css/, assets/, index.html     Existing responsive visual design
scripts/start-integrated.py   Direct Python startup
scripts/start.js              Node startup convenience
scripts/server.js             Original standalone browser-only server
tests/, backend/test_*.py     Frontend and backend checks
database/                    Original normalized SQL analysis design
docs/backlog.md               Scrum user stories and acceptance criteria
```

The adapter maps UI IDs (`LP-1057`, `c1`, `e2`) to numeric team primary keys and maps `order_time`, `user_id`, order junction tables and snake_case statuses to our screen vocabulary. See [integration notes](docs/integration.md).

## Tests

```powershell
node --test tests/*.test.js
.\.venv\Scripts\python.exe -m pytest backend -q
.\.venv\Scripts\python.exe scripts/check_database.py
```

With the integrated server running:

```powershell
$env:PREVIEW_URL = 'http://127.0.0.1:5174'
node scripts/check_server.js
```

Python tests use temporary databases, not the running demo database. They cover the original API plus integrated permissions, checkout totals, retry safety, same-size custom pizzas, rollback, unit conversion, status persistence, shift verification, tickets, profiles and registration. Frontend tests cover pricing, portions, screens, escaping, graphs and role policies. Browser results are recorded in [the testing checklist](docs/testing-checklist.md).

## Standalone mode and reference SQL

`node scripts/server.js` or `npm run start:standalone` serves the original localStorage presentation at port 5173. It does **not** connect to Python. Use port 5174 to demonstrate backend persistence.

`database/schema.sql` and `seed.sql` retain the separate 30-table normalized analysis design. They are **not** the active integrated schema. Runtime uses the team's models plus an additive `ui_workspace` table for features absent from their schema. Future work should normalize that document into dedicated branch/shift/reward/promotion/support tables. Never load the reference SQL into the team database or apply legacy migrations blindly.

## Accessibility and limits

Semantic landmarks, labels, focus handling, native dialogs, validation summaries, chart data tables, live messages, reduced motion and responsive layouts are retained. WCAG 2.2 AA is a target requiring a full audit, not a certification.

Payments, delivery services, notifications, AI responses, estimates and forecasts remain demonstrations. The database and authentication are real local implementations. Public hosting needs HTTPS/secure cookies, private credentials, rate limits, monitoring, backups, capacity tests and review. The extension uses a serialized SQLite JSON workspace, suitable for this class demo rather than high-volume production. API response pagination and normalized extension storage remain future work.

Legacy API write routes are disabled in the integrated mount to prevent bypassing stock/reward/metadata transactions. Their standalone API and tests remain available. Menu management needs a versioned catalog endpoint rather than direct edits underneath the adapter.

See [requirements](docs/requirements.md), [database analysis](docs/database-design.md), [QA checklist](docs/testing-checklist.md), and [the Scrum backlog](docs/backlog.md). The backlog groups ordering, stock, staff operations and reporting into reviewable user stories with acceptance criteria.

## Asset credit

Featured pizzas use distinct real photographs matching plain cheese, pepperoni, and mushroom/green-pepper/onion pizzas. See [photo credits and source details](assets/photo-credits.md). The original hero is by [manoo manoo on Unsplash](https://unsplash.com/photos/iPh0NDrYpzI). Manrope and DM Sans via Google Fonts with system fallbacks. Favicon is a project-authored letter mark.
