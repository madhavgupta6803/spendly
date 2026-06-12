# Spec: Delete Expense

## Overview
This feature lets a logged-in user permanently delete one of their own expenses. The existing GET stub at `/expenses/<id>/delete` is replaced with a POST-only handler that verifies ownership and removes the row from the database, then redirects back to the profile page. The profile page transaction list gains a Delete button per row rendered as a small inline `<form>` (POST), preventing accidental deletions via link prefetching or browser history. A `window.confirm` dialog provides a lightweight client-side guard before submission.

## Depends on
- Step 01 — Database Setup (expenses table must exist)
- Step 03 — Login and Logout (session-based auth)
- Step 04 — Profile Page (redirect destination and transaction list)
- Step 08 — Edit Expense (establishes the per-row action button pattern and `get_expense_by_id`)

## Routes
- `POST /expenses/<int:id>/delete` — verify ownership, DELETE the row, redirect to `/profile` — logged-in only

## Database changes
No database changes. The existing `expenses` schema is sufficient.

## Templates
- **Create:** None
- **Modify:** `templates/profile.html` — add a Delete button to each row in the transactions table, rendered as an inline `<form method="POST" action="{{ url_for('delete_expense', id=tx.id) }}">` with a submit button styled as a danger link. Add an `onsubmit="return confirm('Delete this expense?')"` attribute to the form for client-side confirmation.

## Files to change
- `app.py` — replace the GET stub `delete_expense` with a POST-only handler; add `methods=["POST"]`; enforce `session["user_id"]` guard; call `delete_expense` query; redirect to `url_for('profile')` on success
- `database/queries.py` — add `delete_expense(expense_id, user_id)` that runs `DELETE FROM expenses WHERE id = ? AND user_id = ?`
- `templates/profile.html` — add inline delete form per transaction row

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (not relevant here, but maintain the pattern)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Route must be POST only (`methods=["POST"]`) — a GET request to the delete URL must return 405
- Redirect unauthenticated users to `/login`
- Ownership check: use `get_expense_by_id(id, session["user_id"])` first; if `None`, `abort(404)`
- The `DELETE` query must include `user_id` in the `WHERE` clause as a second ownership guard
- On success, redirect to `url_for('profile')` with HTTP 302
- Currency always displayed as ₹ (Indian Rupees) — never use $
- The delete button must be visually distinct (danger/destructive styling) but must not break the row layout used by existing Edit links

## Definition of done
- [ ] Sending a GET request to `/expenses/<id>/delete` returns 405 (Method Not Allowed)
- [ ] POSTing to `/expenses/<id>/delete` while logged out redirects to `/login`
- [ ] POSTing to `/expenses/<id>/delete` for a non-existent `id` or one owned by another user returns 404
- [ ] POSTing to `/expenses/<id>/delete` for the current user's own expense removes the row and redirects to `/profile`
- [ ] The deleted expense no longer appears in the profile transactions list after redirect
- [ ] Each transaction row on the profile page shows a Delete button that triggers a `confirm()` dialog before submitting
- [ ] The Delete button renders inside a `<form method="POST">` pointing to the correct `/expenses/<id>/delete` URL
- [ ] All button styling uses CSS variables (no hardcoded hex colours)
