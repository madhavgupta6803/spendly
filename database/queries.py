from datetime import datetime

from database.db import get_db


def _date_clause(date_from, date_to):
    if date_from and date_to:
        return " AND date BETWEEN ? AND ?", (date_from, date_to)
    return "", ()


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    member_since = datetime.strptime(row["created_at"][:10], "%Y-%m-%d").strftime("%B %Y")
    return {"name": row["name"], "email": row["email"], "member_since": member_since}


def get_summary_stats(user_id, date_from=None, date_to=None):
    conn = get_db()
    date_clause, date_params = _date_clause(date_from, date_to)
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count "
        "FROM expenses WHERE user_id = ?" + date_clause,
        (user_id,) + date_params
    ).fetchone()
    top = conn.execute(
        "SELECT category, SUM(amount) as cat_total FROM expenses "
        "WHERE user_id = ?" + date_clause + " GROUP BY category ORDER BY cat_total DESC LIMIT 1",
        (user_id,) + date_params
    ).fetchone()
    conn.close()
    return {
        "total_spent": f"₹{row['total']:,.0f}",
        "transaction_count": row["count"],
        "top_category": top["category"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    conn = get_db()
    date_clause, date_params = _date_clause(date_from, date_to)
    rows = conn.execute(
        "SELECT id, date, description, category, amount FROM expenses "
        "WHERE user_id = ?" + date_clause + " ORDER BY date DESC LIMIT ?",
        (user_id,) + date_params + (limit,)
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "date": datetime.strptime(r["date"], "%Y-%m-%d").strftime("%-d %b %Y"),
            "description": r["description"] or "",
            "category": r["category"],
            "amount": f"₹{r['amount']:,.0f}",
        }
        for r in rows
    ]


def insert_expense(user_id, amount, category, expense_date, description):
    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, expense_date, description or None),
    )
    conn.commit()
    conn.close()


def get_expense_by_id(expense_id, user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT id, amount, category, date, description FROM expenses "
        "WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    ).fetchone()
    conn.close()
    return row


def update_expense(expense_id, user_id, amount, category, expense_date, description):
    conn = get_db()
    conn.execute(
        "UPDATE expenses SET amount=?, category=?, date=?, description=? "
        "WHERE id=? AND user_id=?",
        (amount, category, expense_date, description or None, expense_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id, user_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    )
    conn.commit()
    conn.close()


def get_category_breakdown(user_id, date_from=None, date_to=None):
    conn = get_db()
    date_clause, date_params = _date_clause(date_from, date_to)
    rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM expenses "
        "WHERE user_id = ?" + date_clause + " GROUP BY category ORDER BY total DESC",
        (user_id,) + date_params
    ).fetchall()
    conn.close()
    if not rows:
        return []
    grand = sum(r["total"] for r in rows)
    result = [
        {"name": r["category"], "_amount": r["total"], "pct": round(r["total"] / grand * 100)}
        for r in rows
    ]
    # Largest category absorbs rounding remainder so pct values sum to exactly 100
    diff = 100 - sum(item["pct"] for item in result)
    result[0]["pct"] += diff
    for item in result:
        item["amount"] = f"₹{item['_amount']:,.0f}"
        del item["_amount"]
    return result
