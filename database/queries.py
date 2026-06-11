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
    conn = get_db()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count "
        "FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    top = conn.execute(
        "SELECT category, SUM(amount) as cat_total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY cat_total DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    return {
        "total_spent": f"₹{row['total']:,.0f}",
        "transaction_count": row["count"],
        "top_category": top["category"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10):
    # Implemented by Subagent 1
    pass


def get_category_breakdown(user_id):
    # Implemented by Subagent 3
    pass
