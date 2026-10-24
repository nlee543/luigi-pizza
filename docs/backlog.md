# Scrum backlog

User stories and acceptance criteria for the Mini Case. This is planning documentation; current implementation details are in the root README and integration notes.

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
| Future | As an owner, I want production-ready multi-branch operations. | Normalize extension records, add payment integration, monitoring, capacity tests and production access controls. |

Suggested sprints: (1) menu/builder/pricing/cart; (2) checkout/orders/inventory; (3) staff/analytics/rewards/support; (4) database/docs/accessibility and real-backend planning. Definition of done: feature works, business checks pass, QA checklist is recorded, docs agree, and mock boundaries are explicit.
