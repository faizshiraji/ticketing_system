# CCL/CCDL support ticketing system

Django + Django REST Framework + PostgreSQL backend, with a Vue 3 SPA in
`frontend/`. No Odoo integration, no Celery/Redis in this phase —
notifications are sent synchronously and SLA breach checks run via a
scheduled management command.

## Project layout

```
config/            Project settings, root urls, wsgi
apps/
  accounts/        Custom User (role: customer/agent/supervisor/admin), Company
  tickets/         Category, Priority, SLAPolicy, Ticket, comments, attachments,
                   activity log, signals (auto SLA + notifications), the
                   SLA-breach cron command
  notifications/   Synchronous email/SMS-stub sending, one function per event
  analytics/       Backoffice dashboard aggregation endpoint
frontend/          Vue 3 + Vite SPA (customer + agent portals)
```

## Setup (backend)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in DB + email credentials; include Vite CORS origins

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo   # CCL/CCDL companies, ERP categories, test users
python manage.py runserver
```

API: http://127.0.0.1:8000/

## Setup (frontend)

In a second terminal:

```bash
cd frontend
cp .env.example .env   # VITE_API_BASE_URL=http://127.0.0.1:8000
npm install
npm run dev
```

UI: http://127.0.0.1:5173/

Ensure `.env` has:

```
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

Restart Django after changing CORS. Sign in with seeded users (below).
Customers land on My tickets; agents on the queue; supervisors/admins on the Vue **Admin** home (`/admin`).

## Demo data

```bash
python manage.py seed_demo
```

Seeds CCL/CCDL companies, ERP + mobile-app support categories, priorities/SLA,
and test users. Safe to re-run. Shared password for seeded users: `Test@123`.

| Username | Email | Role |
|----------|-------|------|
| `ccl.user` | `user@ccl.example.com` | customer (CCL) |
| `ccdl.user` | `user@ccdl.example.com` | customer (CCDL) |
| `agent1` | `agent1@support.example.com` | agent |
| `agent2` | `agent2@support.example.com` | agent |
| `supervisor` | `supervisor@support.example.com` | supervisor |
| `admin` | `admin@support.example.com` | admin (Vue Admin + Django admin) |

Supervisors land on `/admin` (can manage companies/categories/priorities; list users).
Admins can also create/edit users. Password for all seeded users: `Test@123`.

## Scheduling the SLA check

No Celery/Redis needed at current volumes. Add to cron:

```
*/5 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py check_sla_breaches
```

## API surface

- `POST /api/auth/token/` — obtain JWT (username/password)
- `GET /api/accounts/me/` — current user profile
- `GET|POST /api/accounts/companies/` — staff list; supervisor/admin write
- `GET|POST /api/accounts/users/` — supervisor/admin list; **admin-only** write
- `GET|POST /api/tickets/` — list (role-scoped) / create a ticket
- `GET|PATCH /api/tickets/{id}/` — ticket detail; only staff can PATCH status/assignment
- `GET|POST /api/tickets/{ticket_id}/comments/` — thread replies (internal notes staff-only)
- `GET|POST /api/tickets/categories/`, `GET|POST /api/tickets/priorities/` — write: supervisor/admin
- `GET|POST /api/tickets/support-layers/` — support tiers + agent membership; write: supervisor/admin
- `POST /api/tickets/{id}/escalate/` — staff escalate to next layer or specific agent (reason required)
- `POST /api/tickets/{id}/attachments/` — upload an image (jpg/png/gif/webp, max 5 MB)
- `POST /api/tickets/{id}/comments/` — JSON or multipart with `files` for comment images
- `GET /api/accounts/agents/` — staff list for escalation pickers
- `GET /api/analytics/dashboard-summary/` — staff ops dashboard
- `GET /api/analytics/reports/?company=&days=` — staff trends + SLA breach list

Uploaded images are stored under `media/` and served at `/media/` in DEBUG. The Vue
dev server proxies `/media` to Django.
## Vue portals

| Role | Home | Notes |
|------|------|-------|
| customer | `/tickets` | Create/view/reply |
| agent | `/agent/queue` | Queue + ops dashboard + escalate |
| supervisor / admin | `/admin` | Hub: support layers, management CRUD, analytics, queue |

### Support layers & escalation

Admins/supervisors configure **Support layers** (e.g. L1/L2/L3) and assign agents under `/admin/support-layers`.
New tickets start on the lowest active layer. Agents escalate from ticket detail:

- **Next layer** — moves ticket up one level and unassigns (queues at next tier)
- **Specific agent** — assigns that agent and sets layer to their highest membership

Each move is stored in **movement history** with a required reason (also as an internal comment).

Django admin remains at `http://127.0.0.1:8000/admin/` for edge cases.
## Design notes

- **Role-based access, one User model.** `role` on the custom user drives
  querset scoping in views rather than separate customer/staff models —
  keeps auth and the ticket FK simple.
- **`TicketActivityLog` is the audit trail.** Every status transition is
  recorded via a `pre_save`/`post_save` signal pair on `Ticket`, and this
  table is what the analytics endpoint reads for resolution-time and
  breach reporting — never the mutable `Ticket` row alone.
- **SLA due-at is computed once, at creation**, from `SLAPolicy` (falls
  back to `settings.DEFAULT_*_MINUTES` if no policy matches). Breach
  status (`Ticket.is_sla_breached`) is a live property, not a stored flag.
- **Internal notes vs public replies** are the same `TicketComment` model
  with an `is_internal` flag, filtered out for customers at the
  serializer/queryset level — never trust the client to hide them.
- **Growth path:** if notification volume or SLA-check frequency ever
  strains synchronous sends, that's the signal to introduce Celery/Redis —
  the `apps.notifications.services` functions are already isolated behind
  a single call site (`tickets/signals.py`), so swapping them for
  `.delay()` calls later is a small, contained change.
