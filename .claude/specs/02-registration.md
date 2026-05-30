# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account. The existing `GET /register` route and `register.html` template are already scaffolded; this step wires up the `POST /register` handler that validates input, hashes the password, and inserts the new user into the database. On success the user is shown a success message & redirected to the login page; on failure the form is re-rendered with a clear inline error message. This is the first step that writes real data, so it establishes the pattern (parameterised queries, werkzeug hashing) all subsequent write routes will follow.

## Depends on
- Step 01 — Database Setup (users table must exist; `get_db()` must be implemented)

## Routes
- `GET /register` — render empty registration form — public (already exists, no change needed)
- `POST /register` — process registration form — public

## Database changes
No database changes. The `users` table created in Step 01 is sufficient.

## Templates
- **Modify:** `templates/register.html`
  - Preserve `name` and `email` field values on validation failure (add `value="{{ name }}"` / `value="{{ email }}"` to inputs)
  - No structural changes needed; `{% if error %}` block is already present

## Files to change
- `app.py` — add `request`, `redirect`, `url_for` to Flask import; add `app.secret_key`; convert `/register` to accept `GET` and `POST`; implement POST handler
- `templates/register.html` — bind `value` attributes so the form doesn't blank on error

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security` is already installed.

## Rules for implementation
- No SQLAlchemy or ORMs — use `sqlite3` via `get_db()` directly
- Parameterised queries only — never use string formatting or f-strings in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Set `app.secret_key` to a hard-coded dev string (e.g. `"dev-secret-change-in-prod"`) — a comment noting it must be replaced in production is acceptable here
- Validation must check (in this order):
  1. All three fields are non-empty after `.strip()`
  2. Password is at least 8 characters
  3. Email is not already registered (query the DB; catch the case, not the exception)
- On duplicate email: re-render the form with error `"An account with that email already exists."`
- On success: redirect to `url_for('login')` — do **not** log the user in (session handling is Step 03)
- Pass `name` and `email` back to the template on any validation error so fields are pre-filled

## Definition of done
- [ ] `GET /register` still renders the form without errors
- [ ] Submitting with any empty field shows an inline error and keeps other field values
- [ ] Submitting a password shorter than 8 characters shows an inline error
- [ ] Submitting a duplicate email shows `"An account with that email already exists."`
- [ ] Submitting valid unique data inserts a row into `users` with a hashed (not plaintext) password
- [ ] After successful registration the browser is redirected to `/login`
- [ ] The database enforces the UNIQUE constraint on email (independent of app-level check)
- [ ] App starts without errors after changes to `app.py`
