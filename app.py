from datetime import date, timedelta

from flask import Flask, render_template, request, redirect, url_for, session

from database.db import get_db, init_db, seed_db
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-change-in-prod"  # replace before production

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.", name=name, email=email)

    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email)

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return render_template("register.html", error="An account with that email already exists.", name=name, email=email)

    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password)),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return render_template("login.html", error="All fields are required.", email=email)

    conn = get_db()
    user = conn.execute(
        "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.", email=email)

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/dashboard")
def dashboard():
    return "Dashboard — coming in Step 5"


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_data = get_user_by_id(session["user_id"])
    if not user_data:
        session.clear()
        return redirect(url_for("login"))

    name = user_data["name"]
    initials = "".join(w[0] for w in name.split()[:2]).upper()
    user = {
        "name": name,
        "initials": initials,
        "email": user_data["email"],
        "member_since": user_data["member_since"],
    }

    # ── Date filter ──────────────────────────────────────────────
    today = date.today()
    date_from_raw = request.args.get("from", "").strip()
    date_to_raw   = request.args.get("to", "").strip()
    period        = request.args.get("period", "all")

    date_from = date_to = None
    active_period = "all"
    period_label = "All time"

    if date_from_raw and date_to_raw:
        try:
            d_from = date.fromisoformat(date_from_raw)
            d_to   = date.fromisoformat(date_to_raw)
            if d_from > d_to:
                d_from, d_to = d_to, d_from
            date_from, date_to = d_from.isoformat(), d_to.isoformat()
            active_period = "custom"
            period_label = (
                f"{d_from.strftime('%-d %b %Y')} – {d_to.strftime('%-d %b %Y')}"
            )
        except ValueError:
            pass
    elif period == "this_month":
        date_from = today.replace(day=1).isoformat()
        date_to   = today.isoformat()
        active_period = "this_month"
        period_label  = today.strftime("%B %Y")
    elif period == "last_3_months":
        date_from = (today - timedelta(days=90)).isoformat()
        date_to   = today.isoformat()
        active_period = "last_3_months"
        period_label  = "Last 3 months"
    elif period == "this_year":
        date_from = today.replace(month=1, day=1).isoformat()
        date_to   = today.isoformat()
        active_period = "this_year"
        period_label  = str(today.year)
    # ── END Date filter ──────────────────────────────────────────

    stats        = get_summary_stats(session["user_id"], date_from, date_to)
    transactions = get_recent_transactions(session["user_id"], date_from=date_from, date_to=date_to)
    categories   = get_category_breakdown(session["user_id"], date_from, date_to)

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        active_period=active_period,
        date_from=date_from,
        date_to=date_to,
        period_label=period_label,
    )


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
