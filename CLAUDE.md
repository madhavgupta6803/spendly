# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Spendly** — a personal expense tracker web app. Flask backend, SQLite database, Jinja2 templates. Designed as an incremental student project where the scaffold is provided and features are added step-by-step.

## Commands

```bash
# Activate virtual environment (required before running anything)
source venv/bin/activate

# Run dev server (port 5001)
python app.py

# Or via Flask CLI
flask --app app run --debug --port 5001

# Run tests
pytest

# Run a single test file
pytest tests/test_auth.py

# Run a single test
pytest tests/test_auth.py::test_login_success
```

## Architecture

**`app.py`** — single file containing all Flask routes. Currently only landing, register, login, terms, and privacy render real templates; logout/profile/expense CRUD return placeholder strings pending implementation.

**`database/db.py`** — stub for students to implement three functions:
- `get_db()` — returns a SQLite connection with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`
- `init_db()` — creates tables with `CREATE TABLE IF NOT EXISTS`
- `seed_db()` — inserts sample dev data

**`templates/`** — Jinja2 templates using `base.html` as the layout. `base.html` defines blocks: `title`, `head` (extra `<head>` tags), `content`, `scripts` (bottom-of-body JS). All pages extend it.

**`static/css/style.css`** — global styles (navbar, footer, auth forms, shared utilities). **`static/css/landing.css`** — landing page only (hero, features, CTA, video modal). Loaded via `{% block head %}` in the landing template.

**`static/js/main.js`** — global JS. Page-specific JS lives inline in `{% block scripts %}` within the template (see the video modal logic in `landing.html`).

## Planned database schema

The app targets a `users` table (id, email, password_hash, name, created_at) and an `expenses` table (id, user_id FK, amount, category, date, description, created_at). Categories: Food, Travel, Bills, Entertainment, Health, Other.

## Template conventions

- Currency is displayed in Indian Rupees (₹).
- Fonts: DM Serif Display (headings) + DM Sans (body) from Google Fonts, loaded in `base.html`.
- The navbar in `base.html` always shows Sign in / Get started links; it will need a logged-in state once auth is wired up.
