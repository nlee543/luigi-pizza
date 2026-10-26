# Luigi’s Pizzeria — integrated team application

This branch connects our HTML, CSS, and vanilla JavaScript website to the team’s **FastAPI, SQLAlchemy, and SQLite backend**. Customers can place orders, and staff can manage them through the same saved database. The original ZIP files and local backups are not included in this repository.

The team’s backend files are in `backend/`. The integration added an API client to the website, a Python adapter for the website’s fields, and storage for features such as shifts and rewards. The team’s original documentation remains in `backend/README.md`; use this README to run the combined application.

## Live website

The class demo is hosted at **[pizzabyluigi.duckdns.org](https://pizzabyluigi.duckdns.org/)**. You can use that link without installing anything on your computer. It is a demonstration site with fictional data; payments and automated support replies are simulated.

The hosted copy runs on a Google Cloud Compute Engine VM using Debian 13. DuckDNS points the domain to the VM's external IP. Nginx accepts HTTPS requests and forwards them to the Python application on `127.0.0.1:5174`. Certbot manages the HTTPS certificate, and a systemd service named `luigi-pizza` starts the app when the VM boots and keeps it running after SSH is closed.

The VM stores its SQLite database at `backend/luigi_pizza.db` inside the deployed project. That database is separate from databases created on our own computers. Orders, accounts, inventory, and shifts entered on the hosted site stay with the hosted copy; they are not synced through GitHub. Stopping the VM takes the site offline but does not erase its persistent disk. If its external IP changes, the DuckDNS record must be updated.

Pushing a commit to GitHub does **not** automatically update the hosted site. Deployment is manual: update the VM's project copy, preserve its database and hosting settings, install changed dependencies if needed, and restart the service. The VM's Nginx, Certbot, and systemd configurations are managed on the VM and are not included in this repository.

### Hosted configuration and local defaults

The hosted service uses `APP_ORIGIN=https://pizzabyluigi.duckdns.org`. Secure cookies were enabled in the VM's copy of `backend/integrated_app.py` by setting `cookie_secure=True`. The repository retains `cookie_secure=False` for local HTTP development. These VM-specific settings must be preserved when deploying updates; downloading this branch alone does not reproduce the HTTPS setup.

To check or restart the existing deployment from the VM's SSH terminal:

```bash
sudo systemctl status luigi-pizza --no-pager
sudo journalctl -u luigi-pizza -n 40 --no-pager
sudo systemctl restart luigi-pizza
```

The first two commands show service status and recent logs. The third restarts the application and briefly interrupts requests. HTTPS is one part of the hosting setup; this remains a class demo rather than a production restaurant service.

## Run the integrated application locally

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

First startup creates `backend/luigi_pizza.db` with fictional data. Later restarts preserve orders, stock, rewards, profiles, shifts, verification, promotions and tickets. No real data has been imported. Legacy browser-only orders remain in the standalone demo and are not silently imported. The launcher listens only on loopback and uses local HTTP by default. On the hosted VM, Nginx provides public HTTPS access to that local application, as described above.

## Demonstration logins

These are intentionally public **seeded demo credentials**, not production secrets. They apply to a newly initialized demo database; account changes in the hosted database do not update this table. Passwords are stored as Argon2 hashes in the database.

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
backend/README.md             Original team documentation, retained for reference
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
docs/runtime-database.md      Current database diagram and integration storage
```

The adapter maps UI IDs (`LP-1057`, `c1`, `e2`) to numeric team primary keys and maps `order_time`, `user_id`, order junction tables and snake_case statuses to our screen vocabulary. See [integration notes](docs/integration.md).

## Current database design

The [current database diagram](docs/runtime-database.md) shows the tables used by this branch, including the added `ui_workspace` table. It follows `backend/models.py` and the workspace model in `backend/integration.py`.

The integration removed the unique order/pizza pair constraint so an order can contain two pizzas of the same size with different toppings. Drink selections and topping selections still have their original pair constraints. Branches, shifts, rewards, promotions, and support records are stored in the workspace document and linked to the team’s records through application-managed IDs.

The diagram in the team’s original `backend/README.md` remains historical reference. Its statement that an order/pizza pair must be unique does not apply to this branch. The separate [30-table SQL design](docs/database-design.md) is an analysis document, not the schema used by the running application.

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

`database/schema.sql` and `database/seed.sql` retain the separate 30-table normalized analysis design. They are **not** the active integrated schema. Runtime uses the team's models plus an added `ui_workspace` table for features absent from their schema. Future work should move the workspace records into dedicated branch, shift, reward, promotion, and support tables. Do not load the reference SQL into the integrated database or run older migrations without checking compatibility.

## Accessibility and limits

Semantic landmarks, labels, focus handling, native dialogs, validation summaries, chart data tables, live messages, reduced motion and responsive layouts are retained. WCAG 2.2 AA is a target requiring a full audit, not a certification.

Payments, delivery services, notifications, AI responses, estimates and forecasts remain demonstrations. The database and authentication run on the server. The hosted class demo uses HTTPS; production use would also require private credentials, rate limits, monitoring, verified backups, capacity tests and further review. The extension uses a serialized SQLite JSON workspace, suitable for this class demo rather than high-volume production. API response pagination and normalized extension storage remain future work.

Legacy API write routes are disabled in the integrated mount to prevent bypassing stock/reward/metadata transactions. Their standalone API and tests remain available. Menu management needs a versioned catalog endpoint rather than direct edits underneath the adapter.

See [requirements](docs/requirements.md), [database analysis](docs/database-design.md), [QA checklist](docs/testing-checklist.md), and [the Scrum backlog](docs/backlog.md). The backlog groups ordering, stock, staff operations and reporting into reviewable user stories with acceptance criteria.

## Asset credit

Featured pizzas use distinct real photographs matching plain cheese, pepperoni, and mushroom/green-pepper/onion pizzas. See [photo credits and source details](assets/photo-credits.md). The original hero is by [manoo manoo on Unsplash](https://unsplash.com/photos/iPh0NDrYpzI). Manrope and DM Sans via Google Fonts with system fallbacks. Favicon is a project-authored letter mark.
