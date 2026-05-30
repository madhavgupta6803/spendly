# Spec: Login and Logout

## Overview
Wire up session-based login and logout so users can authenticate and maintain a persistent session across requests. The `GET /login` route and `login.html` template already exist; this step adds the `POST /login` handler that verifies credentials with `check_password_hash`, writes a session cookie on success, and redirects to the landing page. The `GET /logout` route is promoted from its placeholder to a real handler that clears the session and redirects to landing. Both `/login` and `/register` redirect already-logged-in users to `/`. The navbar in `base.html` is updated to show a context-sensitive logged-in state (user name + Sign out link) versus the existing guest state (Sign in + Get started). This step establishes the Flask `session` pattern that all subsequent protected routes will rely on.

## Depends on
- Step 01 — Database Setup (`get_db()` and `users` table must exist)
- Step 02 — Registration (at least one user row must exist to test login)

## Routes
- `GET /login` — render login form; redirect to `/` if already logged in — public
- `POST /login` — verify credentials, start session, redirect to `/` — public
- `GET /logout` — clear session, redirect to `/` — logged-in (currently a placeholder)
- `GET /register` — redirect to `/` if already logged in (existing route, guarded)

## Database changes
No database changes. The `users` table from Step 01 is sufficient.

## Templates
- **Modify:** `templates/login.html`
  - Preserve `email` field value on validation failure (add `value="{{ email or '' }}"` to the email input)
- **Modify:** `templates/base.html`
  - Replace the static nav-links block with a conditional: if `session.user_id` is set show the user's name and a "Sign out" link; otherwise show the existing "Sign in" / "Get started" links

## Files to change
- `app.py`
  - Add `session` to the Flask import
  - Add `check_password_hash` to the werkzeug import
  - Convert `GET /login` to also accept `POST`; implement POST handler; guard with session redirect
  - Guard `GET /register` with session redirect to `/`
  - Implement `GET /logout` (remove placeholder string)
- `templates/login.html` — bind `value` on email input so field is pre-filled on error
- `templates/base.html` — add session-aware nav conditional

## Files to create
None.

## New dependencies
No new dependencies. `flask.session` and `werkzeug.security.check_password_hash` are already available.

## Rules for implementation
- No SQLAlchemy or ORMs — use `sqlite3` via `get_db()` directly
- Parameterised queries only — never use string formatting or f-strings in SQL
- Passwords verified with `werkzeug.security.check_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `session` stores only `user_id` (integer) and `user_name` (string) — nothing else
- Login validation order:
  1. Both fields non-empty after `.strip()`
  2. Email exists in `users` table (single `SELECT` by email)
  3. `check_password_hash` passes — if either check 2 or 3 fails, show the same generic error `"Invalid email or password."` (do not reveal which field is wrong)
- On success: set `session['user_id']` and `session['user_name']`, then `redirect(url_for('landing'))`
- `GET /login` or `GET /register` when already logged in (`session.get('user_id')`): redirect to `url_for('landing')`
- `GET /logout`: call `session.clear()`, then `redirect(url_for('landing'))`
- In `base.html`, check `session.get('user_id')` (not `session['user_id']`) to avoid KeyError

## Definition of done
- [ ] `GET /login` renders the form for unauthenticated visitors
- [ ] `GET /login` redirects to `/` when already logged in
- [ ] `GET /register` redirects to `/` when already logged in
- [ ] Submitting the login form with any empty field shows an inline error
- [ ] Submitting a non-existent email shows `"Invalid email or password."`
- [ ] Submitting a wrong password shows `"Invalid email or password."` (same message — no hint which field failed)
- [ ] Submitting valid credentials sets the session and redirects to `/`
- [ ] The email field is pre-filled when the form is re-rendered after an error
- [ ] `GET /logout` clears the session and redirects to `/`
- [ ] The navbar shows "Sign in" / "Get started" for guests and the user's name + "Sign out" for logged-in users
- [ ] App starts without errors after all changes to `app.py`
