# Spec: Date Filter for Profile Page

## Overview
Step 6 adds a date-range filter to the profile page so users can slice their
spending data by time period. Currently all three data sections — summary stats,
transaction history, and category breakdown — always show all-time totals. This
step adds a filter bar with preset period buttons (This Month, Last 3 Months,
This Year, All Time) and a custom date range picker. Selecting any filter
re-fetches the same `/profile` route with query parameters, and all three
sections update to reflect only the expenses in the chosen window.

## Depends on
- Step 1: Database setup (`expenses` table with `date` column exists)
- Step 2: Registration (users in the database)
- Step 3: Login / Logout (`session["user_id"]` set on login)
- Step 4: Profile page static UI (template structure with stats, transactions, categories)
- Step 5: Backend routes for profile page (`get_summary_stats`, `get_recent_transactions`, `get_category_breakdown` exist in `database/queries.py`)

## Routes
No new routes. The existing `GET /profile` route is modified to accept optional
query parameters:
- `?period=this_month` — current calendar month
- `?period=last_3_months` — the past 90 days
- `?period=this_year` — current calendar year
- `?period=all` — no date restriction (default when no params present)
- `?from=YYYY-MM-DD&to=YYYY-MM-DD` — custom date range

If both `period` and `from`/`to` are present, `from`/`to` takes precedence.
Invalid or malformed date strings are silently ignored (fall back to `all`).

## Database changes
No database changes.

## Templates
- **Modify**: `templates/profile.html`
  - Add a filter bar between the profile hero and the stats grid.
  - Filter bar contains four preset buttons: "This Month", "Last 3 Months",
    "This Year", "All Time".
  - Filter bar also contains two `<input type="date">` fields (From / To) and
    an "Apply" button for the custom range.
  - The active preset button receives an `active` CSS class so it appears
    highlighted.
  - A one-line summary label ("Showing: May 2026" / "Showing: Last 3 months" /
    "Showing: all time") appears below the filter bar and above the stats grid.
  - No structural changes to the stats grid, transaction table, or category
    breakdown — they already consume Jinja variables; only those variables
    change.

## Files to change
- `app.py` — update `profile()` to read `period`, `from`, `to` query params;
  compute `date_from` / `date_to` bounds; pass them to all three query helpers;
  pass `active_period`, `date_from`, `date_to`, and `period_label` to the
  template.
- `database/queries.py` — add optional `date_from` and `date_to` parameters to
  `get_summary_stats`, `get_recent_transactions`, and `get_category_breakdown`.
  When both are `None` the queries behave identically to today.
- `templates/profile.html` — add filter bar UI and period label (see Templates
  section above).

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles except for CSS custom property overrides (`--bar-pct`)
- Currency must always display as ₹ — never £ or $
- Date bounds are computed in `app.py` using Python's `datetime` / `date`
  stdlib — no third-party date libraries
- `date_from` and `date_to` passed to queries must be ISO strings
  (`YYYY-MM-DD`) or `None`; never `datetime` objects
- The "All Time" preset (and the default with no query params) passes
  `date_from=None, date_to=None`, which means no `WHERE date BETWEEN` clause
  is added — do not pass open-ended sentinel dates like `0001-01-01`
- If `date_from > date_to` (reversed custom range), swap them silently before
  querying
- The `period_label` shown in the summary line must be human-readable:
  - `this_month` → "May 2026" (current month name + year)
  - `last_3_months` → "Last 3 months"
  - `this_year` → "2026"
  - `all` → "All time"
  - custom range → "1 May 2026 – 31 May 2026"
- Preset buttons submit via plain HTML `<a href="...">` links (no JS required)
- The custom date range form uses `method="get"` pointing to `/profile`

## Definition of done
- [ ] Visiting `/profile` with no query params shows all-time data (same as before this step)
- [ ] Clicking "This Month" shows only expenses in the current calendar month; the stats, transaction list, and category breakdown all reflect the filtered window
- [ ] Clicking "Last 3 Months" shows only expenses from the past 90 days
- [ ] Clicking "This Year" shows only expenses from the current calendar year
- [ ] Clicking "All Time" reverts to showing all expenses
- [ ] The active preset button is visually highlighted (distinct from inactive buttons)
- [ ] The period label below the filter bar accurately describes the active window
- [ ] Entering a valid custom From / To date and clicking Apply filters all three sections to that range
- [ ] When a date range contains no expenses, stats show ₹0 / 0 transactions / "—" top category, the transaction table is empty, and the category breakdown is empty — no errors
- [ ] Visiting `/profile?from=2026-05-01&to=2026-05-31` directly shows only May 2026 data
