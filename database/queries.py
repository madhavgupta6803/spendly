from datetime import datetime

from database.db import get_db


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


def get_summary_stats(user_id):
    # Implemented by Subagent 2
    pass


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT date, description, category, amount FROM expenses "
        "WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [
        {
            "date": datetime.strptime(r["date"], "%Y-%m-%d").strftime("%-d %b %Y"),
            "description": r["description"] or "",
            "category": r["category"],
            "amount": f"₹{r['amount']:,.0f}",
        }
        for r in rows
    ]


def get_category_breakdown(user_id):
    # Implemented by Subagent 3
    pass
