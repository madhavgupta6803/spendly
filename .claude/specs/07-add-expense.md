# Spec: Add Expense

## Overview
This feature implements the "Add Expense" form that lets a logged-in user record a new expense. It converts the existing `/expenses/add` stub route into a real GET/POST handler: GET renders the form, POST validates the input and inserts a row into the `expenses` table, then redirects back to the profile page. This is the first user-facing write path for expense data in Spendly.

## Depends on
- Step 01 — Database Setup (expenses table must exist)
- Step 03 — Login and Logout (session-based auth)
- Step 04 — Profile Page (redirect destination after save)

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in only
- `POST /expenses/add` — validate and insert expense, redirect to `/profile` — logged-in only

## Database changes
No database changes. The `expenses` table already exists:
```sql
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    description TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);
```

## Templates
- **Create:** `templates/add_expense.html` — form with fields: amount, category (select), date, description (optional). Extends `base.html`. Shows inline validation errors on re-render. Pre-fills previously entered values on error.
- **Modify:** `templates/profile.html` — confirm the "Add expense" button/link points to `url_for('add_expense')` (no structural change needed if already wired).

## Files to change
- `app.py` — replace the GET-only `add_expense` stub with a GET/POST handler that validates input and inserts into `expenses`

## Files to create
- `templates/add_expense.html` — the add-expense form template

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (not relevant here, but maintain the pattern)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Redirect unauthenticated users to `/login`
- Amount must be a positive number; reject zero or negative values
- Category must be one of the allowed values: Food, Travel, Bills, Entertainment, Health, Other
- Date must be a valid ISO date (YYYY-MM-DD); default the date field to today's date
- Description is optional (max 200 characters if provided)
- On validation failure, re-render the form with the error message and all previously entered values pre-filled
- On success, redirect to `url_for('profile')` with an HTTP 302
- Currency is always displayed as ₹ (Indian Rupees) — never use $

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in renders a form with amount, category, date, and description fields
- [ ] The date field defaults to today's date on first load
- [ ] The category field is a `<select>` with options: Food, Travel, Bills, Entertainment, Health, Other
- [ ] Submitting the form with all valid fields inserts a row in `expenses` and redirects to `/profile`
- [ ] The new expense appears in the transactions list on the profile page immediately after redirect
- [ ] Submitting with a missing or zero amount shows an inline error and pre-fills the other fields
- [ ] Submitting with an invalid or missing category shows an inline error
- [ ] Submitting with an invalid date shows an inline error
- [ ] All form styling uses CSS variables (no hardcoded hex colours)
