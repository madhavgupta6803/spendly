# Spec: Edit Expense

## Overview
This feature lets a logged-in user edit an existing expense. The `/expenses/<id>/edit` stub route is replaced with a real GET/POST handler: GET loads the expense (verifying ownership), pre-fills the form, and renders it; POST validates the updated fields and issues an `UPDATE` query, then redirects back to the profile page. The profile page transaction list also gains per-row Edit links so the user can reach the form naturally.

## Depends on
- Step 01 — Database Setup (expenses table must exist)
- Step 03 — Login and Logout (session-based auth)
- Step 04 — Profile Page (redirect destination and transaction list)
- Step 07 — Add Expense (establishes the add-expense form pattern this feature mirrors)

## Routes
- `GET /expenses/<int:id>/edit` — render the edit form pre-filled with the expense's current values — logged-in only
- `POST /expenses/<int:id>/edit` — validate updated fields and UPDATE the row, redirect to `/profile` — logged-in only

## Database changes
No new tables or columns. The existing `expenses` schema is sufficient.

## Templates
- **Create:** `templates/edit_expense.html` — pre-filled form with amount, category (select), date, description fields. Mirrors the layout of `add_expense.html`. Extends `base.html`. Shows inline validation errors on re-render.
- **Modify:** `templates/profile.html` — add an Edit link/button to each row in the transactions table that points to `url_for('edit_expense', id=tx.id)`. Requires `id` to be present on each transaction dict (see queries change below).

## Files to change
- `app.py` — replace the GET-only `edit_expense` stub with a GET/POST handler; enforce ownership check (expense must belong to `session["user_id"]`); reuse the same `CATEGORIES` list for validation
- `database/queries.py` — add `get_expense_by_id(expense_id, user_id)` (returns the row or `None` if not found or not owned); add `update_expense(expense_id, user_id, amount, category, expense_date, description)`; modify `get_recent_transactions` to include `id` in each returned dict

## Files to create
- `templates/edit_expense.html` — edit form template

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (not relevant here, but maintain the pattern)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Redirect unauthenticated users to `/login`
- Ownership check: if the expense `id` does not exist **or** belongs to a different user, return `abort(404)`
- Amount must be a positive number; reject zero or negative values
- Category must be one of the allowed `CATEGORIES` values
- Date must be a valid ISO date (YYYY-MM-DD)
- Description is optional (max 200 characters if provided)
- On validation failure, re-render the form with the error message and the submitted (not original) values pre-filled
- On success, redirect to `url_for('profile')` with HTTP 302
- Currency always displayed as ₹ (Indian Rupees) — never use $
- The `update_expense` query must include `user_id` in the `WHERE` clause as a second ownership guard

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for an expense owned by the current user renders a form pre-filled with that expense's amount, category, date, and description
- [ ] Visiting `/expenses/<id>/edit` for a non-existent `id` or an `id` owned by another user returns a 404
- [ ] Submitting valid updated values updates the row in `expenses` and redirects to `/profile`
- [ ] The updated values appear correctly in the profile transactions list after redirect
- [ ] Submitting with a missing or zero amount shows an inline error and re-fills the submitted values
- [ ] Submitting with an invalid category shows an inline error
- [ ] Submitting with an invalid date shows an inline error
- [ ] Each transaction row on the profile page shows an Edit link pointing to the correct `/expenses/<id>/edit` URL
- [ ] All form styling uses CSS variables (no hardcoded hex colours)
