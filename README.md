# Spendly

A personal expense tracker web app built with Flask and SQLite. Track spending by category, filter by date range, and manage individual expenses — all in Indian Rupees (₹).

**Live demo:** https://expense-tracker-production-fc8f.up.railway.app
Login: `demo@spendly.com` / `demo123`

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask 3.1 |
| Database | SQLite (via `sqlite3` stdlib) |
| Templates | Jinja2 |
| Auth | Session-based (Werkzeug password hashing) |
| Styling | Custom CSS with CSS variables |
| Testing | pytest, pytest-flask |
| Deployment | Railway |

---

## Features

- Register and log in with a personal account
- Add, edit, and delete expenses
- Categorise spending: Food, Travel, Bills, Entertainment, Health, Shopping, Other
- Filter transactions by preset periods (this month, last 3 months, this year) or a custom date range
- Dashboard showing total spend, transaction count, top category, and a per-category breakdown
- CSRF protection on all state-changing forms

---

## Installation

### Prerequisites

- Python 3.10+
- `pip`

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/madhavgupta6803/spendly.git
cd spendly

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
python app.py
```

The app starts at **http://localhost:5001**.

On first run, the database is created automatically and seeded with a demo user and sample expenses.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-change-in-prod` | Flask session signing key — **set this in production** |
| `PORT` | `5001` | Server port |
| `FLASK_DEBUG` | `0` | Set to `1` to enable debug mode |

---

## Usage

### Demo account

| Field | Value |
|---|---|
| Email | `demo@spendly.com` |
| Password | `demo123` |

### Adding an expense

1. Log in and go to your profile page
2. Click **+ Add Expense**
3. Enter amount (₹), category, date, and an optional description
4. Submit — the expense appears immediately in your transaction list

### Editing an expense

Click **Edit** on any transaction row, update the fields, and submit.

### Deleting an expense

Click **Delete** on any transaction row and confirm the dialog. The row is removed immediately.

### Filtering by date

Use the period buttons (**This month**, **Last 3 months**, **This year**) or enter a custom **From / To** date range at the top of your profile page. Stats and the transaction list update to reflect the selected period.

---

## Project structure

```
spendly/
├── app.py                  # All Flask routes
├── Procfile                # Railway/Heroku start command
├── requirements.txt        # Python dependencies
│
├── database/
│   ├── db.py               # get_db(), init_db(), seed_db()
│   └── queries.py          # All SQL query functions
│
├── templates/              # Jinja2 templates (all extend base.html)
│   ├── base.html           # Layout with navbar and footer
│   ├── landing.html        # Public landing page
│   ├── login.html          # Login form
│   ├── register.html       # Registration form
│   ├── profile.html        # Dashboard + transaction list
│   ├── add_expense.html    # Add expense form
│   ├── edit_expense.html   # Edit expense form
│   ├── analytics.html      # Analytics page (stub)
│   ├── terms.html          # Terms of service
│   └── privacy.html        # Privacy policy
│
├── static/
│   ├── css/
│   │   ├── style.css       # Global styles and component classes
│   │   └── landing.css     # Landing page only
│   └── js/
│       └── main.js         # Global JS
│
└── tests/
    ├── conftest.py          # Shared fixtures (app, client)
    ├── test_backend_connection.py
    ├── test_date_filter.py
    ├── test_07-add-expense.py
    └── test_09-delete-expense.py
```

### Database schema

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    description TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);
```

---

## Running tests

```bash
# All tests
pytest

# Single file
pytest tests/test_09-delete-expense.py

# Single test
pytest tests/test_09-delete-expense.py::TestHappyPath::test_post_own_expense_redirects_to_profile

# With output
pytest -v
```

Tests use an isolated in-memory SQLite database — no seed data is injected automatically; each test sets up exactly what it needs.

---

## Contributing

1. **Fork** the repository and create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow the conventions:**
   - No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
   - Parameterised queries only — never string-format SQL
   - Passwords hashed with `werkzeug.security`
   - CSS variables only — never hardcode hex values
   - All templates must extend `base.html`
   - Currency displayed as ₹ (Indian Rupees) — never `$`

3. **Write tests** for any new routes or query functions. Tests live in `tests/` and follow the fixture pattern in `conftest.py`.

4. **Run the full test suite** before opening a PR:
   ```bash
   pytest
   ```

5. **Open a pull request** against `main` with a clear description of what changed and why.

---

## Deployment

The app is configured to deploy to [Railway](https://railway.com) via `Procfile`. To deploy your own instance:

```bash
npm i -g @railway/cli   # install Railway CLI
railway login
railway up
railway domain          # generate a public URL
```

Set `SECRET_KEY` to a random value in Railway's environment variables before going live.
